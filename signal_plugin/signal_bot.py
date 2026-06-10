import requests
import db
import core
import asyncio
from logger import get_logger
from typing import Optional

# Get logger for this module
logger = get_logger(__name__)

class SignalBot:
    def __init__(self, queue):
        try:
            # Get Signal configuration from database
            self.signal_api_url = db.get_parameter("signal_api_url")
            self.signal_phone = db.get_parameter("signal_phone")
            self.signal_recipient = db.get_parameter("signal_recipient")
            
            # Create the item queue to send to Signal
            self.new_items_queue = queue
            
            # Start the queue processor
            asyncio.create_task(self.check_signal_queue())
            
            logger.info("Signal bot initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Signal bot: {str(e)}", exc_info=True)

    async def check_signal_queue(self):
        """Process the queue of new items and send them to Signal."""
        while True:
            try:
                if not self.new_items_queue.empty():
                    item = await self.new_items_queue.get()
                    await self.send_new_post(item)
                    self.new_items_queue.task_done()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error processing Signal queue: {str(e)}", exc_info=True)
                await asyncio.sleep(5)  # Wait a bit before retrying

    async def send_new_post(self, item):
        """Send a new post to Signal."""
        try:
            # Format the message
            message = self._format_message(item)
            
            # Send the message using signal-cli-rest-api
            response = requests.post(
                f"{self.signal_api_url}/v2/send",
                json={
                    "message": message,
                    "number": self.signal_phone,
                    "recipients": [self.signal_recipient]
                }
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully sent message to Signal for item {item.get('id')}")
            else:
                logger.error(f"Failed to send message to Signal. Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending message to Signal: {str(e)}", exc_info=True)

    def _format_message(self, item: dict) -> str:
        """Format the item data into a readable message."""
        try:
            title = item.get('title', 'No title')
            price = item.get('price', 'No price')
            currency = item.get('currency', '')
            url = item.get('url', 'No URL')
            brand = item.get('brand_title', 'No brand')
            size = item.get('size_title', 'No size')
            
            message = (
                f"🆕 New Item Found!\n\n"
                f"📌 {title}\n"
                f"💰 {price} {currency}\n"
                f"🏷️ {brand}\n"
                f"📏 {size}\n"
                f"🔗 {url}"
            )
            
            return message
        except Exception as e:
            logger.error(f"Error formatting message: {str(e)}", exc_info=True)
            return "Error formatting message"

    async def send_error_message(self, error_message: str):
        """Send an error message to Signal."""
        try:
            response = requests.post(
                f"{self.signal_api_url}/v2/send",
                json={
                    "message": f"❌ Error: {error_message}",
                    "number": self.signal_phone,
                    "recipients": [self.signal_recipient]
                }
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to send error message to Signal. Status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending error message to Signal: {str(e)}", exc_info=True) 
