import os
from crewai.tools import tool
from rembg import remove
from PIL import Image, ImageDraw, ImageFont

@tool("background_removal_and_resize")
def background_removal_and_resize(image_path: str, text: str = "", text_color: str = "#000000"):
    """画像を背景削除し、指定色で商品名を印字します。"""
    try:
        input_image = Image.open(image_path)
        output_image = remove(input_image)
        background = Image.new("RGBA", output_image.size, (255, 255, 255))
        combined = Image.alpha_composite(background, output_image).convert("RGB")
        
        if text:
            draw = ImageDraw.Draw(combined)
            font_path = "NotoSansJP-Bold.ttf"
            if os.path.exists(font_path):
                font_size = int(combined.height * 0.07)
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()

            color_hex = text_color.lstrip('#')
            rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))

            bbox = draw.textbbox((0, 0), text, font=font)
            text_w, text_h = bbox[3] - bbox, bbox[4] - bbox[5]
            x = (combined.width - text_w) // 2
            y = combined.height - text_h - 60
            draw.text((x, y), text, font=font, fill=rgb)
            
        output_path = f"processed_{os.path.basename(image_path)}"
        combined.save(output_path, "JPEG")
        return f"画像処理完了"
    except Exception as e:
        return f"画像処理エラー: {str(e)}"

@tool("product_web_research")
def product_web_research(product_name: str):
    """WEB調査を実行します。"""
    from firecrawl import FirecrawlApp
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key: return "APIキー不足"
    app = FirecrawlApp(api_key=api_key)
    return app.search(product_name, params={'limit': 3})