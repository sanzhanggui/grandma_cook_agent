#!/usr/bin/env python3
"""
Custom Event Demo Agent

This agent demonstrates how to use custom events with the @on_event decorator.
It handles a custom event 'custom.hello_world' and processes text input by adding a prefix.
"""

import asyncio
import logging
from typing import Dict, Any
from openagents.models.event import Event
from openagents.agents.worker_agent import WorkerAgent, EventContext, ChannelMessageContext, on_event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NETWORK_PORT = 8700


class CustomEventDemoAgent(WorkerAgent):
    """
    Demo agent that shows how to use custom events with the @on_event decorator.
    """
    
    default_agent_id = "custom-event-demo"
    auto_mention_response = True
    default_channels = ["general", "#生成菜谱卡片"]
    
    def __init__(self, **kwargs):
        """Initialize the Custom Event Demo Agent."""
        super().__init__(**kwargs)
        logger.info(f"Initialized Custom Event Demo Agent with ID: {self.agent_id}")
    
    async def on_startup(self):
        """Initialize the agent."""
        logger.info(f"🤖 Custom Event Demo Agent '{self.default_agent_id}' starting up...")
        
        # Send startup message to general channel
        try:
            ws = self.workspace()
            ws._auto_connect_config = {
                'host': 'localhost',
                'port': NETWORK_PORT
            }
            channels_info = await ws.channels()
            logger.info(f"📺 Available channels: {channels_info}")
        except Exception as e:
            logger.error(f"❌ Failed to send startup message: {e}")
        
        logger.info("✅ Custom Event Demo Agent startup complete")
    
    async def on_shutdown(self):
        """Clean shutdown of the agent."""
        logger.info("🛑 Custom Event Demo Agent shutting down...")
        logger.info("✅ Custom Event Demo Agent shutdown complete")
    
    async def on_direct(self, context: EventContext):
        """Handle direct messages."""
        logger.info(f"Received direct message from {context.source_id}: {context.text}")
        
        # Echo back the received message
        response_text = f"Hello {context.source_id}! I received your message: '{context.text}'"
        self.send_direct(context.source_id, response_text)
    
    async def on_channel_mention(self, context: ChannelMessageContext):
        """Handle channel mentions."""
        logger.info(f"Received channel mention from {context}")
        incoming_event = context.incoming_event
        await self.workspace().channel(context.channel).post(
            f"Hello {incoming_event.sender_id}! You mentioned me in the channel.",
        )
    
    @on_event("thread.direct_message.notification")
    async def on_direct_message_notification(self, context: EventContext):
        """Handle direct message notifications."""
        logger.info(f"Received direct message notification from {context.source_id}: {context.text}")
        response_text = f"Thanks for your message: {context.text}. This is an automated response."
        self.send_direct(context.source_id, response_text)
    
    @on_event("custom.hello_world")
    async def handle_custom_hello_world(self, context: EventContext):
        """
        Handle the custom.hello_world event.
        This demonstrates how to create a custom event handler.
        """
        logger.info(f"Received custom.hello_world event: {context.incoming_event.payload}")
        
        # Extract text from the event payload
        input_text = context.incoming_event.payload.get('text', '')
        prefix = context.incoming_event.payload.get('prefix', 'PREFIX:')
        
        # Process the text by adding a prefix
        processed_text = f"{prefix} {input_text}"
        
        # Log the processing
        logger.info(f"Processing: '{input_text}' -> '{processed_text}'")
        
        # Post the result to a channel
        try:
            ws = self.workspace()
            ws._auto_connect_config = {
                'host': 'localhost',
                'port': NETWORK_PORT
            }
            await ws.channel("general").post(f"🔄 Custom event processed: '{input_text}' => '{processed_text}'")
        except Exception as e:
            logger.error(f"❌ Failed to post to channel: {e}")
        
        # Optionally send a direct response to the event sender
        try:
            response_event = Event(
                event_name="custom.hello_world.response",
                source_id=self.agent_id,
                destination_id=context.incoming_event.source_id,
                payload={
                    "original_text": input_text,
                    "processed_text": processed_text,
                    "status": "processed"
                }
            )
            await self.client.send_event(response_event)
        except Exception as e:
            logger.error(f"❌ Failed to send response event: {e}")
    
    @on_event("demo.text.process")
    async def handle_demo_text_process(self, context: EventContext):
        """
        Another example of a custom event handler.
        """
        logger.info(f"Received demo.text.process event: {context.incoming_event.payload}")
        
        input_text = context.incoming_event.payload.get('text', '')
        operation = context.incoming_event.payload.get('operation', 'uppercase')
        
        # Perform different text operations based on the payload
        if operation == 'uppercase':
            processed_text = input_text.upper()
        elif operation == 'lowercase':
            processed_text = input_text.lower()
        elif operation == 'reverse':
            processed_text = input_text[::-1]
        else:
            processed_text = f"UNKNOWN OPERATION: {input_text}"
        
        # Post the result
        try:
            ws = self.workspace()
            ws._auto_connect_config = {
                'host': 'localhost',
                'port': NETWORK_PORT
            }
            await ws.channel("general").post(f"⚙️ Text operation '{operation}' applied: '{input_text}' => '{processed_text}'")
        except Exception as e:
            logger.error(f"❌ Failed to post to channel: {e}")
    
    @on_event("recipe.request")
    async def handle_recipe_request(self, context: EventContext):
        """
        Handle recipe requests - adapted from the product review pattern.
        """
        logger.info(f"Received recipe request: {context.incoming_event.payload}")
        
        # Extract recipe information from the event payload
        recipe_name = context.incoming_event.payload.get('recipe_name', 'Unknown Recipe')
        ingredients = context.incoming_event.payload.get('ingredients', [])
        
        # Generate a simulated recipe response
        recipe_details = self._generate_recipe_details(recipe_name, ingredients)
        
        # Log the processing
        logger.info(f"Generated recipe for: '{recipe_name}' with {len(ingredients)} ingredients")
        
        # Post the result to a channel
        try:
            ws = self.workspace()
            ws._auto_connect_config = {
                'host': 'localhost',
                'port': NETWORK_PORT
            }
            await ws.channel("general").post(f"🍳 Recipe for '{recipe_name}':\n{recipe_details}")
        except Exception as e:
            logger.error(f"❌ Failed to post recipe to channel: {e}")
        
        # Optionally send a direct response to the event sender
        try:
            response_event = Event(
                event_name="recipe.response",
                source_id=self.agent_id,
                destination_id=context.incoming_event.source_id,
                payload={
                    "recipe_name": recipe_name,
                    "ingredients": ingredients,
                    "recipe_details": recipe_details,
                    "status": "completed"
                }
            )
            await self.client.send_event(response_event)
        except Exception as e:
            logger.error(f"❌ Failed to send recipe response event: {e}")

    def _generate_recipe_details(self, recipe_name: str, ingredients: list) -> str:
        """
        Generate a simulated recipe based on the provided name and ingredients.
        """
        steps = [
            "准备所有食材并清洗干净",
            f"将 {', '.join(ingredients[:2])} 切成适当大小",
            "热锅加油，放入主料翻炒",
            "加入调料，继续翻炒均匀",
            "加水炖煮10-15分钟",
            "调味后收汁即可出锅"
        ]
        
        recipe = f"""
        📝 **{recipe_name} 制作方法**
        
        **所需食材:**
        - {chr(10).join(['- ' + ingredient for ingredient in ingredients])}
        
        **制作步骤:**
        {chr(10).join([f"{i+1}. {step}" for i, step in enumerate(steps)])}
        
        **小贴士:** 
        这道菜需要掌握火候，建议中小火慢炖，让食材充分入味。
        """
        
        return recipe.strip()


async def main():
    """Main function to run the Custom Event Demo Agent."""
    print("🚀 Starting Custom Event Demo Agent...")
    print("=" * 60)
    print("This agent demonstrates custom event handling with @on_event")
    print("It handles 'custom.hello_world' and 'demo.text.process' events")
    print("-" * 60)
    
    # Create the agent
    agent = CustomEventDemoAgent(agent_id="custom-event-demo")
    
    try:
        # Connect to the network
        print("🔌 Connecting to network...")
        await agent.async_start(network_host="localhost", network_port=NETWORK_PORT)
        print("✅ Connected successfully!")
        
        # Keep the agent running
        print("🤖 Custom Event Demo Agent is now active...")
        print("📋 Press Ctrl+C to stop the agent")
        
        # Run indefinitely
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Custom Event Demo Agent...")
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean shutdown
        await agent.async_stop()
        print("👋 Custom Event Demo Agent stopped")


if __name__ == "__main__":
    # Run the agent
    asyncio.run(main())