from openagents.workspace.tool_decorator import tool
import qrcode
from PIL import Image, ImageDraw, ImageFont
from markdown import Markdown
import io
import re


@tool(description="从markdown菜谱内容生成带二维码的菜谱卡片")
async def generate_recipe_card(markdown_content: str, recipe_id: str) -> str:
    """根据markdown内容生成菜谱卡片，并返回生成结果信息."""
    try:
        # Use markdown library to convert content to HTML for better parsing
        md = Markdown(extensions=['meta', 'tables', 'fenced_code'])
        html_content = md.convert(markdown_content)
        
        # Extract content using the markdown library's features
        lines = markdown_content.split('\n')
        title = "未知菜谱"
        ingredients = []
        instructions_preview = []
        
        # Extract title from H1
        for line in lines:
            line = line.strip()
            if line.startswith('# ') and title == "未知菜谱":
                title = line[2:].strip()
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
                continue
            elif line.startswith('## 制作步骤') or '## Instructions' in line:
                ingredients_section = False
                instructions_section = True
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
                if len(ingredients) >= 5:  # Only take first 5 ingredients
                    break
            
            # Extract instructions
            if instructions_section and re.match(r'^\d+\.\s', line) and len(instructions_preview) < 3:
                # Match lines starting with "number. " (e.g., "1. ", "2. ", etc.)
                instruction = re.sub(r'^\d+\.\s*', '', line).strip()
                if len(instruction) > 60:
                    instruction = instruction[:60] + "..."
                instructions_preview.append(instruction)

        # Create a QR code linking to the recipe
        qr_url = f"http://localhost:8700/recipes/{recipe_id}"  # Placeholder URL
        qr_img = qrcode.make(qr_url)
        qr_img = qr_img.resize((100, 100))  # Resize QR code
        
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
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        card.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        png_bytes = img_byte_arr.read()
        
        # For the tool, we'll just return info about the card generated
        # In a real implementation, this would save the card to a persistent location
        return f"成功为菜谱 '{title}' (ID: {recipe_id}) 生成了卡片，包含 {len(ingredients)} 个食材和 {len(instructions_preview)} 个制作步骤预览。"
        
    except Exception as e:
        return f"生成菜谱卡片时发生错误: {str(e)}"