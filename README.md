# OwnerRobert

一个基于 FastAPI 的语音/文本助手应用，内置会话持久化、历史全文搜索与可选联网检索。前端为简洁的网页 UI，后端调用 OpenAI 模型生成回复，支持中文语音合成与浏览器语音识别（受浏览器支持限制）。

## 功能特性
- **聊天与上下文记忆**：会话保存在本地 SQLite，连续对话有上下文。
- **可选联网检索**：勾选“联网搜索”时，优先使用 Tavily（需 `TAVILY_API_KEY`），失败/未配置时回退 DuckDuckGo 摘要。
- **历史搜索**：基于 SQLite FTS5 的全文搜索接口。
- **语音支持**：
  - 文字转语音：浏览器 `SpeechSynthesis` 合成中文播报。
  - 语音转文字：Chrome 的 `webkitSpeechRecognition`（若支持）。
- **前后端一体**：静态页面通过 FastAPI 直接挂载在根路径。

## 目录结构
```
app/
  main.py                # FastAPI 入口与路由
  db.py                  # SQLite/FTS5 持久化
  services/
    llm.py              # OpenAI Chat API 调用
    search.py           # Tavily / DuckDuckGo 搜索
static/
  index.html            # 简洁网页 UI（中文）
  app.js                # 前端逻辑（聊天、语音、历史搜索）
  styles.css            # 样式
requirements.txt         # 依赖清单
```

## 环境要求
- Python 3.10+
- 可联网（如需联网检索）
- 浏览器：Chrome/Safari（语音功能取决于浏览器支持）

## 安装与运行
1) 克隆并进入项目目录：
```bash
cd OwnerRobert
```

2) 创建虚拟环境并安装依赖：
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

3) 配置环境变量（至少需要 OpenAI 密钥）：
```bash
export OPENAI_API_KEY="你的OpenAI密钥"
# 可选：
export MODEL="gpt-4o-mini"         # 默认即为 gpt-4o-mini
export PERSONA="calm, helpful"     # 默认人设风格
export SYSTEM_PROMPT="You are a helpful voice assistant. Be concise and friendly."
export TAVILY_API_KEY="你的Tavily密钥"  # 启用高质量联网检索
```

4) 启动服务：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5) 打开浏览器访问：
```
http://localhost:8000/
```

## 使用说明（前端）
- 在输入框键入消息，点击“发送”。
- 可填写 `persona`（如：`calm, helpful`）影响风格。
- 勾选“联网搜索”开启检索增强。
- 点击麦克风图标尝试语音输入（取决于浏览器）。
- 下方“搜索历史”支持全文关键字检索以往消息记录。

## 数据存储
- 数据文件位于 `data/app.db`（启动后自动创建）。
- 表结构：`conversations`、`messages`、`messages_fts`（FTS5 虚拟表），并带触发器保持 FTS 同步。

## API 文档
### 1) 聊天接口
- 路径：`POST /api/chat`
- 请求体：
```json
{
  "message": "你好",
  "persona": "calm, helpful",   // 可选
  "conversation_id": "uuid",    // 可选，不传则新建
  "enable_search": true          // 可选，默认 false
}
```
- 响应体：
```json
{
  "conversation_id": "uuid",
  "reply": "你好！很高兴帮你。"
}
```

示例：
```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"你好","enable_search":false}'
```

### 2) 历史搜索
- 路径：`GET /api/history/search?q=关键词&limit=10`
- 响应：
```json
{ "results": [ { "id": 1, "conversation_id": "...", "role": "user", "content": "...", "created_at": "..." } ] }
```

## 可配置项（环境变量）
- `OPENAI_API_KEY`：必填，用于调用 OpenAI。
- `MODEL`：可选，默认 `gpt-4o-mini`。
- `PERSONA`：可选，默认 `calm, helpful`。
- `SYSTEM_PROMPT`：可选，系统提示词前缀。
- `TAVILY_API_KEY`：可选，提供更稳定与结构化的联网检索。

## 常见问题
- 浏览器无语音识别：部分浏览器不支持 `webkitSpeechRecognition`，可手动输入。
- 429/鉴权错误：检查 `OPENAI_API_KEY` 是否配置正确及调用配额。
- 联网检索失败：未设置 `TAVILY_API_KEY` 时自动回退 DuckDuckGo；网络问题可稍后重试。
- 数据位置：删除 `data/app.db` 会清空历史记录。

## 部署建议
- 生产环境建议使用：`uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`
- 置于反向代理（如 Nginx）后以启用 HTTPS。
- 将环境变量通过系统服务或容器安全注入；不要硬编码。

## 许可
本项目遵循 `LICENSE` 文件所述许可。
