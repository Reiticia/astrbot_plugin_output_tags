"""生成注入系统提示词中的输出标签使用说明。

LLM 需要明确知道每个标签的语法和用法，这里根据配置开关生成对应指令。
"""


def build_interaction_instructions(
    mention_enable: bool = True,
    quote_enable: bool = True,
    refuse_enable: bool = True,
) -> str:
    """构建输出标签使用说明，用于注入 LLM 系统提示词。

    Args:
        mention_enable: 是否启用 <mention/> 功能。
        quote_enable: 是否启用 <quote/> 功能。
        refuse_enable: 是否启用 <refuse/> 功能。

    Returns:
        可拼接到 system_prompt 末尾的文本块。
    """
    parts: list[str] = []

    # ── Mention 指令 ──
    if mention_enable:
        parts.append(
            "## Mention\n"
            "当你需要在回复中 @提及某个用户时，使用控制标签：<mention id=\"user_id\"/>。\n"
            "例如：<mention id=\"123456\"/> 你好！\n"
            "一条消息中可以提及多个用户。user_id 可以从聊天历史中找到。\n"
            "不要对自己使用 mention 标签。\n"
            "重要：mention 标签不是容器标签，不要输出 </mention>。"
        )

    # ── Quote 指令 ──
    if quote_enable:
        parts.append(
            "## Quote\n"
            "当你想引用/回复某条特定消息时，在回复的最开头放置 <quote id=\"msg_id\"/>。\n"
            "例如：<quote id=\"12345\"/> 我同意这个观点！\n"
            "msg_id 可以从聊天历史中 # 符号后找到（如 #msg12345）。\n"
            "每条回复最多引用一条消息，且 quote 标签必须是输出中的第一个内容。\n"
            "只有确实需要引用具体消息时才使用 quote。\n"
            "重要：quote 标签不是容器标签，不要输出 </quote>。"
        )

    # ── Refuse 指令 ──
    if refuse_enable:
        parts.append(
            "## Refuse\n"
            "如果你决定不回复当前消息，输出 `<refuse/>` 作为完整回复。\n"
            "必须是纯文本 `<refuse/>`，不能有任何其他内容，前后不能有额外文字。\n"
            "任何其他格式会被视为普通文本正常发送。"
        )

    return "\n\n".join(parts)
