# Podcast Transcription Agent

自动将播客/视频音频转写为文字并进行 AI 总结。

## 功能

1. **自动下载** - 支持 B站、YouTube 及通用链接（含移动端复制格式）
2. **AI 转写** - 本地 Whisper.cpp 或云端 API（SiliconFlow、OpenAI）
3. **AI 总结** - 多 LLM 提供商支持（MiniMax、SiliconFlow、DeepSeek、OpenAI、Qwen）
4. **自动推送** - 结果发送到 Telegram/飞书

## 快速开始

```bash
# 通过 openclaw 触发
"播客转写 https://b23.tv/xxxxx"
"帮我转写这个视频"

# 或直接运行
uv run python -m podcast_agent.main "URL" "播客名称"
```

## 支持的链接格式

```
# 标准格式
https://www.bilibili.com/video/BV1xxx
https://www.youtube.com/watch?v=xxx

# 移动端复制格式（自动提取 URL）
【视频标题】 https://b23.tv/xxxxx
```

## 配置

### ~/.api_keys

```bash
# 转写 + LLM
SILICONFLOW_API_KEY=sk-xxx

# 仅 LLM
ANTHROPIC_API_KEY=xxx      # MiniMax
DEEPSEEK_API_KEY=sk-xxx    # DeepSeek
DASHSCOPE_API_KEY=sk-xxx    # Qwen

# 通知
TELEGRAM_CHAT_ID=xxx
FEISHU_USER_ID=xxx
```

### ~/.llm_providers

```bash
# Provider 选择
LLM_PROVIDER=minimax
TRANSCRIPTION_PROVIDER=siliconflow

# 模型
LLM_MODEL=MiniMax-M2.7
TRANSCRIPTION_MODEL=FunAudioLLM/SenseVoiceSmall

# 本地 Whisper.cpp
WHISPERCPP_CLI_PATH=~/Desktop/whisper.cpp/build/bin/whisper-cli
WHISPERCPP_MODEL_PATH=~/Desktop/whisper.cpp/models/ggml-medium.bin
```

详细配置说明见 [SKILL.md](./skills/podcast-transcription/SKILL.md)

## 转写提供商

| 提供商 | 类型 | 速度 | 特点 |
|--------|------|------|------|
| siliconflow | 云端 | 快 (~2s) | 无时间戳 |
| whispercpp | 本地 | 慢 (~4min) | 有时间戳 |
| openai | 云端 | 快 | 需 API Key |

## LLM 提供商

| 提供商 | 模型 | 说明 |
|--------|------|------|
| minimax | MiniMax-M2.7 | 默认 |
| siliconflow | DeepSeek-V3.2 | 第三方聚合 |
| deepseek | deepseek-chat | 官方 API |
| openai | gpt-4o | OpenAI 兼容 |
| qwen | qwen-plus | 阿里云百炼 |

## 项目结构

```
podcast_agent/
├── main.py              # 主入口
├── config.py            # 配置加载
├── downloader.py         # 视频下载
├── transcriber.py        # 转写（Facade）
├── transcription_providers.py  # 转写 Provider 实现
├── summarizer.py         # AI 总结
├── notifier.py           # 结果推送
├── providers.py          # 统一 Provider 注册表
├── llm_providers.py      # LLM Provider 实现
├── llm_client.py        # LLM 接口
└── models.py            # 数据模型

skills/podcast-transcription/
└── SKILL.md             # 详细配置文档
```

## 依赖

| 工具 | 说明 |
|------|------|
| yt-dlp | 视频下载 |
| ffmpeg | 音频转换 |
| Whisper.cpp | 本地转写（可选） |
| tmux | 后台运行 |

## 输出

- **详细文档**: `documents/doc_YYYYMMDD_HHMMSS.md`
- **转写文本**: `transcriptions/`
- **临时文件**: `tmp/`
