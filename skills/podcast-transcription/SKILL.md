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

1. **自动下载** - 支持 B站、YouTube 及通用链接
2. **格式转换** - 自动转换不支持的格式
3. **Whisper转写** - 使用本地 Whisper.cpp 模型
4. **AI总结** - 支持 MiniMax/SiliconFlow/DeepSeek/Qwen 等多 LLM 提供商
5. **自动推送** - 转写完成后自动发送到 Telegram
6. **后台运行** - 使用 tmux 后台执行，不阻塞 openclaw

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
- 其他可下载的音频链接

### 示例
```
用户: 播客转写 https://www.bilibili.com/video/BV173wdzgEyw
Fairy: ✅ 收到！转写任务已在后台启动，完成后自动推送给你
       PID: 12345
       查看进度: tail -f ~/Desktop/podcast-agent/logs/tmux_podcast_trans_12345.log
       进入会话: tmux attach -t podcast_trans_12345
       停止任务: tmux kill-session -t podcast_trans_12345
[5分钟后]
Fairy: 📝 播客转写完成！

## 📌 主题
...简短总结...

## 📝 主要内容
- ...要点列表...

## 💡 关键观点
- ...观点...

## 🎯 总结
...总结...

📄 详细文档: /Users/cynningli/Desktop/podcast-agent/documents/doc_xxx.md
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

### 环境变量

通过 `~/.openclaw/.env` 或 `~/.api_keys` 配置：

```bash
# LLM 提供商选择 (可选，默认 minimax)
export LLM_PROVIDER="minimax"  # 可选: siliconflow, deepseek, openai, qwen

# 各提供商 API Key (根据 LLM_PROVIDER 选择需要的)
export ANTHROPIC_API_KEY="your-minimax-token-plan-key"  # MiniMax Token Plan
export SILICONFLOW_API_KEY="your-siliconflow-key"       # SiliconFlow
export DEEPSEEK_API_KEY="your-deepseek-key"             # DeepSeek 官方
export DASHSCOPE_API_KEY="your-qwen-key"                # 阿里云百炼

# OpenClaw 配置
export TELEGRAM_CHAT_ID="your-telegram-chat-id"
```

### 依赖

| 工具 | 说明 |
|------|------|
| tmux | 后台会话管理（必需） |
| ffmpeg | 音频格式转换 |
| Whisper.cpp | 转写引擎 | 必选 |
| 模型文件 | `~/Desktop/whisper.cpp/models/ggml-medium.bin` | 必选 |
| Bilibili cookies | `~/Desktop/podcast-agent/bilibili_cookies.txt` | B站下载必需 |
| yt-dlp | 视频下载 |
| Python 3 | 运行脚本 |
| anthropic | MiniMax Token Plan SDK |

## 文件位置

| 类型 | 位置 |
|------|------|
| 启动脚本 | `~/Desktop/podcast-agent/run_in_tmux.sh` |
| 会话管理 | `~/Desktop/podcast-agent/sessions.sh` |
| 主脚本 | `~/Desktop/podcast-agent/podcast_agent/main.py` |
| 转写输出 | `~/Desktop/podcast-agent/transcriptions/` |
| 文档输出 | `~/Desktop/podcast-agent/documents/` |
| 临时文件 | `~/Desktop/podcast-agent/tmp/` |
| 日志文件 | `~/Desktop/podcast-agent/logs/` |
| Bilibili cookies | `~/Desktop/podcast-agent/bilibili_cookies.txt` |

## LLM 提供商

| 提供商 | 模型 | 说明 |
|--------|------|------|
| MiniMax | MiniMax-M2.7 | Token Plan 专属端点 |
| SiliconFlow | DeepSeek-V3.2 | 第三方聚合 |
| DeepSeek | deepseek-chat | 官方 API |
| OpenAI | gpt-4o | OpenAI 兼容格式 |
| Qwen | qwen-plus | 阿里云百炼 |

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

# 或直接用 tmux 命令
tmux attach -t podcast_trans_<pid>   # 进入会话
tmux kill-session -t podcast_trans_<pid>  # 停止会话
```

## 错误处理

| 错误情况 | 反馈 |
|----------|------|
| 下载失败 | "下载失败，请检查链接是否有效" |
| 格式转换失败 | "格式转换失败，请检查音频文件是否损坏" |
| 转写失败 | "转写失败，请检查音频文件是否损坏" |
| API调用失败 | "AI总结失败，请检查 API Key 是否有效" |
| B站 cookies 缺失 | "B站下载需要 cookies 文件，请检查 bilibili_cookies.txt 是否存在" |
| Whisper 模型缺失 | "Whisper 模型未找到，请确认 ~/Desktop/whisper.cpp/models/ggml-medium.bin 存在" |

## 注意事项

1. 转写时间取决于音频长度（16分钟音频约需5分钟）
2. B站下载需要 `bilibili_cookies.txt` 文件
   - 如果文件不存在，系统会提示错误
   - 获取方法：登录 B站 → 开发者工具 → Network → 找到 bilibili.com 请求 → 复制 cookie 字符串保存为此文件
3. 首次使用需要配置对应的 API Key 环境变量
4. tmux 会话会在任务完成后自动关闭，日志保留在 `logs/` 目录
5. 首次使用前确认 Whisper.cpp 和模型文件已安装
