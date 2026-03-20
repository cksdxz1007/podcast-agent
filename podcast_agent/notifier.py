"""Notifier module - sends results via openclaw."""

import logging
import subprocess
from pathlib import Path

from .config import Config
from .models import Summary

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Raised when notification fails."""
    pass


class Notifier:
    """Sends notifications via openclaw binary."""

    def __init__(self, config: Config):
        self.config = config

    def send(self, brief: Summary, doc_path: Path) -> None:
        """Send brief summary and document path via openclaw to all configured channels.

        Args:
            brief: Summary object with content
            doc_path: Path to the generated document
        """
        logger.info("Sending notification...")

        message = f"""📝 播客转写完成！

{brief.content}

📄 详细文档: {doc_path}"""

        # Send to all configured channels
        channels = [
            ("telegram", self.config.telegram_user_id),
            ("feishu", self.config.feishu_user_id),
        ]

        for channel, user_id in channels:
            if not user_id:
                logger.info(f"Skipping {channel} - no user_id configured")
                continue

            logger.info(f"Sending to {channel}...")
            result = subprocess.run(
                [
                    str(self.config.openclaw_bin),
                    "message", "send",
                    "--channel", channel,
                    "-t", user_id,
                    "-m", message
                ],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to send to {channel}: {result.stderr}")
            else:
                logger.info(f"{channel.capitalize()} notification sent")

        logger.info("Notification complete")
