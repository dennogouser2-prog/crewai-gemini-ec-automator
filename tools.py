import os
from crewai.tools import tool
from rembg import remove
from PIL import Image
from firecrawl import FirecrawlApp


@tool("background_removal_and_resize")
def background_removal_and_resize(image_path: str) -> str:
    """
    画像の背景を削除し、白背景に合成してJPEGで保存するツール
    """
    try:
        input_image = Image.open(image_path).convert("RGBA")
        output_image = remove(input_image).convert("RGBA")

        background = Image.new("RGBA", output_image.size, (255, 255, 255))
        combined = Image.alpha_composite(background, output_image).convert("RGB")

        output_path = f"processed_{os.path.basename(image_path)}"
        combined.save(output_path, "JPEG")

        return f"画像処理完了: {output_path}"
    except Exception as e:
        return f"画像処理エラー: {str(e)}"


@tool("product_web_research")
def product_web_research(product_name: str) -> str:
    """
    Firecrawlを使用して商品の情報をWeb検索するツール
    """
    try:
        app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        result = app.search(product_name, params={'limit': 3})
        return str(result)
    except Exception as e:
        return f"Web検索エラー: {str(e)}"