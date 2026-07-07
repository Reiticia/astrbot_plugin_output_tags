"""QQ 经典表情（QFace）数据管理。

不在代码中硬编码表情 id → 名称映射，而是在插件加载时（含 AstrBot 整体启动、以及仅
热重载/更新本插件的场景）从远程拉取一次最新数据，写入插件数据目录（覆盖旧缓存）。
之后插件运行期间直接使用内存中的缓存结果，触发时机见 `main.Main.__init__`。

数据来源：https://koishi.js.org/QFace
"""

import json
from pathlib import Path

import httpx

from astrbot.api import logger

QFACE_SOURCE_URL = "https://koishi.js.org/QFace/assets/qq_emoji/_index.json"
CACHE_FILE_NAME = "qq_faces.json"


async def refresh_face_cache(data_dir: Path) -> list[tuple[int, str]]:
    """从远程拉取最新的表情 id → 名称映射，写入插件数据目录（覆盖旧数据）。

    拉取失败时保留并返回本地已有缓存，不影响插件其余标签功能。

    Args:
        data_dir: 插件数据目录（由 `StarTools.get_data_dir()` 获取）。

    Returns:
        (表情 id, 名称) 列表，拉取失败且无本地缓存时为空列表。
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(QFACE_SOURCE_URL)
            resp.raise_for_status()
            raw = resp.json()
    except Exception as e:
        logger.warning(f"output-tags | 拉取 QFace 表情数据失败，沿用本地缓存（若有）| {e!r}")
        return load_face_cache(data_dir)

    faces = _parse_faces(raw)

    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        cache_path = data_dir / CACHE_FILE_NAME
        cache_path.write_text(json.dumps(faces, ensure_ascii=False), encoding="utf-8")
        logger.info(f"output-tags | 已更新 QFace 表情数据缓存，共 {len(faces)} 条 | {cache_path}")
    except OSError as e:
        logger.warning(f"output-tags | 写入 QFace 表情数据缓存失败，本次仅在内存中生效 | {e!r}")

    return [(face_id, name) for face_id, name in faces]


def load_face_cache(data_dir: Path) -> list[tuple[int, str]]:
    """读取本地已缓存的表情映射表，不存在或损坏时返回空列表。"""
    cache_path = data_dir / CACHE_FILE_NAME
    if not cache_path.exists():
        return []
    try:
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
        return [(int(face_id), str(name)) for face_id, name in raw]
    except Exception as e:
        logger.warning(f"output-tags | 读取本地 QFace 表情缓存失败 | {e!r}")
        return []


def _parse_faces(raw: object) -> list[list]:
    """将远程 JSON 中带有效中文描述的条目转为 [id, 名称] 列表，按原始顺序保留。"""
    if not isinstance(raw, list):
        return []

    faces: list[list] = []
    seen_ids: set[int] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue

        describe = str(item.get("describe") or "").strip()
        if describe.startswith("/"):
            describe = describe[1:]
        if not describe:
            continue

        try:
            face_id = int(item.get("emojiId"))
        except (TypeError, ValueError):
            continue

        if face_id in seen_ids:
            continue
        seen_ids.add(face_id)
        faces.append([face_id, describe])

    return faces
