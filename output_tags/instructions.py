"""生成注入系统提示词中的输出标签使用说明。

LLM 需要明确知道每个控制标签的语法。本插件同时兼容两种 mention 格式：
  - <mention id="user_id"/>  —— 明确的 XML 标签
  - [At: user_id]             —— 与聊天历史格式一致（推荐，LLM 会自然使用）

Face 同理，同时兼容 <face id="face_id"/> 与 [Face: face_id] 两种格式，
后者与聊天历史格式一致，是本模块指令中引导 LLM 使用的格式。

表情（Face）的 id → 名称映射不写死在代码中，而是运行时从 `output_tags.face_data`
下载并缓存后传入，详见 `build_interaction_instructions` 的 `faces` 参数。
"""


def _build_face_hint(faces: list[tuple[int, str]], hint_count: int) -> str:
    """构建 `id=名称` 形式的表情提示片段。

    Args:
        faces: 当前可用的 (表情 id, 名称) 列表。
        hint_count: 注入的表情条目数量，<= 0 表示注入完整列表。
    """
    entries = faces if hint_count <= 0 else faces[:hint_count]
    return "、".join(f"{face_id}={name}" for face_id, name in entries)


def build_interaction_instructions(
    mention_enable: bool = True,
    quote_enable: bool = True,
    refuse_enable: bool = True,
    face_enable: bool = True,
    face_hint_count: int = 50,
    faces: list[tuple[int, str]] | None = None,
) -> str:
    """构建输出标签使用说明，用于注入 LLM 系统提示词。

    Args:
        mention_enable: 是否启用 mention 功能。
        quote_enable: 是否启用 <quote/> 功能。
        refuse_enable: 是否启用 <refuse/> 功能。
        face_enable: 是否启用 <face/> 功能。
        face_hint_count: 注入表情 id 提示的数量，<= 0 表示注入完整列表。
        faces: 当前可用的 (表情 id, 名称) 列表，来自运行时下载的缓存。

    Returns:
        可拼接到 system_prompt 末尾的文本块。
    """
    parts: list[str] = []

    # ── Mention 指令 ──
    if mention_enable:
        parts.append(
            "## At/Mention\n"
            "当你需要在回复中 @提及某个用户时，使用 `[At: user_id]` 格式。\n"
            "例如：`[At: 123456]` 你好！\n"
            "一条消息中可以提及多个用户。user_id 可以从聊天历史中找到。\n"
            "不要对自己使用 mention。"
        )

    # ── Quote 指令 ──
    if quote_enable:
        parts.append(
            "## Quote\n"
            "当你想引用/回复某条特定消息时，在回复的最开头放置 `[Quote: msg_id]`。\n"
            "例如：`[Quote: 12345]` 我同意这个观点！\n"
            "msg_id 可以从聊天历史中 # 符号后找到（如 #msg12345）。\n"
            "每条回复最多引用一条消息，且 quote 必须是输出中的第一个内容。\n"
            "只有确实需要引用具体消息时才使用 quote。"
        )

    # ── Face 指令 ──
    if face_enable:
        lines = [
            "## Face（QQ表情）",
            "当你想发送一个 QQ 经典表情来表达情绪时，使用 `[Face: face_id]` 格式。",
            "例如：`[Face: 21]` 好可爱！",
            "一条消息中可以包含多个表情，且可以与文字混排。",
        ]
        hint = _build_face_hint(faces or [], face_hint_count)
        if hint:
            scope_label = "完整列表" if face_hint_count <= 0 else "部分"
            lines.append(f"可用的表情 id 及含义（{scope_label}）：{hint}")
        parts.append("\n".join(lines))

    # ── Refuse 指令 ──
    if refuse_enable:
        parts.append(
            "## Refuse\n"
            "如果你决定不回复当前消息，输出 `[Refuse]` 作为完整回复。\n"
            "必须是纯文本 `[Refuse]`，不能有任何其他内容，前后不能有额外文字。\n"
            "任何其他格式会被视为普通文本正常发送。"
        )

    return "\n\n".join(parts)
