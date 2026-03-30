import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# =========================
# 環境変数設定（最重要）
# =========================
try:
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")

    if not google_api_key:
        st.error("🚨 Streamlit Secretsに GOOGLE_API_KEY が設定されていません。")
        st.stop()

    # 正しい書き方（←絶対これ）
    os.environ["GOOGLE_API_KEY"] = google_api_key

    if firecrawl_api_key:
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

except Exception:
    st.error("🚨 Secretsの設定を確認してください。")
    st.stop()


# =========================
# モデル設定
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
    name_input = st.text_input("商品名", key="key_input_name")
    manual_features = st.text_area("補足情報（任意）", key="key_input_feat")
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="key_input_web")
    image_input = st.file_uploader("画像（背景削除）", type=["jpg", "png", "jpeg"], key="key_input_img")


# =========================
# 実行処理
# =========================
if st.button("コピー生成開始", key="key_input_submit") and name_input:

    # ←ここも修正済み（空リストを必ず入れる）
    agent_tools = [product_web_research] if use_web_research else []

    native_llm = LLM(
        model=MODEL_NAME,
        api_key=google_api_key,
        temperature=1.0
    )

    with st.spinner("AIエージェントが連携して作業中..."):
        try:
            # -------------------------
            # エージェント
            # -------------------------
            analyst = Agent(
                role='商品特性アナリスト',
                goal=f'商品「{name_input}」の独自の魅力を特定する',
                backstory='20年のEC運用経験に基づき、商品名からインサイトを抽出する専門家。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )

            copywriter = Agent(
                role='戦略的コピーライター',
                goal='文字数制限内でクリック率を最大化するコピーを作る',
                backstory='SEOタイトルの配置技術（前半15文字に重要キーワード）のプロ。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            # -------------------------
            # タスク
            # -------------------------
            task1 = Task(
                description=f"商品「{name_input}」を分析せよ",
                expected_output="詳細レポート",
                agent=analyst
            )

            task2 = Task(
                description="指定文字数で4案のコピーを出せ",
                expected_output="4つのコピー案（箇条書き）",
                agent=copywriter,
                context=[task1]
            )

            # -------------------------
            # Crew実行
            # -------------------------
            crew = Crew(
                agents=[analyst, copywriter],
                tasks=[task1, task2],
                process=Process.sequential
            )

            result = crew.kickoff()

            # -------------------------
            # 結果表示
            # -------------------------
            st.success("生成が完了しました！")

            with col2:
                st.subheader("生成結果")
                st.markdown(result.raw)

                # -------------------------
                # 画像処理
                # -------------------------
                if image_input:
                    img_path = os.path.abspath(f"temp_{image_input.name}")

                    with open(img_path, "wb") as f:
                        f.write(image_input.getbuffer())

                    background_removal_and_resize.run(image_path=img_path)

                    processed_img = f"processed_{os.path.basename(img_path)}"

                    if os.path.exists(processed_img):
                        st.image(processed_img, caption="背景削除済み画像（白背景・中央配置）")

        except Exception as e:
            st.error(f"実行中にエラーが発生しました: {str(e)}")