# 输出标签

将 LLM 输出的 XML 控制标签（`<mention/>`、`<quote/>`、`<refuse/>`）转换为平台原生消息组件，让 Bot 拥有精确控制回复行为的能力。

- **插件名**：`astrbot_plugin_output_tags`
- **版本**：`1.0.0`
- **作者**：`Reiticia`
- **适配 AstrBot 版本**：`>= 4.24.2`
- **仓库地址**：`https://github.com/Reiticia/astrbot_plugin_output_tags`

## 功能特性

- **@提及**：LLM 输出 `<mention id="user_id"/>` 自动转为平台 At 组件
- **引用回复**：LLM 输出 `<quote id="msg_id"/>` 自动转为平台 Reply 组件
- **拒绝回复**：LLM 输出 `<refuse/>` 取消本次发送，Bot 保持沉默
- **独立控制**：三个标签各自可独立开关

## 安装

```bash
# 在 AstrBot 插件目录下
git clone https://github.com/Reiticia/astrbot_plugin_output_tags.git
```

无需额外依赖，仅依赖 AstrBot 核心框架。

## 配置项

| 配置键 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `mention_enable` | `bool` | `true` | 启用 `<mention/>` 标签解析 |
| `quote_enable` | `bool` | `true` | 启用 `<quote/>` 标签解析 |
| `refuse_enable` | `bool` | `true` | 启用 `<refuse/>` 标签解析 |

## 指令列表

> 本插件不注册任何用户指令。

| 指令 | 参数 | 权限 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| 无 | — | — | — | — |

## 函数调用 / 对外接口

> 本插件不提供对外接口。

## 附加功能

- **事件监听**：
  - `on_llm_request`：在 LLM 请求中注入标签使用说明，告知模型如何输出控制标签。
  - `on_decorating_result`：在响应发送前解析标签，将 XML 标签转为平台原生组件。
  - `on_llm_response`：清理回复文本中的标签，防止标签原文被存入聊天历史。

## 依赖

- `astrbot`（核心框架）

## 更新日志

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| `1.0.0` | `2026-07-04` | 初始版本 |

## 协议

`MIT`
