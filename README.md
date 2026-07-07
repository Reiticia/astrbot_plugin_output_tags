# 输出标签

将 LLM 输出的 XML 控制标签（`<mention/>`、`<quote/>`、`<face/>`、`<refuse/>`）转换为平台原生消息组件，让 Bot 拥有精确控制回复行为的能力。

- **插件名**：`astrbot_plugin_output_tags`
- **版本**：`1.1.2`
- **作者**：`Reiticia`
- **适配 AstrBot 版本**：`>= 4.24.2`
- **仓库地址**：`https://github.com/Reiticia/astrbot_plugin_output_tags`

## 功能特性

- **@提及**：LLM 输出 `<mention id="user_id"/>` 自动转为平台 At 组件
- **引用回复**：LLM 输出 `<quote id="msg_id"/>` 自动转为平台 Reply 组件
- **QQ 表情**：LLM 输出 `[Face: face_id]`（或 `<face id="face_id"/>`）自动转为平台 Face 组件（QQ 经典表情）。表情 id → 名称映射不写死在代码中，插件加载时（AstrBot 整体启动，或仅热重载/更新本插件）会自动从 [koishi.js.org/QFace](https://koishi.js.org/QFace) 下载最新数据并缓存到插件数据目录（覆盖旧缓存），无需重启整个 AstrBot 进程
- **拒绝回复**：LLM 输出 `<refuse/>` 取消本次发送，Bot 保持沉默
- **独立控制**：四个标签各自可独立开关

## 安装

```bash
# 在 AstrBot 插件目录下
git clone https://github.com/Reiticia/astrbot_plugin_output_tags.git
```

除 AstrBot 核心框架外依赖 `httpx`（用于下载 QQ 表情数据），插件启动时需要能访问 `koishi.js.org`。

## 配置项

| 配置键 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `mention_enable` | `bool` | `true` | 启用 `<mention/>` 标签解析 |
| `quote_enable` | `bool` | `true` | 启用 `<quote/>` 标签解析 |
| `refuse_enable` | `bool` | `true` | 启用 `<refuse/>` 标签解析 |
| `face_enable` | `bool` | `true` | 启用 `[Face: xxx]` / `<face id="xxx"/>` 标签解析 |
| `face_hint_count` | `int` | `50` | 注入系统提示词的表情 id 提示数量，0 或负数表示注入本次下载到的完整列表 |

## 指令列表

> 本插件不注册任何用户指令。

| 指令 | 参数 | 权限 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| 无 | — | — | — | — |

## 函数调用 / 对外接口

> 本插件不提供对外接口。

## 附加功能

- **事件监听**：
  - 插件加载（`__init__`，覆盖 AstrBot 整体启动与仅热重载/更新本插件两种场景）：异步从远程下载最新的 QQ 表情 id → 名称映射并覆盖插件数据目录中的本地缓存；下载失败时沿用已有缓存，不影响插件其余功能。
  - `on_llm_request`：在 LLM 请求中注入标签使用说明，告知模型如何输出控制标签。
  - `on_decorating_result`：在响应发送前解析标签，将 XML 标签转为平台原生组件。
  - `on_llm_response`：清理回复文本中的标签，防止标签原文被存入聊天历史。
- **数据缓存**：`data/plugin_data/astrbot_plugin_output_tags/qq_faces.json`（由 `StarTools.get_data_dir()` 管理，插件卸载并选择删除数据时会一并清理）。

## 依赖

- `astrbot`（核心框架）
- `httpx`（下载 QQ 表情数据）

## 更新日志

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| `1.1.2` | `2026-07-07` | 新增 `[Face: xxx]` 原生格式解析，修复 LLM 从聊天历史学到该格式后原文透传给用户的问题 |
| `1.1.1` | `2026-07-07` | 表情数据刷新改为在插件 `__init__` 时触发，覆盖热重载/更新场景，不再依赖仅在 AstrBot 整体启动时触发一次的 `on_astrbot_loaded` |
| `1.1.0` | `2026-07-07` | 新增 `<face id="xxx"/>` QQ 经典表情标签 |
| `1.0.0` | `2026-07-04` | 初始版本 |

## 协议

`MIT`
