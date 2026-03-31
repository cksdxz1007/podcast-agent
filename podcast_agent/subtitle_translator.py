"""Subtitle translator module - parses SRT and translates via LLM."""

import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Rough estimate: ~4 chars per token, use 3000 chars (~750 tokens) per chunk
CHUNK_SIZE = 3000


def parse_srt_text(srt_path) -> str:
    """Extract plain text from SRT file, removing timestamps and sequence numbers.

    Args:
        srt_path: Path to SRT file

    Returns:
        Clean text with subtitle lines joined by newlines
    """
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove sequence numbers (lines that are only digits)
    content = re.sub(r"^\d+$", "", content, flags=re.MULTILINE)
    # Remove timestamp lines (HH:MM:SS,mmm --> HH:MM:SS,mmm)
    content = re.sub(
        r"\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}",
        "",
        content,
    )
    # Remove blank lines and strip
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    return "\n".join(lines)


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks of approximately chunk_size chars.

    Splits on newline boundaries to keep subtitle lines intact.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    lines = text.split("\n")
    current = []

    for line in lines:
        current.append(line)
        if sum(len(l) for l in current) + len(current) > chunk_size:
            # Push current chunk (except last line which overflowed)
            if len(current) > 1:
                chunks.append("\n".join(current[:-1]))
                current = [current[-1]]
            else:
                # Single line too long, force it
                chunks.append("\n".join(current))
                current = []

    if current:
        chunks.append("\n".join(current))

    return chunks


def translate_srt_to_chinese(srt_path, llm_client, chunk_size: int = CHUNK_SIZE, concurrency: int = 2) -> str:
    """Translate English SRT subtitles to Chinese text via LLM.

    Translates in chunks to avoid token limits, then concatenates results.
    Uses ThreadPoolExecutor for parallel processing of chunks.

    Args:
        srt_path: Path to SRT file
        llm_client: LLMClient instance (from llm_providers)
        chunk_size: Max chars per chunk (default 3000)
        concurrency: Number of parallel LLM calls (default 2)

    Returns:
        Chinese translated text
    """
    logger.info(f"Translating subtitles to Chinese: {srt_path}")

    english_text = parse_srt_text(srt_path)
    logger.info(f"Extracted {len(english_text)} chars from SRT")

    chunks = _chunk_text(english_text, chunk_size)
    logger.info(f"Split into {len(chunks)} chunks for translation (concurrency={concurrency})")

    system_prompt = """你是一个专业的翻译员。请将以下英文字幕内容翻译成中文（简体中文）。

要求：
1. 保持原文的语义和语气
2. 按段落翻译，不要在翻译内容中添加任何编号、时间戳或格式化标记
3. 只输出翻译后的中文文本，不要有任何解释
4. 专有名词保持原文或使用通用的中文译名"""

    def translate_one(args):
        idx, chunk = args
        logger.info(f"Translating chunk {idx + 1}/{len(chunks)} ({len(chunk)} chars)...")
        response = llm_client.chat(
            system_prompt,
            f"请将以下英文字幕翻译成中文：\n\n{chunk}"
        )
        return idx, response.content.strip()

    # Use index to preserve order after parallel execution
    results: list[str] = ["" for _ in chunks]
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(translate_one, (i, c)): i for i, c in enumerate(chunks)}
        for future in as_completed(futures):
            idx, translated = future.result()
            results[idx] = translated

    result = "\n".join(results)
    logger.info(f"Subtitle translation complete: {len(result)} chars")
    return result
