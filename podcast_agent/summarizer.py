"""Summarizer module - generates AI summaries using configurable LLM providers."""

import logging
import re
from pathlib import Path
from datetime import datetime

from .config import Config
from .models import Transcript, TextSource, Summary
from .llm_providers import create_llm_client, LLMClient

logger = logging.getLogger(__name__)

# Rough estimate: ~4 chars per token, use 3000 chars (~750 tokens) per chunk
DEFAULT_CHUNK_SIZE = 3000


def _chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[str]:
    """Split text into chunks of approximately chunk_size chars.

    Splits on newline boundaries to keep logical units intact.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    lines = text.split("\n")
    current = []

    for line in lines:
        current.append(line)
        if sum(len(l) for l in current) + len(current) > chunk_size:
            if len(current) > 1:
                chunks.append("\n".join(current[:-1]))
                current = [current[-1]]
            else:
                chunks.append("\n".join(current))
                current = []

    if current:
        chunks.append("\n".join(current))

    return chunks


class SummarizationError(Exception):
    """Raised when summarization fails."""
    pass


class Summarizer:
    """Generates summaries using a pluggable LLM client.

    The LLM provider can be configured via environment variables:
    - LLM_PROVIDER: "siliconflow", "deepseek", "openai", "qwen"
    - SILICONFLOW_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY / DASHSCOPE_API_KEY
    """

    DOCUMENT_PROMPT = """你是一个播客内容整理专家。请根据**仅有**的转写内容生成 Markdown 文档。

**重要约束：**
1. **只使用转写内容中的信息**，不要编造、推测、补充任何转写中没有的内容
2. 如果转写内容本身不完整或模糊，在文档中如实说明，不要强行填补
3. 将对话转为文章段落形式，不是对话格式
4. 按话题分段，每段以时间戳开头
5. 提取 3-5 个关键引用（必须是转写中真实出现的内容）

**输出格式：**
```markdown
# [播客主题]

> 时长：[根据转写时长推断]
> 主题：[一句话概括转写内容的核心]

## [章节标题1] (00:xx)
[基于转写内容整理的段落...]

## [章节标题2] (00:xx)
[继续整理...]

## 关键引用
> "[转写中真实出现的引用]"

## 总结
[简要总结，但只基于转写内容]
```

请直接输出 Markdown，不要任何解释。"""

    BRIEF_PROMPT = """你是一个播客总结专家。请根据**仅有**的转写内容生成简短总结。

**重要约束：**
1. **只基于转写内容**，不编造任何信息
2. 如果内容不足以生成某个部分，如实说明而非编造
3. 不超过 500 字
4. 用 bullet points 列出要点

**格式：**
## 📌 主题
[一句话，基于转写内容]

## 📝 主要内容
- [要点1，必须来自转写内容]
- [要点2]

## 💡 关键观点
- [观点1]
- [观点2]

## 🎯 总结
[简短总结，只基于转写内容]

请直接输出，不要任何解释。"""

    def __init__(self, config: Config, llm_client: LLMClient = None):
        self.config = config
        self._llm_client = llm_client

    @property
    def llm_client(self) -> LLMClient:
        """Lazy-load LLM client."""
        if self._llm_client is None:
            self._llm_client = create_llm_client()
            logger.info(f"Using LLM provider: {self._llm_client.name}")
        return self._llm_client

    def _call_llm(self, prompt: str, text: str) -> str:
        """Call LLM to generate content.

        Args:
            prompt: System prompt
            text: Input text

        Returns:
            Generated content
        """
        response = self.llm_client.chat(prompt, text)
        return response.content

    def generate_document(
        self, text_source: Transcript | TextSource, name: str = None
    ) -> Path:
        """Generate detailed Markdown document from transcript or subtitle text.

        Args:
            text_source: The transcript or TextSource object
            name: Optional name for the podcast (used in output filename)

        Returns:
            Path to the generated document
        """
        logger.info("Generating detailed document...")

        full_text = text_source.get_full_text()
        chunks = _chunk_text(full_text, DEFAULT_CHUNK_SIZE)
        logger.info(f"Split into {len(chunks)} chunks for document generation")

        try:
            if len(chunks) == 1:
                markdown_content = self._call_llm(
                    self.DOCUMENT_PROMPT,
                    f"请根据以下转写内容生成详细文档：\n\n{chunks[0]}"
                )
            else:
                # Generate partial documents from each chunk
                partial_docs = []
                for i, chunk in enumerate(chunks):
                    logger.info(f"Processing chunk {i + 1}/{len(chunks)}...")
                    partial = self._call_llm(
                        self.DOCUMENT_PROMPT,
                        f"请根据以下转写内容（第 {i + 1}/{len(chunks)} 部分）生成详细文档：\n\n{chunk}"
                    )
                    partial_docs.append(partial)

                # Synthesize final document from all partials
                logger.info("Synthesizing final document from chunks...")
                markdown_content = self._call_llm(
                    "你是一个播客内容整理专家。请将多份文档片段合成为一份完整、连贯的 Markdown 文档。"
                    "要求：合并重复内容，保持结构清晰，不要添加转写中没有的信息。",
                    "\n\n---\n\n".join(f"文档片段 {i + 1}:\n{doc}" for i, doc in enumerate(partial_docs))
                )
        except Exception as e:
            raise SummarizationError(f"Failed to generate document: {e}")

        # Clean markdown content
        markdown_content = self._clean_markdown(markdown_content)

        # Save document - use name if provided, otherwise fallback to doc_{timestamp}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if name:
            doc_file = self.config.document_dir / f"{name}_{timestamp}.md"
        else:
            doc_file = self.config.document_dir / f"doc_{timestamp}.md"

        with open(doc_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Document saved to {doc_file}")
        return doc_file

    def generate_brief(self, text_source: Transcript | TextSource) -> Summary:
        """Generate brief summary from transcript or subtitle text.

        Args:
            text_source: The transcript or TextSource object

        Returns:
            Summary object with brief content
        """
        logger.info("Generating brief summary...")

        full_text = text_source.get_full_text()
        chunks = _chunk_text(full_text, DEFAULT_CHUNK_SIZE)
        logger.info(f"Split into {len(chunks)} chunks for brief generation")

        try:
            if len(chunks) == 1:
                content = self._call_llm(
                    self.BRIEF_PROMPT,
                    f"请总结以下播客内容：\n\n{chunks[0]}"
                )
            else:
                # Extract key points from each chunk
                point_parts = []
                for i, chunk in enumerate(chunks):
                    logger.info(f"Extracting key points from chunk {i + 1}/{len(chunks)}...")
                    points = self._call_llm(
                        "你是一个播客总结专家。请从以下转写内容中提取关键要点（3-5条），"
                        "每条用一句话概括。只基于内容本身，不要编造。",
                        f"转写内容（第 {i + 1}/{len(chunks)} 部分）：\n\n{chunk}"
                    )
                    point_parts.append(points)

                # Generate final brief from all key points
                logger.info("Generating final brief from key points...")
                content = self._call_llm(
                    self.BRIEF_PROMPT,
                    f"以下是播客各部分的要点总结，请整合成一份连贯的简短总结：\n\n"
                    + "\n\n---\n\n".join(f"第 {i + 1} 部分要点:\n{pts}" for i, pts in enumerate(point_parts))
                )
        except Exception as e:
            raise SummarizationError(f"Failed to generate brief: {e}")

        # Extract topic from first heading
        topic = ""
        match = re.search(r"#+\s*📌\s*主题\s*\n(.+)", content)
        if match:
            topic = match.group(1).strip()

        logger.info("Brief summary generated")
        return Summary(content=content, topic=topic)

    def _clean_markdown(self, content: str) -> str:
        """Clean markdown content by removing code block markers."""
        content = content.strip()
        if content.startswith("```markdown"):
            content = content[10:]
        elif content.startswith("```md"):
            content = content[5:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
