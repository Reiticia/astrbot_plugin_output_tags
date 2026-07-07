"""输出标签插件 — 入口。

将 LLM 输出的 XML 控制标签转为平台原生消息行为：
  - <mention id="xxx"/>  →  At 组件
  - <quote id="xxx"/>     →  Reply 组件
  - <face id="xxx"/>      →  Face 组件
  - <refuse/>             →  取消发送
"""

import asyncio

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import LLMResponse
from astrbot.api.star import Context, Star, StarTools

from .output_tags.face_data import load_face_cache, refresh_face_cache
from .output_tags.instructions import build_interaction_instructions
from .output_tags.parser import (
    chain_has_refuse_tag,
    clean_response_text_for_history,
    has_refuse_tag,
    transform_result_chain,
)

PLUGIN_NAME = "astrbot_plugin_output_tags"


class Main(Star):
    def __init__(self, context: Context, config: dict | None = None) -> None:
        super().__init__(context)
        self._config = config or {}
        self._data_dir = StarTools.get_data_dir(PLUGIN_NAME)
        self._faces: list[tuple[int, str]] = load_face_cache(self._data_dir)
        # 在 __init__ 中触发刷新：无论是 AstrBot 整体启动还是仅热重载/更新本插件，
        # 都会重新实例化 Star 子类、走到这里，因此不依赖 on_astrbot_loaded（只在整体启动时触发一次）。
        self._face_refresh_task = self._schedule_face_refresh()
        logger.info("output-tags | 插件已加载")

    def _schedule_face_refresh(self) -> asyncio.Task | None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("output-tags | 当前不在事件循环中，跳过表情数据自动刷新")
            return None
        return loop.create_task(self._refresh_face_cache())

    async def _refresh_face_cache(self) -> None:
        self._faces = await refresh_face_cache(self._data_dir)

    # ── 配置读取 ──────────────────────────────────────────

    def _cfg_mention(self) -> bool:
        return bool(self._config.get("mention_enable", True))

    def _cfg_quote(self) -> bool:
        return bool(self._config.get("quote_enable", True))

    def _cfg_refuse(self) -> bool:
        return bool(self._config.get("refuse_enable", True))

    def _cfg_face(self) -> bool:
        return bool(self._config.get("face_enable", True))

    def _cfg_face_hint_count(self) -> int:
        return int(self._config.get("face_hint_count", 50))

    # ── 生命周期钩子 ──────────────────────────────────────

    @filter.on_llm_request()
    async def inject_tag_instructions(self, event: AstrMessageEvent, req) -> None:
        """在 LLM 请求中注入标签使用说明。"""
        instructions = build_interaction_instructions(
            mention_enable=self._cfg_mention(),
            quote_enable=self._cfg_quote(),
            refuse_enable=self._cfg_refuse(),
            face_enable=self._cfg_face(),
            face_hint_count=self._cfg_face_hint_count(),
            faces=self._faces,
        )
        if not instructions:
            return

        req.system_prompt += "\n\n" + instructions

    @filter.on_decorating_result()
    async def parse_tags(self, event: AstrMessageEvent) -> None:
        """解析 LLM 输出中的控制标签并转换为平台原生组件。"""
        result = event.get_result()
        if not result or not result.chain:
            return

        # 处理 <refuse/>：清空结果链，阻止发送
        if self._cfg_refuse() and chain_has_refuse_tag(result.chain):
            logger.info(
                "output-tags | 检测到 <refuse/>，已取消发送 | origin=%s",
                event.unified_msg_origin,
            )
            result.chain = []
            return

        # 转换 <mention/> → At, <quote/> → Reply
        transformed = transform_result_chain(
            result.chain,
            parse_mention=self._cfg_mention(),
            parse_quote=self._cfg_quote(),
            parse_face=self._cfg_face(),
        )
        if transformed is not None:
            result.chain = transformed

    @filter.on_llm_response()
    async def clean_history_text(
        self, event: AstrMessageEvent, resp: LLMResponse
    ) -> None:
        """将回复文本中的标签清理后写入聊天历史。

        注意：此钩子依赖上游（如 AstrBot 内置或群聊上下文插件）管理历史存储，
        本插件仅负责将 resp.completion_text 中的标签替换为纯文本形式。
        """
        if not resp.completion_text:
            return

        if self._cfg_refuse() and has_refuse_tag(resp.completion_text):
            return

        cleaned = clean_response_text_for_history(resp.completion_text)
        if cleaned and cleaned != resp.completion_text:
            resp.completion_text = cleaned
