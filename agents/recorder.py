#!/usr/bin/env python3
"""
Recorder Agent - Voice to Text Converter
Listens for audio uploads and converts them to text using ASR
"""

import asyncio
import os
import sys
from pathlib import Path
import requests
from openai import OpenAI

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from openagents.agents.worker_agent import WorkerAgent, on_event
from openagents.models.event_context import EventContext
from openagents.models.agent_config import AgentConfig


class RecorderAgent(WorkerAgent):
    """An agent that converts voice recordings to text using ASR."""

    default_agent_id = "recorder"

    def __init__(self, **kwargs):
        # Create agent config
        agent_config = AgentConfig(
            instruction="""您是录音员 - 一个语音转文字助手，负责将语音菜谱转换为文字。

            您的使命：
            监听语音上传并使用ASR技术将其转换为文字。

            行为：
            - 监听 recipe.audio.new 事件
            - 将音频URL转换为文字转录
            - 将转录的文字发布到 recipe.text 频道
            - 在回复中包含置信度得分

            流程：
            1. 接收用户的音频文件URL
            2. 使用ASR工具将音频转录为文字
            3. 返回带有置信度得分的转录文字
            4. 触发菜谱处理流水线的下一步

            回复指南：
            - 保持原始菜谱的语调和细节
            - 保留任何地区烹饪术语或特殊说明
            - 标记不清楚的部分以供人工验证
            - 将转录内容适当格式化以进行下一步处理""",
        )
        super().__init__(agent_config=agent_config, **kwargs)

    async def on_startup(self):
        """Called when agent starts and connects to the network."""
        print("Recorder Agent is running! Waiting for audio files to transcribe.")
        print("Waiting for recipe.audio.new events...")

    
    async def on_shutdown(self):
        """Called when agent shuts down."""
        print("Recorder Agent stopped.")

    async def react(self, context: EventContext):
        """React to incoming audio events by converting them to text."""
        event = context.incoming_event

        # Skip our own messages
        if event.source_id == self.agent_id:
            return

        # Handle new audio events - fixed attribute access
        if event.event_name == "recipe.audio.new":
            audio_url = event.payload.get("audio_url", "")
            audio_filename = event.payload.get("filename", "audio.mp3")
            recipe_id = event.payload.get("recipe_id", "default")
            
            if audio_url:
                print(f"Received audio file for transcription: {audio_url}")
                await self.transcribe_audio(audio_url, recipe_id, context)

    async def transcribe_audio(self, audio_url, recipe_id, context):
        """Transcribe audio using OpenAI's Whisper API."""
        try:
            # Download the audio file
            print(f"Downloading audio file: {audio_url}")
            response = requests.get(audio_url)
            if response.status_code != 200:
                print(f"Failed to download audio file: {response.status_code}")
                return

            # Save to temporary file
            temp_filename = f"temp_{recipe_id}_audio.m4a"
            with open(temp_filename, 'wb') as f:
                f.write(response.content)

            print(f"Audio file downloaded and saved as {temp_filename}")
            
            # Use OpenAI's Whisper API for transcription
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            
            with open(temp_filename, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="text"
                )
            
            print(f"Transcription completed: {transcript}")
            
            # Remove the temporary file
            os.remove(temp_filename)
            
            # Publish the transcribed text
            messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
            if messaging:
                # Send the transcribed text to the next step in the pipeline
                await messaging.send_channel_message(
                    channel="recipe-uploads",  # Using same channel as the trigger
                    text=f"新菜谱已转录完成: {transcript}"
                )
                
                # Send a structured event for the next agent (polisher)
                # Changed from recipe.text.transcribed to recipe.text for consistency with YAML
                await context.create_event(
                    name="recipe.text",
                    payload={
                        "content": transcript,
                        "recipe_id": recipe_id,
                        "confidence": 0.9  # Placeholder confidence score
                    }
                )
                
                print(f"Transcription sent for recipe {recipe_id}")
            else:
                print("Messaging mod not available")
                
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run the Recorder agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Recorder Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument("--url", default=None, help="Connection URL (e.g., grpc://localhost:8600 for direct gRPC)")
    args = parser.parse_args()

    agent = RecorderAgent()

    try:
        if args.url:
            # Use URL for direct connection (useful for Docker port mapping)
            await agent.async_start(url=args.url)
        else:
            await agent.async_start(
                network_host=args.host,
                network_port=args.port,
            )

        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())