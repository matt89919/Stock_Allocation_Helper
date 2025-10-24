# portfolio_tracker/consumers.py
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class PriceUpdateConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # A user connects to the WebSocket
        await self.channel_layer.group_add(
            "price_updates", self.channel_name
        )
        await self.accept()
        print(f"WebSocket client connected: {self.channel_name}")

    async def disconnect(self, close_code):
        # A user disconnects
        await self.channel_layer.group_discard(
            "price_updates", self.channel_name
        )
        print(f"WebSocket client disconnected: {self.channel_name}")

    # This method is a handler for messages sent to the 'price_updates' group
    async def price_update(self, event):
        # The 'event' dictionary contains the data sent from our Celery task
        message_data = event["data"]

        # Send the data down to the connected frontend client
        await self.send_json(
            {
                "type": "price.update",
                "data": message_data,
            }
        )