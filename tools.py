import os
from crewai.tools import tool
from rembg import remove
from PIL import Image
from firecrawl import FirecrawlApp


# ===============================
# 画像背景削除 + 白背景 + リサイズ
# ===============================
@tool("background_removal_and_resize")
def background_removal_and_resize(image_path: str):
    """
    画像を読み込み、背景を削除してECサイト向けに最適化（白背景・JPEG保存）します。
    戻り値は処理後画像パス
    """
    try:
        input_image = Image.open(image_path).convert("RGBA")

        # 背景削除
        output_image = remove(input_image).convert("RGBA")

        # 白背景作成
        background = Image.new("RGBA", output_image.size, (255, 255, 255, 255))

        # 合成
        combined = Image.alpha_composite(background, output_image).convert("RGB")

        # 保存
        output_path = f"processed_{os.path.basename(image_path)}"
        combined.save(output_path, "JPEG", quality=95)

        return output_path

    except Exception as e:
        return f"画像処理エラー: {str(e)}"


# ===============================
# Firecrawl 商品リサーチ
# ===============================
@tool("product_web_research")
def product_web_research(product_name: str):
    """
    Firecrawlを使用して商品の特性を調査します
    """
    try:
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return "Firecrawl APIキーが設定されていません"

        app = FirecrawlApp(api_key=api_key)

        result = app.search(
            product_name,
            params={'limit': 3}
        )

        return result

    except Exception as e:
        return f"WEB調査エラー: {str(e)}"