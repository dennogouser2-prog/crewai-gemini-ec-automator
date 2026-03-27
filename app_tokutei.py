import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# ===============================
# SecretsからAPIキー取得
# ===============================
try:
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")

    if not google_api_key:
        st.error("🚨 GOOGLE_API_KEY が設定されていません")
        st.stop()

except Exception:
    st.error("🚨 secrets.toml を確認してください")
    st.stop()

# ===============================
# 環境変数設定（Geminiはこれ重要）
# ===============================
os.environ["GOOGLE_API_KEY"] = google_api_key
os.environ["GEMINI_API_KEY"] = google_api_key
os.environ["GOOGLE_GENERATIVEAI_API_KEY"] = google_api_key

if firecrawl_api_key:
    os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

# ===============================
# Geminiモデル
# ===============================
MODEL_NAME = "gemini/gemini-1.5-flash"

# ===============================
# Streamlit UI
# ===============================
st.set_page_config(page_title="EC自動化ツール", layout="wide")
st.title("🚀 EC商品登録：CrewAI自動化ツール")

col1, col2 = st.columns(2)

with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名")
    manual_features = st.text_area("補足情報")
    use_web_research = st.checkbox("WEB調査を実行する")
    image_input = st.file_uploader("画像", type=["jpg","png","jpeg"])

# ===============================
# 実行
# ===============================
if st.button("コピー生成開始") and name_input:

    agent_tools = [product_web_research] if use_web_research else []

# LLM
native_llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=google_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta",
    temperature=0.7
)

with st.spinner("AIが商品分析中..."):

        try:
            analyst = Agent(
                role='商品特性アナリスト',
                goal=f'商品「{name_input}」の魅力を分析する',
                backstory='ECマーケティング専門家',
                llm=native_llm,
                tools=agent_tools,
                verbose=True
            )

            copywriter = Agent(
                role='コピーライター',
                goal='売れる商品タイトルを作成する',
                backstory='SEOコピーライター',
                llm=native_llm,
                verbose=True
            )

            task1 = Task(
                description=f"商品「{name_input}」の特徴、ターゲット、メリットを分析せよ。補足情報：{manual_features}",
                agent=analyst
            )

            task2 = Task(
                description="SEOに強い商品タイトルを30文字前後で4つ作成せよ。",
                agent=copywriter,
                context=[task1]
            )

            crew = Crew(
                agents=[analyst, copywriter],
                tasks=[task1, task2],
                process=Process.sequential
            )

            result = crew.kickoff()

            with col2:
                st.subheader("生成結果")
                st.write(result.raw)

                # 画像処理
                if image_input:
                    img_path = os.path.abspath(f"temp_{image_input.name}")
                    with open(img_path, "wb") as f:
                        f.write(image_input.getbuffer())

                    processed_img = background_removal_and_resize.run(image_path=img_path)

                    if processed_img and os.path.exists(processed_img):
                        st.image(processed_img)

        except Exception as e:
            st.error(f"実行エラー: {str(e)}")