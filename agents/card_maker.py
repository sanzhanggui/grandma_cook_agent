#!/usr/bin/env python3
"""
Card Maker Agent - Creates recipe cards with QR codes from markdown recipes.

This agent listens for recipe markdown content and generates a PNG card
with QR code linking to the full recipe, storing it using the shared artifact mod.
"""

import asyncio
import sys
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageFont
from markdown import Markdown
import io
import re

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from openagents.agents.worker_agent import WorkerAgent, on_event
from openagents.models.event_context import EventContext
from openagents.models.agent_config import AgentConfig


class CardMakerAgent(WorkerAgent):
    """An agent that creates recipe cards with QR codes from markdown recipes."""

    default_agent_id = "card-maker"

    def __init__(self, **kwargs):
        # Create agent config
        agent_config = AgentConfig(
            instruction="""您是卡片制作代理。您的工作是将菜谱markdown转换为带有二维码的精美PNG卡片。

            当您接收到标准菜谱时，生成一个包含以下内容的视觉上吸引人的卡片：
            1. 菜谱标题
            2. 主要食材（以紧凑形式）
            3. 链接到完整菜谱的二维码
            4. 便于阅读的基本样式
            
            使用shared_artifact模块存储生成的PNG以供下载。""",
        )
        super().__init__(agent_config=agent_config, **kwargs)

    async def on_startup(self):
        """Called when agent starts and connects to the network."""
        print("Card Maker Agent is running! Press Ctrl+C to stop.")
        print("Waiting for recipe markdown to generate cards...")

    async def on_shutdown(self):
        """Called when agent shuts down."""
        print("Card Maker Agent stopped.")

    async def react(self, context: EventContext):
        """React to incoming recipe markdown by generating a card with QR code."""
        # Skip our own messages
        if context.incoming_event.source_id == self.agent_id:
            return

        print(f"Event received: {context.incoming_event.event_name}")
        print(f"Event source: {context.incoming_event.source_id}")
        print(f"Agent ID: {self.agent_id}")

    @on_event('recipe.md.processed')
    async def handle_recipe_processed(self, context: EventContext):
        """Handle recipe markdown processing events."""
        event = context.incoming_event
        content = event.payload.get("content", "")
        recipe_id = event.payload.get("recipe_id", "default")
        
        if content:
            print(f"Handling recipe.md.processed event for recipe: {recipe_id}")
            await self.generate_recipe_card(content, recipe_id, context)

    async def generate_recipe_card(self, markdown_content, recipe_id, context):
        """Generate a recipe card with QR code from markdown content."""
        try:
            print(f"开始处理菜谱卡片生成，ID: {recipe_id}")
            
            # Use markdown library to convert content to HTML for better parsing
            md = Markdown(extensions=['meta', 'tables', 'fenced_code'])
            html_content = md.convert(markdown_content)
            
            print(f"Markdown已转换为HTML，长度: {len(html_content)}")
            
            # Extract content using the markdown library's features
            lines = markdown_content.split('\n')
            title = "未知菜谱"
            ingredients = []
            instructions_preview = []
            
            print(f"开始解析Markdown内容，共 {len(lines)} 行")
            
            # Extract title from H1
            for line in lines:
                line = line.strip()
                if line.startswith('# ') and title == "未知菜谱":
                    title = line[2:].strip()
                    print(f"提取到菜谱标题: {title}")
                    break
            
            # More robust parsing using regex to find ingredients and instructions
            ingredients_section = False
            instructions_section = False
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                
                # Check for section headers
                if line.startswith('## 食材') or '## Ingredients' in line:
                    ingredients_section = True
                    instructions_section = False
                    print(f"检测到食材部分，行号: {line_num}")
                    continue
                elif line.startswith('## 制作步骤') or '## Instructions' in line:
                    ingredients_section = False
                    instructions_section = True
                    print(f"检测到制作步骤部分，行号: {line_num}")
                    continue
                elif line.startswith('##'):
                    # If we encounter another section, reset both flags
                    ingredients_section = False
                    instructions_section = False
                
                # Extract ingredients
                if ingredients_section and line.startswith('- '):
                    ingredient = line[2:].strip()
                    if len(ingredient) > 80:
                        ingredient = ingredient[:80] + "..."
                    ingredients.append(ingredient)
                    print(f"提取到食材: {ingredient}")
                    if len(ingredients) >= 5:  # Only take first 5 ingredients
                        print(f"已达到食材数量上限: {len(ingredients)} 个")
                        break
                
                # Extract instructions
                if instructions_section and re.match(r'^\d+\.\s', line) and len(instructions_preview) < 3:
                    # Match lines starting with "number. " (e.g., "1. ", "2. ", etc.)
                    instruction = re.sub(r'^\d+\.\s*', '', line).strip()
                    if len(instruction) > 60:
                        instruction = instruction[:60] + "..."
                    instructions_preview.append(instruction)
                    print(f"提取到制作步骤: {instruction}")

            print(f"解析完成 - 标题: {title}, 食材数量: {len(ingredients)}, 步骤预览数量: {len(instructions_preview)}")
            
            # Create a QR code linking to the recipe
            qr_url = f"http://localhost:8700/recipes/{recipe_id}"  # Placeholder URL
            qr_img = qrcode.make(qr_url)
            qr_img = qr_img.resize((100, 100))  # Resize QR code
            
            print(f"QR码已生成，链接: {qr_url}")
            
            # Create the card image
            card_width, card_height = 600, 800
            card = Image.new('RGB', (card_width, card_height), color='white')
            draw = ImageDraw.Draw(card)
            
            # Try to load a font (fall back to default if not available)
            try:
                # Attempt to load a font (platform specific)
                import platform
                if platform.system() == "Windows":
                    font_title = ImageFont.truetype("simsun.ttc", 36)  # Use SimSun font for Chinese
                    font_subtitle = ImageFont.truetype("simsun.ttc", 24)
                    font_body = ImageFont.truetype("simsun.ttc", 18)
                else:
                    font_title = ImageFont.truetype("DejaVuSans.ttf", 36)
                    font_subtitle = ImageFont.truetype("DejaVuSans.ttf", 24)
                    font_body = ImageFont.truetype("DejaVuSans.ttf", 18)
            except:
                # Use default font if specific font not available
                font_title = ImageFont.load_default()
                font_subtitle = ImageFont.load_default()
                font_body = ImageFont.load_default()
            
            # Draw title
            title_y = 40
            draw.text((30, title_y), title, fill='black', font=font_title)
            
            # Draw "Ingredients" header
            ingredients_y = title_y + 70
            draw.text((30, ingredients_y), "食材:", fill='black', font=font_subtitle)
            
            # Draw ingredients list
            ingredient_y = ingredients_y + 40
            for i, ingredient in enumerate(ingredients):
                draw.text((40, ingredient_y + i*30), f"• {ingredient}", fill='black', font=font_body)
            
            # Draw "Instructions Preview" header
            instructions_y = ingredient_y + len(ingredients)*30 + 30
            draw.text((30, instructions_y), "制作步骤预览:", fill='black', font=font_subtitle)
            
            # Draw instructions preview
            instruction_y = instructions_y + 40
            for i, instruction in enumerate(instructions_preview):
                draw.text((40, instruction_y + i*25), f"{i+1}. {instruction}", fill='black', font=font_body)
            
            # Paste QR code
            qr_x = card_width - 130  # Position QR code in bottom right
            qr_y = card_height - 130
            card.paste(qr_img, (qr_x, qr_y))
            
            # Draw QR code label
            qr_label_y = qr_y - 30
            draw.text((qr_x, qr_label_y), "扫描获取完整菜谱", fill='black', font=font_body)
            
            print("菜谱卡片绘制完成，开始保存为字节流")
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            card.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            png_bytes = img_byte_arr.read()
            
            print(f"图片已转换为字节流，大小: {len(png_bytes)} 字节")
            
            # Store the card using shared_artifact mod
            artifact = self.client.mod_adapters.get("openagents.mods.workspace.shared_artifact")
            if artifact:
                print("共享资源模块已找到，开始存储菜谱卡片")
                await artifact.put(key=f"recipe_card_{recipe_id}.png", value=png_bytes)
                print(f"Recipe card stored for {recipe_id}")
                
                # Send a message to the recipe-cards channel
                messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
                if messaging:
                    download_url = f"http://localhost:8700/artifacts/download/recipe_card_{recipe_id}.png"
                    message = f"🎉 菜谱卡片已生成！下载您的带二维码的卡片: {download_url}"
                    print(f"向 recipe-cards 频道发送消息: {message}")
                    await messaging.send_channel_message(
                        channel="recipe-cards",
                        text=message
                    )
                    
                    # Publish the completion event
                    print(f"发布完成事件: recipe.card.generated")
                    await context.create_event(
                        name="recipe.card.generated",
                        payload={
                            "recipe_id": recipe_id,
                            "card_url": download_url
                        }
                    )
                    
                    print(f"Notification and completion event sent for recipe {recipe_id}")
                else:
                    print("Messaging 模块未找到")
            else:
                print("Shared artifact mod not available")
                
        except Exception as e:
            print(f"Error generating recipe card: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run the Card Maker agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Card Maker Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument("--url", default=None, help="Connection URL (e.g., grpc://localhost:8600 for direct gRPC)")
    args = parser.parse_args()

    agent = CardMakerAgent()

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

        print("Agent 启动成功，等待事件...")
        
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