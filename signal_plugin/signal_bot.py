import asyncio
import requests
import db
from logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


class SignalBot:
    def __init__(self, queue):
        # Get Signal configuration from database
        self.signal_api_url = db.get_parameter("signal_api_url")
        self.signal_phone = db.get_parameter("signal_phone")
        self.signal_recipient = db.get_parameter("signal_recipient")

        # The shared queue of new items to send to Signal
        self.new_items_queue = queue

        logger.info("Signal bot initialized successfully")

    async def check_signal_queue(self):
        """Poll the queue of new items and send them to Signal.

        Items are produced by core.clear_item_queue as the tuple
        (content, url, text, buy_url, buy_text), where ``content`` is the
        already-formatted message. The queue is a multiprocessing.Queue, so we
        poll it without blocking the event loop.
        """
        logger.info("Signal bot queue processor started")
        while True:
            try:
                if not self.new_items_queue.empty():
                    content, url, text, buy_url, buy_text = self.new_items_queue.get()
                    await self.send_new_post(content, url)
                else:
                    await asyncio.sleep(0.1)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                logger.error(f"Error processing Signal queue: {str(e)}", exc_info=True)
                await asyncio.sleep(5)  # Wait a bit before retrying

    async def send_new_post(self, content, url=None):
        """Send a new item notification to Signal."""
        try:
            message = f"{content}\n{url}" if url else content

            # signal-cli-rest-api is synchronous; run it off the event loop
            response = await asyncio.to_thread(
                requests.post,
                f"{self.signal_api_url}/v2/send",
                json={
                    "message": message,
                    "number": self.signal_phone,
                    "recipients": [self.signal_recipient],
                },
            )

            if response.status_code == 201:
                logger.info("Successfully sent message to Signal")
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
