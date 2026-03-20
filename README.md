# Podcast Transcription Agent

## 功能
当收到包含"播客转写"关键词的消息时，自动进行：
1. 下载播客音频
2. Whisper.cpp 转写
3. AI 总结
4. 发送结果

## 触发方式
- 关键词：**播客转写** + 链接

## 使用方法
```bash
# 方式1: 通过脚本
~/Desktop/podcast-agent/podcast-agent.sh "Apple Podcasts链接"

# 方式2: 告诉Fairy
"帮我转写这个播客: [链接]"
```

## 文件位置
- 脚本: ~/Desktop/podcast-agent/podcast-agent.sh
- 转写输出: ~/Desktop/podcast-agent/transcriptions/
- 音频缓存: ~/Desktop/podcast-agent/output/

## 依赖
- yt-dlp (已安装)
- whisper.cpp (medium模型)
- DeepSeek API (已配置)
- curl, jq

## 配置
- 模型: ggml-medium.bin
- 语言: 中文 (zh)
- 总结: DeepSeek Chat
