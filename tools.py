import os
from crewai.tools import tool
from rembg import remove
from PIL import Image
from firecrawl import FirecrawlApp


@tool("background_removal_and_resize")
def background_removal_and_resize(image_path: str):
    """画像の背景削除して白背景JPEGにする"""
    try:
        input_image = Image.open(image_path).convert("RGBA")
        output_image = remove(input_image).convert("RGBA")

        background = Image.new("RGBA", output_image.size, (255, 255, 255, 255))
        combined = Image.alpha_composite(background, output_image).convert("RGB")

        output_path = f"processed_{os.path.basename(image_path)}"
        combined.save(output_path, "JPEG", quality=95)

        return output_path

    except Exception as e:
        return f"画像処理エラー: {str(e)}"


@tool("product_web_research")
def product_web_research(product_name: str):
    """Firecrawlで商品調査"""
    try:
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return "Firecrawl APIキー未設定"

        app = FirecrawlApp(api_key=api_key)
        result = app.search(product_name, params={'limit': 3})

        return result

    except Exception as e:
        return f"検索エラー: {str(e)}"