import os
from crewai.tools import tool
from rembg import remove
from PIL import Image
from firecrawl import FirecrawlApp

#add
from crewai.tools import tool
from rembg import remove
from PIL import Image, ImageDraw, ImageFont

@tool("background_removal_and_resize")
def background_removal_and_resize(image_path: str, product_name: str = "", text_color: str = "#000000"):
    """画像を背景削除し、指定された色で商品名を中央下部に書き込みます。"""
    try:
        input_image = Image.open(image_path)
        output_image = remove(input_image)
        
        # 白背景と合成
        background = Image.new("RGBA", output_image.size, (255, 255, 255))
        combined = Image.alpha_composite(background, output_image).convert("RGB")
        
        # --- 文字入れ処理 ---
        if product_name:
            draw = ImageDraw.Draw(combined)
            # フォントの読み込み（リポジトリに配置したファイル名を指定）
            font_path = "NotoSansJP-Bold.ttf" 
            if os.path.exists(font_path):
                font_size = int(combined.height * 0.08) # 画像の高さの8%
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()

            # テキストの位置計算（中央下部）
            bbox = draw.textbbox((0, 0), product_name, font=font)
            text_w, text_h = bbox[1] - bbox, bbox[2] - bbox[3]
            x = (combined.width - text_w) // 2
            y = combined.height - text_h - 40 # 下から40px余白
            
            # 色の指定 (HexからRGBへ変換)
            rgb_color = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            draw.text((x, y), product_name, font=font, fill=rgb_color)
            
        output_path = f"processed_{os.path.basename(image_path)}"
        combined.save(output_path, "JPEG")
        return f"画像処理完了"
    except Exception as e:
        return f"画像処理エラー: {str(e)}"
#end   

@tool("background_removal_and_resize")
def background_removal_and_resize(image_path: str):
    """画像を読み込み、背景を削除してECサイト向けに最適化（白背景・リサイズ）します。"""
    try:
        input_image = Image.open(image_path)
        output_image = remove(input_image)
        background = Image.new("RGBA", output_image.size, (255, 255, 255))
        combined = Image.alpha_composite(background, output_image).convert("RGB")
        output_path = f"processed_{os.path.basename(image_path)}"
        combined.save(output_path, "JPEG")
        return f"画像処理完了: {output_path}"
    except Exception as e:
        return f"画像処理エラー: {str(e)}"

@tool("product_web_research")
def product_web_research(product_name: str):
    """Firecrawlを使用して商品の特性を調査します。"""
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        return "Firecrawl APIキーが環境変数に見つかりません。"
    app = FirecrawlApp(api_key=api_key)
    return app.search(product_name, params={'limit': 3})