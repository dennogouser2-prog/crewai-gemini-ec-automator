import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# ===============================
# Secrets取得
# ===============================
google_api_key = st.secrets.get("GOOGLE_API_KEY")
firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")

if not google_api_key:
    st.error("GOOGLE_API_KEY が設定されていません")
    st.stop()

# ===============================
# 環境変数設定
# ===============================
os.environ["GEMINI_API_KEY"] = google_api_key
os.environ["GOOGLE_API_KEY"] = google_api_key
os.environ["GOOGLE_GENERATIVEAI_API_KEY"] = google_api_key

if firecrawl_api_key:
    os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

# ===============================
# LLM（LiteLLM経由 Gemini）
# ===============================
native_llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=google_api_key,
    temperature=0.7
)

# ===============================
# Streamlit UI
# ===============================
st.set_page_config(page_title="EC自動化ツール", layout="wide")
st.title("EC商品登録 自動生成AI")

col1, col2 = st.columns(2)

with col1:
    name_input = st.text_input("商品名")
    manual_features = st.text_area("補足情報")
    use_web_research = st.checkbox("WEB調査する")
    image_input = st.file_uploader("商品画像", type=["jpg", "png", "jpeg"])

# ===============================
# 実行
# ===============================
if st.button("コピー生成") and name_input:

    agent_tools = [product_web_research] if use_web_research else []

    try:
        analyst = Agent(
            role="商品分析担当",
            goal="商品の特徴とターゲットを分析する",
            backstory="ECマーケティング専門家",
            llm=native_llm,
            tools=agent_tools
        )

        copywriter = Agent(
            role="コピーライター",
            goal="売れる商品タイトルを作る",
            backstory="SEOコピーライター",
            llm=native_llm
        )

        task1 = Task(
            description=f"{name_input} の商品分析を行う。補足情報: {manual_features}",
            agent=analyst
        )

        task2 = Task(
            description="SEOに強い商品タイトルを30文字前後で4つ作成",
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

            if image_input:
                img_path = f"temp_{image_input.name}"
                with open(img_path, "wb") as f:
                    f.write(image_input.getbuffer())

                processed_img = background_removal_and_resize.run(image_path=img_path)

                if processed_img and os.path.exists(processed_img):
                    st.image(processed_img)

    except Exception as e:
        st.error(str(e))