#!/usr/bin/env python3
"""
LLM Agent - Handles recipe processing via chat interface

This agent allows users to interact via chat to trigger recipe processing workflows.
It can receive recipe text via chat and trigger the recipe processing pipeline.
"""

import asyncio
import sys
from pathlib import Path
import json
import logging

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from openagents.agents.collaborator_agent import CollaboratorAgent
from openagents.models.event_context import EventContext
from openagents.models.agent_config import AgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LlmAgent(CollaboratorAgent):
    """An LLM agent that handles recipe processing via chat interface."""

    default_agent_id = "llm-agent"

    def __init__(self, **kwargs):
        # Create agent config
        agent_config = AgentConfig(
            instruction="""您是一个菜谱处理助手，帮助用户处理菜谱相关的请求。

            您可以：
            1. 接收用户输入的菜谱文本
            2. 将菜谱文本标准化为markdown格式
            3. 触发菜谱卡片生成流程

            当用户提交菜谱内容时，您应该：
            - 理解用户提交的菜谱内容
            - 将菜谱内容转换为标准markdown格式
            - 触发后续处理流程生成菜谱卡片""",
            react_to_all_messages=True
        )
        super().__init__(agent_config=agent_config, **kwargs)

    async def on_startup(self):
        """Called when agent starts and connects to the network."""
        logger.info("LLM Agent is running! Press Ctrl+C to stop.")
        logger.info("Ready to process recipe requests via chat...")

    async def on_shutdown(self):
        """Called when agent shuts down."""
        logger.info("LLM Agent stopped.")

    async def react(self, context: EventContext):
        """React to incoming messages by processing recipe requests."""
        # Skip our own messages
        if context.incoming_event.source_id == self.agent_id:
            return

        logger.info(f"Event received: {context.incoming_event.event_name}")
        logger.info(f"Event source: {context.incoming_event.source_id}")
        
        # Process chat messages that contain recipe requests
        payload = context.incoming_event.payload
        content = ""
        
        # Check if payload is a dict and has content
        if isinstance(payload, dict):
            # Try different possible keys for content
            content = payload.get("content", "")
            if not content:
                content = payload.get("text", "")
            if not content and "message" in payload:
                content = payload["message"]
            # If content is still empty, try to convert the entire payload to string
            if not content:
                content = str(payload)
        else:
            # If payload is not a dict, it might already be the content
            content = str(payload) if payload else ""
        
        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content)
        
        if content:
            # Check if this looks like a recipe request
            if any(keyword in content.lower() for keyword in 
                  ["菜谱", "recipe", "做法", "cooking", "cook", "how to make", "怎么做", "食谱", "ingredients", "instructions"]):
                logger.info(f"Processing recipe request: {content[:100]}...")
                
                # Trigger the recipe processing workflow
                await self._trigger_recipe_processing(content, context)
            else:
                # For other messages, just acknowledge
                response = f"收到您的消息。如果您想创建菜谱卡片，请提供菜谱内容，我会帮您处理。"
                await self.send_direct_message(context.incoming_event.source_id, response)

    async def _trigger_recipe_processing(self, recipe_content, context):
        """Trigger the recipe processing workflow."""
        try:
            logger.info("开始触发菜谱处理流程...")
            
            # Send a message to the user acknowledging the request
            await self.send_direct_message(
                context.incoming_event.source_id, 
                "正在处理您的菜谱请求，将其转换为标准格式..."
            )
            
            # Publish the recipe text event to trigger the processing pipeline
            await context.create_event(
                name="recipe.text.transcribed",  # This matches the event polisher listens for
                payload={
                    "content": recipe_content,
                    "recipe_id": f"recipe_{context.incoming_event.id}" if hasattr(context.incoming_event, 'id') else "manual_recipe",
                    "source": "llm_agent"
                }
            )
            
            logger.info("菜谱处理事件已发布，等待后续处理...")
            
            # Send a message to the recipe processing channel
            messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
            if messaging:
                await messaging.send_channel_message(
                    channel="recipe.md",
                    text=f"📝 新菜谱已提交，正在处理中..."
                )
                
        except Exception as e:
            logger.error(f"处理菜谱请求时出错: {e}")
            await self.send_direct_message(
                context.incoming_event.source_id,
                f"处理菜谱时出现错误: {str(e)}"
            )


async def main():
    """Run the LLM Agent."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Agent for Recipe Processing")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument("--url", default=None, help="Connection URL (e.g., grpc://localhost:8600 for direct gRPC)")
    args = parser.parse_args()

    agent = LlmAgent()

    try:
        if args.url:
            # Use URL for direct connection (useful for Docker port mapping)
            print(f"尝试连接到 {args.url}...")
            await agent.async_start(url=args.url)
        else:
            print(f"尝试连接到网络 {args.host}:{args.port}...")
            await agent.async_start(
                network_host=args.host,
                network_port=args.port,
            )

        print("LLM Agent 启动成功，等待消息...")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"启动 Agent 时发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("停止 Agent...")
        try:
            await agent.async_stop()
        except:
            pass  # 如果 agent 没有成功启动，停止时可能会出错


if __name__ == "__main__":
    asyncio.run(main())