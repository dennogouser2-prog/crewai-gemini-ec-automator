import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# =========================
# APIキー設定
# =========================
try:
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")

    if not google_api_key:
        st.error("🚨 Streamlit Secretsに GOOGLE_API_KEY が設定されていません。")
        st.stop()

    # ★ここが最重要
    os.environ["GEMINI_API_KEY"] = google_api_key

    if firecrawl_api_key:
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

except Exception:
    st.error("🚨 Secretsの設定を確認してください。")
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
    image_input = st.file_uploader("画像（背景削除）", type=["jpg", "png", "jpeg"])


# =========================
# 実行
# =========================
if st.button("コピー生成開始") and name_input:

    agent_tools = [product_web_research] if use_web_research else []

    native_llm = LLM(
        model=MODEL_NAME,
        temperature=1.0
    )

    with st.spinner("AIエージェントが連携して作業中..."):
        try:
            analyst = Agent(
                role='商品特性アナリスト',
                goal=f'商品「{name_input}」の独自の魅力を特定する',
                backstory='EC分析の専門家',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )

            copywriter = Agent(
                role='戦略的コピーライター',
                goal='売れるコピーを作る',
                backstory='ECコピーライター',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(
                description=f"商品「{name_input}」を分析せよ",
                expected_output="詳細レポート",
                agent=analyst
            )

            task2 = Task(
                description="ECサイト用のコピーを4案作成",
                expected_output="4つのコピー案",
                agent=copywriter,
                context=[task1]
            )

            crew = Crew(
                agents=[analyst, copywriter],
                tasks=[task1, task2],
                process=Process.sequential
            )

            result = crew.kickoff()

            st.success("生成が完了しました！")

            with col2:
                st.subheader("生成結果")
                st.markdown(result.raw)

        except Exception as e:
            st.error(f"実行中にエラーが発生しました: {str(e)}")