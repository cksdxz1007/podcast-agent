#!/usr/bin/env python3
"""Main orchestration module for podcast transcription workflow."""

import logging
import sys
import argparse
from pathlib import Path

from .config import Config
from .downloader import Downloader, DownloadError
from .transcriber import Transcriber, TranscriptionError
from .summarizer import Summarizer, SummarizationError
from .notifier import Notifier, NotificationError
from .models import TextSource, Summary
from .subtitle_checker import check_subtitles
from .subtitle_downloader import download_subtitle
from .subtitle_translator import translate_srt_to_chinese, parse_srt_text
from .llm_providers import create_llm_client

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stderr)]
    )


def main(url: str, name: str = "podcast") -> int:
    """Main entry point for the podcast transcription workflow.

    Args:
        url: Source URL to download and transcribe
        name: Optional name for the podcast

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("========== Starting podcast transcription ==========")
    logger.info(f"URL: {url}")
    logger.info(f"Name: {name}")

    try:
        config = Config.load()
        config.ensure_directories()

        # Select cookie file based on platform
        if "bilibili.com" in url or "b23.tv" in url:
            subtitle_cookie_file = config.cookie_file
        else:
            subtitle_cookie_file = config.youtube_cookie_file

        # Step 0: Check for subtitles before downloading
        logger.info("Step 0/5: Checking available subtitles...")
        subtitle_info = check_subtitles(url, cookie_file=subtitle_cookie_file)

        if subtitle_info is not None:
            try:
                if subtitle_info.language_code.startswith("zh"):  # Chinese
                    # Chinese subtitles available - skip download & transcription
                    logger.info(
                        f"Found Chinese {subtitle_info.subtitle_type} subtitles "
                        f"({subtitle_info.language_code}), skipping audio download & transcription"
                    )
                    srt_path = download_subtitle(
                        url=url,
                        language=subtitle_info.language_code,
                        subtitle_type=subtitle_info.subtitle_type,
                        output_dir=config.subtitle_dir,
                        name=name,
                        cookie_file=subtitle_cookie_file,
                    )

                    chinese_text = parse_srt_text(srt_path)
                    text_source = TextSource(
                        source_type="subtitle_zh",
                        full_text=chinese_text,
                        source_path=srt_path,
                    )
                elif subtitle_info.language_code.lower() == "en":
                    # English subtitles - download & translate
                    logger.info(
                        f"Found English {subtitle_info.subtitle_type} subtitles "
                        f"({subtitle_info.language_code}), downloading & translating"
                    )
                    srt_path = download_subtitle(
                        url=url,
                        language=subtitle_info.language_code,
                        subtitle_type=subtitle_info.subtitle_type,
                        output_dir=config.subtitle_dir,
                        name=name,
                        cookie_file=subtitle_cookie_file,
                    )

                    llm_client = create_llm_client()
                    chinese_text = translate_srt_to_chinese(srt_path, llm_client, concurrency=config.llm_concurrency)
                    text_source = TextSource(
                        source_type="subtitle_en_translated",
                        full_text=chinese_text,
                        source_path=srt_path,
                    )
                else:
                    raise RuntimeError(f"Unexpected subtitle language: {subtitle_info.language_code}")

                # Skip to generation
                logger.info("Step 1/4: Generating document from subtitles...")
                summarizer = Summarizer(config)
                doc_path = summarizer.generate_document(text_source, name)
                logger.info(f"Document saved to: {doc_path}")

                logger.info("Step 2/4: Generating brief summary...")
                brief = summarizer.generate_brief(text_source)

                logger.info("Step 3/4: Sending notification...")
                notifier = Notifier(config)
                notifier.send(brief, doc_path)

                logger.info("========== Processing complete ==========")
                return 0

            except RuntimeError:
                # Subtitle download failed - fall back to normal flow
                logger.warning("Subtitle download failed, falling back to audio download & transcription")
        logger.info("No subtitles found, proceeding with audio download & transcription")

        # Step 1: Download
        logger.info("Step 1/5: Downloading audio...")
        downloader = Downloader(config)
        audio_path = downloader.download(url, name)
        logger.info(f"Audio saved to: {audio_path}")

        # Step 2: Transcribe
        logger.info("Step 2/5: Transcribing (this may take a while)...")
        transcriber = Transcriber(config)
        transcript = transcriber.transcribe(audio_path)
        logger.info(f"Transcript saved to: {transcript.source_path}")

        # Step 3: Generate document
        logger.info("Step 3/5: Generating detailed document...")
        summarizer = Summarizer(config)
        doc_path = summarizer.generate_document(transcript, name)
        logger.info(f"Document saved to: {doc_path}")

        # Step 4: Generate brief
        logger.info("Step 4/5: Generating brief summary...")
        brief = summarizer.generate_brief(transcript)

        # Step 5: Send notification
        logger.info("Step 5/5: Sending notification...")
        notifier = Notifier(config)
        notifier.send(brief, doc_path)

        # Cleanup audio file
        try:
            audio_path.unlink()
        except OSError:
            pass

        logger.info("========== Processing complete ==========")
        return 0

    except DownloadError as e:
        logger.error(f"Download failed: {e}")
        _send_error_notification(f"下载失败：{e}")
        return 1
    except TranscriptionError as e:
        logger.error(f"Transcription failed: {e}")
        _send_error_notification(f"转写失败：{e}")
        return 1
    except SummarizationError as e:
        logger.error(f"Summarization failed: {e}")
        _send_error_notification(f"AI总结失败：{e}")
        return 1
    except NotificationError as e:
        logger.error(f"Notification failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        _send_error_notification(f"未知错误：{e}")
        return 1


def _send_error_notification(message: str) -> None:
    """Send error notification via openclaw."""
    try:
        config = Config.load()
        notifier = Notifier(config)
        notifier.send(
            Summary(content=f"播客转写失败：{message}"),
            Path("error")
        )
    except Exception:
        pass


def entry_point() -> None:
    """CLI entry point."""
    setup_logging()

    parser = argparse.ArgumentParser(description="Podcast Transcription Agent")
    parser.add_argument("url", help="URL to download and transcribe")
    parser.add_argument("name", nargs="?", default="podcast", help="Podcast name")
    args = parser.parse_args()

    sys.exit(main(args.url, args.name))


if __name__ == "__main__":
    entry_point()
