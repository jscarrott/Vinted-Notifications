import asyncio
import base64
import re
from collections import defaultdict

import requests

import db
from logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Used if no signal_message_template is configured in the database
DEFAULT_TEMPLATE = (
    "🆕 {title}\n"
    "💶 Price: {price}\n"
    "🏷️ Brand: {brand}\n"
    "📏 Size: {size}\n"
    "🔗 {url}"
)


class SignalBot:
    def __init__(self, queue):
        # Get Signal configuration from database
        self.signal_api_url = db.get_parameter("signal_api_url")
        self.signal_phone = db.get_parameter("signal_phone")

        # The shared queue of new items to send to Signal
        self.new_items_queue = queue

        logger.info("Signal bot initialized successfully")

    @staticmethod
    def _parse_recipients(value):
        """Split a ';' or ',' separated recipient string into a clean list."""
        if not value:
            return []
        return [r.strip() for r in re.split(r"[;,]", value) if r.strip()]

    def _recipients_for(self, query_id):
        """Resolve the recipients for an item, falling back to the default.

        Read fresh each time so config changes take effect without a restart.
        """
        recipients = []
        if query_id is not None:
            recipients = db.get_query_signal_recipients(query_id)
        if recipients:
            return recipients
        return self._parse_recipients(db.get_parameter("signal_recipient"))

    async def _fetch_attachment(self, url):
        """Download an image URL and return it as a base64 data URI, or None."""
        if not url:
            return None
        try:
            response = await asyncio.to_thread(requests.get, url, timeout=15)
            if response.status_code != 200:
                logger.warning(
                    f"Could not fetch item image ({response.status_code}); sending text only"
                )
                return None
            mime = response.headers.get("Content-Type", "image/jpeg").split(";")[0]
            encoded = base64.b64encode(response.content).decode("ascii")
            return f"data:{mime};base64,{encoded}"
        except Exception as e:
            logger.warning(f"Error fetching item image, sending text only: {e}")
            return None

    def _format_message(self, item):
        """Build the Signal message for an item using the configured template."""
        template = db.get_parameter("signal_message_template") or DEFAULT_TEMPLATE
        price = item.get("price")
        currency = item.get("currency") or ""
        fields = {
            "title": item.get("title", ""),
            "price": f"{price} {currency}".strip() if price is not None else "",
            "brand": item.get("brand") or "",
            "size": item.get("size") or "N/A",
            "url": item.get("url", ""),
        }
        try:
            # defaultdict avoids KeyError if the template has extra placeholders
            return template.format_map(defaultdict(str, fields))
        except Exception as e:
            logger.error(f"Error formatting Signal message: {e}", exc_info=True)
            # Fall back to the pre-formatted content plus the URL
            content = item.get("content", "")
            url = item.get("url", "")
            return f"{content}\n{url}" if url else content

    async def check_signal_queue(self):
        """Poll the queue of new items and send them to Signal.

        Items are dicts produced by core.clear_item_queue. The queue is a
        multiprocessing.Queue, so we poll it without blocking the event loop.
        """
        logger.info("Signal bot queue processor started")
        while True:
            try:
                if not self.new_items_queue.empty():
                    item = self.new_items_queue.get()
                    await self.send_new_post(item)
                else:
                    await asyncio.sleep(0.1)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                logger.error(f"Error processing Signal queue: {str(e)}", exc_info=True)
                await asyncio.sleep(5)  # Wait a bit before retrying

    async def send_new_post(self, item):
        """Send a new item notification to its target Signal recipients."""
        recipients = self._recipients_for(item.get("query_id"))
        if not recipients:
            logger.warning(
                "No Signal recipients for item (query_id=%s) and no default set; skipping",
                item.get("query_id"),
            )
            return

        message = self._format_message(item)
        payload = {
            "message": message,
            "number": self.signal_phone,
            "recipients": recipients,
        }

        # Optionally attach the item photo
        if db.get_parameter("signal_include_image") == "True":
            attachment = await self._fetch_attachment(item.get("photo"))
            if attachment:
                payload["base64_attachments"] = [attachment]

        try:
            # signal-cli-rest-api is synchronous; run it off the event loop
            response = await asyncio.to_thread(
                requests.post,
                f"{self.signal_api_url}/v2/send",
                json=payload,
            )

            if response.status_code == 201:
                logger.info(
                    f"Successfully sent message to {len(recipients)} Signal recipient(s)"
                )
            else:
                logger.error(
                    f"Failed to send message to Signal. Status code: {response.status_code}, Response: {response.text}"
                )
        except Exception as e:
            logger.error(f"Error sending message to Signal: {str(e)}", exc_info=True)


async def run_signal_bot(queue):
    """Process entry point: build the bot and run its queue processor."""
    bot = SignalBot(queue)
    await bot.check_signal_queue()
