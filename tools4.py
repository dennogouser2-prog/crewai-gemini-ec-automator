import os
from crewai.tools import tool
from rembg import remove
from PIL import Image, ImageDraw, ImageFont

@tool("background_removal_and_resize")
def background_removal_and_resize(image_path: str, text: str = "", text_color: str = "#000000"):
    """画像を背景削除し、指定された色で商品名を印字します。"""
    try:
        input_image = Image.open(image_path)
        # 背景削除
        output_image = remove(input_image)
        
        # 白背景と合成（JPEG保存用に透明度を排除）
        background = Image.new("RGBA", output_image.size, (255, 255, 255, 255))
        combined = Image.alpha_composite(background, output_image)
        
        if text:
            draw = ImageDraw.Draw(combined)
            # 日本語フォントの読み込み
            font_path = "NotoSansJP-Bold.ttf"
            if os.path.exists(font_path):
                font_size = int(combined.height * 0.07)
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()

            # --- 【新機能】16進数カラーをRGBに変換 ---
            color_hex = text_color.lstrip('#')
            rgb_color = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))

            # --- 【bbox修正】正確なインデックスで計算 ---
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0] # 右端 - 左端
            text_h = bbox[3] - bbox[1] # 下端 - 上端
            
            x = (combined.width - text_w) // 2
            y = combined.height - text_h - 60 # 下から60px
            
            # 指定された色で印字
            draw.text((x, y), text, font=font, fill=rgb_color)
        
        # RGBに変換して保存
        final_image = combined.convert("RGB")
        output_path = os.path.abspath(f"processed_{os.path.basename(image_path)}")
        final_image.save(output_path, "JPEG", quality=95)
        
        return output_path
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