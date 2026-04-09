import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# =========================
# APIキー設定
# =========================
try:
    google_api_key = st.secrets["GOOGLE_API_KEY"]
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")

    # Gemini / LiteLLM 用（全部入れる）
    os.environ["GEMINI_API_KEY"] = google_api_key
    os.environ["GOOGLE_API_KEY"] = google_api_key
    os.environ["GOOGLE_GENERATIVEAI_API_KEY"] = google_api_key

    if firecrawl_api_key:
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

except Exception as e:
    st.error(f"Secrets設定エラー: {str(e)}")
    st.stop()


# =========================
# モデル
# =========================
MODEL_NAME = "gemini/gemini-2.5-flash"


# =========================
# UI
# =========================
st.set_page_config(page_title="EC自動化エージェント", layout="wide")
st.title("🚀 EC商品登録：CrewAI安定稼働環境")

col1, col2 = st.columns(2)

with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名")
    manual_features = st.text_area("補足情報（任意）")
    use_web_research = st.checkbox("WEB調査を実行する", value=False)
    image_input = st.file_uploader("画像", type=["jpg", "png", "jpeg"])


# =========================
# 実行
# =========================
if st.button("コピー生成開始") and name_input:

    agent_tools = [product_web_research] if use_web_research else []

    native_llm = LLM(
        model=MODEL_NAME,
        temperature=0.7
    )

    with st.spinner("AIエージェント実行中..."):
        try:
            analyst = Agent(
                role='商品分析',
                goal=f'商品「{name_input}」の魅力を分析',
                backstory='EC商品分析の専門家',
                llm=native_llm,
                tools=agent_tools,
                verbose=True
            )

            copywriter = Agent(
                role='コピーライター',
                goal='売れるコピー作成',
                backstory='ECコピー専門',
                llm=native_llm,
                verbose=True
            )

            task1 = Task(
                description=f"{name_input} を分析",
                expected_output="商品分析",
                agent=analyst
            )

            task2 = Task(
                description="EC用コピーを4つ作成",
                expected_output="コピー4案",
                agent=copywriter,
                context=[task1]
            )

            crew = Crew(
                agents=[analyst, copywriter],
                tasks=[task1, task2],
                process=Process.sequential
            )

            result = crew.kickoff()

            st.success("完了")
            with col2:
                st.markdown(result.raw)

        except Exception as e:
            st.error(f"実行中にエラーが発生しました: {str(e)}")