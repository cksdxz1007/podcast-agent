---
name: podcast-transcription
description: 播客音频自动转写 - 收到"播客转写"关键词时自动下载音频、转写、总结并推送结果
triggers:
  - "播客转写"
  - "转写这个播客"
  - "帮我转写"
  - "transcribe podcast"
---

# Podcast Transcription Skill

自动将播客音频转写为文字并进行AI总结。

## 功能

1. **字幕优先** - 自动检测字幕，有字幕时跳过音频下载和转写
2. **自动下载** - 支持 B站、YouTube 及通用链接（含移动端复制的链接格式）
3. **格式转换** - 自动转换不支持的格式
4. **AI转写** - 支持本地 Whisper.cpp 和云端 API（SiliconFlow、OpenAI）
5. **AI总结** - 支持 MiniMax/SiliconFlow/DeepSeek/OpenAI/Qwen/OpenRouter 等多 LLM 提供商
6. **自动推送** - 转写完成后自动发送到 Telegram
7. **后台运行** - 使用 tmux 后台执行，不阻塞 openclaw
8. **长内容分块** - 超长内容自动分块并行处理

## 触发方式

发送包含以下关键词的消息：
- "播客转写"
- "转写这个播客"
- "帮我转写"
- "transcribe podcast"

## 支持的输入

### 视频/音频链接
- B站视频链接（支持 `bilibili.com` 和 `b23.tv` 短链接，自动使用 cookie）
- YouTube 链接
- 移动端复制的链接（自动提取 URL）
  - 格式：`【标题】 https://b23.tv/xxxxx`
- 其他可下载的音频链接

### 示例
```
用户: 播客转写 https://www.bilibili.com/video/BV173wdzgEyw
用户: 播客转写 【视频标题】 https://b23.tv/xxxxx
```

## 支持的格式

### ✅ 直接支持
| 格式 | 扩展名 |
|------|---------|
| WAV | .wav |
| MP3 | .mp3 |
| OGG | .ogg |
| FLAC | .flac |

### ⚠️ 需要转换
| 格式 | 扩展名 |
|------|---------|
| M4A | .m4a |
| AAC | .aac |
| WEBM | .webm |
| MP4 | .mp4 |

## 配置

### 配置文件

配置文件分离管理：
- **`~/.api_keys`** - API 密钥（仅存放密钥）
- **`~/.llm_providers`** - Provider 模型配置和路径

### ~/.api_keys（API 密钥）

```bash
# MiniMax
ANTHROPIC_API_KEY=your-minimax-token-plan-key

# SiliconFlow
SILICONFLOW_API_KEY=your-siliconflow-key

# OpenAI
OPENAI_API_KEY=your-openai-key

# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-key

# Qwen
DASHSCOPE_API_KEY=your-qwen-key

# OpenRouter
OPENROUTER_API_KEY=your-openrouter-key

# 通知
TELEGRAM_CHAT_ID=your-telegram-chat-id
FEISHU_USER_ID=your-feishu-user-id
```

### ~/.llm_providers（Provider 模型和路径配置）

```bash
# =============================================================================
# Provider 选择
# =============================================================================
LLM_PROVIDER=minimax                  # LLM 提供商 (默认 minimax)
TRANSCRIPTION_PROVIDER=siliconflow     # 转写提供商 (默认 whispercpp)

# =============================================================================
# LLM 模型
# =============================================================================
LLM_MODEL=MiniMax-M2.7                # 默认 LLM 模型

# Provider 特定覆盖（可选）
# MINIMAX_LLM_MODEL=MiniMax-M2.7
# SILICONFLOW_LLM_MODEL=deepseek-ai/DeepSeek-V3.2
# DEEPSEEK_LLM_MODEL=deepseek-chat
# OPENAI_LLM_MODEL=gpt-4o
# QWEN_LLM_MODEL=qwen-plus
OPENROUTER_LLM_MODEL=z-ai/glm-4.5-air:free

# =============================================================================
# API Base URL（可选）
# =============================================================================
# 用于自定义 API 代理 / 公司内部部署 / 特殊网络环境
# MINIMAX_BASE_URL=https://custom-api.example.com/anthropic
# SILICONFLOW_BASE_URL=https://custom-siliconflow.example.com/v1

# =============================================================================
# 转写模型
# =============================================================================
TRANSCRIPTION_MODEL=FunAudioLLM/SenseVoiceSmall  # 默认转写模型

# Provider 特定覆盖（可选）
# OPENAI_TRANSCRIPTION_MODEL=whisper-1

# =============================================================================
# Whisper.cpp 本地路径
# =============================================================================
WHISPERCPP_CLI_PATH=~/Desktop/whisper.cpp/build/bin/whisper-cli
WHISPERCPP_MODEL_PATH=~/Desktop/whisper.cpp/models/ggml-medium.bin
```

### 转写提供商

| 提供商 | 类型 | 模型 | 特点 |
|--------|------|------|------|
| whispercpp | 本地 | ggml-medium.bin | 免费、需本地安装 |
| siliconflow | 云端 | FunAudioLLM/SenseVoiceSmall | 快速、精确 |
| openai | 云端 | whisper-1 | 需 OpenAI API Key |

### LLM 提供商

| 提供商 | 默认模型 | 说明 |
|--------|---------|------|
| minimax | MiniMax-M2.7 | Token Plan 专属端点 |
| siliconflow | DeepSeek-V3.2 | 第三方聚合 |
| deepseek | deepseek-chat | 官方 API |
| openai | gpt-4o | OpenAI 兼容格式 |
| qwen | qwen-plus | 阿里云百炼 |
| openrouter | gemini-2.5-flash | 统一 API，支持数百种模型 |

### 配置优先级

| 配置项 | 优先级 |
|--------|--------|
| `~/.llm_providers` 中的 Provider 选择 | 高 |
| `~/.llm_providers` 中的模型/路径 | 高 |
| 代码默认值 | 低（备用） |

### 环境变量（备用）

```bash
# LLM 提供商
export LLM_PROVIDER="minimax"

# 转写提供商
export TRANSCRIPTION_PROVIDER="whispercpp"

# LLM 并发数（默认 2，用于长内容分块并行处理）
export LLM_CONCURRENCY=2

# Whisper.cpp 路径（备用）
export WHISPER_CLI="~/Desktop/whisper.cpp/build/bin/whisper-cli"
export WHISPER_MODEL="~/Desktop/whisper.cpp/models/ggml-medium.bin"
```

## 字幕优先流程

处理优先级：**中文字幕 > 英文字幕 > 无字幕（走转写）**

| 字幕情况 | 处理流程 |
|----------|----------|
| 有中文字幕 | 检测字幕 → 下载字幕 → 解析 SRT → **直接 LLM 整理** |
| 有英文字幕 | 检测字幕 → 下载字幕 → **翻译为中文** → LLM 整理 |
| 无字幕 | 检测失败 → 下载音频 → 转写 → LLM 整理 |

- 字幕下载使用 yt-dlp，自动处理 B站/YouTube 短链接
- B站使用 Firefox cookies，YouTube 使用 Firefox cookies 或配置文件指定
- 英文字幕翻译使用当前 LLM Provider（MiniMax/DeepSeek/SiliconFlow 等）

## 依赖

| 工具 | 说明 |
|------|------|
| tmux | 后台会话管理（必需） |
| ffmpeg | 音频格式转换 |
| Whisper.cpp | 本地转写引擎（可选） |
| yt-dlp | 视频下载 |
| Python 3 | 运行脚本 |

## 文件位置

| 类型 | 位置 |
|------|------|
| 启动脚本 | `~/Desktop/podcast-agent/run_in_tmux.sh` |
| 会话管理 | `~/Desktop/podcast-agent/sessions.sh` |
| 主脚本 | `~/Desktop/podcast-agent/podcast_agent/` |
| 转写输出 | `~/Desktop/podcast-agent/transcriptions/` |
| 文档输出 | `~/Desktop/podcast-agent/documents/` |
| 字幕输出 | `~/Desktop/podcast-agent/subtitles/` |
| 临时文件 | `~/Desktop/podcast-agent/tmp/` |
| Bilibili cookies | Firefox 浏览器（自动读取，无需文件） |

## 后台运行机制

转写任务在 tmux 会话中后台执行，openclaw 不会被阻塞：

```
用户发起请求 → run_in_tmux.sh 创建会话 → 立即返回 → openclaw 继续处理其他指令
                                     ↓
                              tmux 后台执行转写
                                     ↓
                              完成后自动推送结果
```

### 会话管理命令

```bash
# 查看所有转写会话
~/Desktop/podcast-agent/sessions.sh list

# 实时查看进度
~/Desktop/podcast-agent/sessions.sh log <pid>

# 停止会话
~/Desktop/podcast-agent/sessions.sh stop <pid>
```

## 错误处理

| 错误情况 | 反馈 |
|----------|------|
| 字幕下载失败 | 降级：回退到音频下载+转写流程 |
| 下载失败 | "下载失败，请检查链接是否有效" |
| 格式转换失败 | "格式转换失败，请检查音频文件是否损坏" |
| 转写失败 | "转写失败，请检查音频文件是否损坏" |
| API调用失败 | "AI总结失败，请检查 API Key 是否有效" |
| B站/YouTube 下载失败 | "下载失败，请确保 Firefox 已登录对应网站" |

## 注意事项

1. 转写时间：SiliconFlow API 约 2-5 秒，Whisper.cpp 约 4-5 分钟
2. Bilibili 和 YouTube 下载自动从 Firefox 浏览器读取 cookies
   - 确保 Firefox 已登录对应网站即可，无需手动配置 cookies 文件
3. SiliconFlow 转写速度快但无时间戳，Whisper.cpp 有时间戳
4. tmux 会话会在任务完成后自动关闭，日志保留在 `logs/` 目录
5. 有字幕时**优先使用字幕**（中文字幕直接整理，英文字幕翻译后整理），大幅节省时间
6. 长内容自动分块并行处理（`LLM_CONCURRENCY` 控制并发数，默认 2）
