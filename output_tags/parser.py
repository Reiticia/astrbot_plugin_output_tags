"""输出标签解析器 — 将 LLM 输出的控制标签转为平台原生消息组件。

标签说明：
  <mention id="user_id"/>  → At 组件
  [At: user_id]            → At 组件（LLM 从聊天历史中自然习得的格式，兼容处理）
  <quote id="msg_id"/>     → Reply 组件
  <refuse/>                → 取消本次回复
"""

import re
from typing import Optional

from astrbot.api.message_components import At, Plain, Reply

# ── 正则匹配 ──────────────────────────────────────────────

_MENTION_XML_RE = re.compile(
    r"""<mention\s+id\s*=\s*['"]([^'"]+)['"]\s*/?>""",
    re.IGNORECASE,
)
_MENTION_NATIVE_RE = re.compile(r"\[At:\s*(\d+)\]")
_QUOTE_RE = re.compile(
    r"""<quote\s+id\s*=\s*['"]([^'"]+)['"]\s*/?>""",
    re.IGNORECASE,
)
_REFUSE_RE = re.compile(r"<refuse\s*/?>", re.IGNORECASE)


# ── 公开函数 ─────────────────────────────────────────────

def transform_result_chain(
    chain: list,
    *,
    parse_mention: bool = True,
    parse_quote: bool = True,
) -> Optional[list]:
    """将结果链中的 XML 标签转为平台原生组件。

    处理流程：
    1. 先扫描链中是否包含 <quote/>，若有则提取 msg_id 插入链首的 Reply 组件。
    2. 遍历链中的 Plain 文本，将 <mention/> 和 [At:xxx] 替换为 At，将 <quote/> 剔除。

    Args:
        chain: 消息组件列表（由 `event.get_result().chain` 获取）。
        parse_mention: 是否解析 mention 标签（<mention/> + [At:xxx]）。
        parse_quote: 是否解析 <quote/> 标签。

    Returns:
        转换后的新链，若无需转换则返回 None。
    """
    if not chain:
        return None

    # 步骤 1：检测是否有需要处理的标签
    has_any_tag = _chain_has_tags(chain, parse_mention, parse_quote)
    quote_msg_id = _extract_quote_id(chain, parse_quote) if parse_quote else None

    if not has_any_tag and not quote_msg_id:
        return None

    # 步骤 2：构建新链
    new_chain: list = []

    for comp in chain:
        if not isinstance(comp, Plain):
            new_chain.append(comp)
            continue

        text = comp.text

        # 剔除 <quote/> 标签（已转为 Reply 组件放在链首）
        if parse_quote:
            text = _QUOTE_RE.sub("", text)

        # 替换 mention → At（支持两种格式）
        if parse_mention and (_MENTION_XML_RE.search(text) or _MENTION_NATIVE_RE.search(text)):
            new_chain.extend(_split_mentions(text))
        else:
            if text.strip():
                new_chain.append(Plain(text=text))

    # 步骤 3：在链首插入 Reply 组件
    if quote_msg_id:
        new_chain.insert(0, Reply(id=quote_msg_id))

    return new_chain


def clean_response_text_for_history(text: str) -> str:
    """清理回复文本中的标签，用于写入聊天历史。

    <mention/> → [At: user_id]
    [At: xxx]  → [At: user_id]（保持不变，与 AstrBot 历史格式一致）
    <quote/>   → 移除
    """
    text = _MENTION_XML_RE.sub(r"[At: \1]", text)
    text = _QUOTE_RE.sub("", text)
    return text.strip()


def has_refuse_tag(text: str) -> bool:
    """检查文本是否完整匹配 <refuse/>（不含任何额外内容）。"""
    if not text:
        return False
    return bool(_REFUSE_RE.fullmatch(text.strip()))


def chain_has_refuse_tag(chain: list) -> bool:
    """检查结果链是否为单个 <refuse/> 的 Plain 组件。"""
    if len(chain) != 1:
        return False
    comp = chain[0]
    if not isinstance(comp, Plain):
        return False
    return has_refuse_tag(comp.text)


# ── 内部辅助函数 ─────────────────────────────────────────

_NORMALIZE_QUOTE_RE = re.compile(r"^(?:#|msg)+", re.IGNORECASE)


def _normalize_quote_id(raw: str) -> str:
    """去除 msg_id 前缀（# / msg），返回纯数字。"""
    text = str(raw).strip()
    text = _NORMALIZE_QUOTE_RE.sub("", text).strip()
    return text


def _chain_has_tags(
    chain: list,
    parse_mention: bool,
    parse_quote: bool,
) -> bool:
    """检测链中是否存在需要处理的标签。"""
    for comp in chain:
        if not isinstance(comp, Plain):
            continue
        text = comp.text
        if parse_quote and _QUOTE_RE.search(text):
            return True
        if parse_mention and (
            _MENTION_XML_RE.search(text) or _MENTION_NATIVE_RE.search(text)
        ):
            return True
    return False


def _extract_quote_id(chain: list, parse_quote: bool) -> Optional[str]:
    """从链中提取第一个 <quote/> 的 msg_id。"""
    if not parse_quote:
        return None
    for comp in chain:
        if not isinstance(comp, Plain):
            continue
        match = _QUOTE_RE.search(comp.text)
        if match:
            return _normalize_quote_id(match.group(1))
    return None


def _split_mentions(text: str) -> list:
    """将文本按 mention 分割，mention 部分替换为 At 组件。

    同时识别 <mention id="xxx"/> 和 [At:xxx] 两种格式。
    """
    # 统一所有 mention 格式为占位符
    unified = _MENTION_XML_RE.sub(r"[At: \1]", text)

    # 按 [At:xxx] 分割
    parts: list = []
    segments = _MENTION_NATIVE_RE.split(unified)
    for idx, segment in enumerate(segments):
        if idx % 2 == 0:
            # 偶数索引 = 普通文本
            if segment.strip():
                parts.append(Plain(text=segment))
        else:
            # 奇数索引 = user_id
            parts.append(At(qq=segment))
    return parts
