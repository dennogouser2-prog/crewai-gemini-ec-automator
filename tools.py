import os
from crewai.tools import tool
from rembg import remove
from PIL import Image
from firecrawl import FirecrawlApp

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
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return "Firecrawl APIキーが環境変数に見つかりません。"
    app = FirecrawlApp(api_key=api_key)
    return app.search(product_name, params={'limit': 3})