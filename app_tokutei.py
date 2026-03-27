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
        st.error("🚨 Secretsに GOOGLE_API_KEY が設定されていません。")
        st.stop()

except Exception:
    st.error("🚨 Secretsの設定を確認してください。")
    st.stop()

# ===============================
# 環境変数にAPIキー設定（重要）
# ===============================
os.environ["GOOGLE_API_KEY"] = google_api_key
if firecrawl_api_key:
    os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

# 使用モデル
MODEL_NAME = "gemini/gemini-2.5-flash"

# ===============================
# Streamlit UI
# ===============================
st.set_page_config(page_title="EC自動化ツール", layout="wide")
st.title("🚀 EC商品登録：CrewAI安定稼働版")

col1, col2 = st.columns(2)

with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名", key="inp_p_name")
    manual_features = st.text_area("補足情報（任意）", key="inp_p_feat")
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="chk_p_web")
    image_input = st.file_uploader("画像（背景削除）", type=["jpg", "png", "jpeg"], key="upl_p_img")

# ===============================
# コピー生成ボタン
# ===============================
if st.button("コピー生成開始", key="btn_p_submit") and name_input:

    # ツールリスト
    agent_tools = [product_web_research] if use_web_research else []

    # CrewAI LLM
    native_llm = LLM(
        model=MODEL_NAME,
        temperature=0.7
    )

    with st.spinner("AIエージェントが作業中..."):
        try:
            # ===============================
            # Agent定義
            # ===============================
            analyst = Agent(
                role='商品特性アナリスト',
                goal=f'商品「{name_input}」の魅力を整理する',
                backstory='20年のEC運用経験を持つ専門家。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )

            copywriter = Agent(
                role='戦略的コピーライター',
                goal='クリック率を最大化するコピーを作る',
                backstory='SEOの30文字タイトルルールを熟知したプロ。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            # ===============================
            # Task定義
            # ===============================
            task1 = Task(
                description=f"商品「{name_input}」を分析し、特徴・ターゲット・訴求ポイントを整理せよ。補足情報：{manual_features}",
                expected_output="商品分析レポート",
                agent=analyst
            )

            task2 = Task(
                description="SEOを意識した30文字前後の商品タイトルを4案作成せよ。",
                expected_output="商品タイトル4案",
                agent=copywriter,
                context=[task1]
            )

            # ===============================
            # Crew実行
            # ===============================
            crew = Crew(
                agents=[analyst, copywriter],
                tasks=[task1, task2],
                process=Process.sequential
            )

            result = crew.kickoff()

            # ===============================
            # 結果表示
            # ===============================
            with col2:
                st.subheader("生成結果")
                st.markdown(result.raw)
                
                # ===============================
                # 画像処理
                # ===============================
                if image_input:
                    img_path = os.path.abspath(f"temp_{image_input.name}")
                    with open(img_path, "wb") as f:
                        f.write(image_input.getbuffer())

                    processed_img = background_removal_and_resize.run(image_path=img_path)

                    if processed_img and os.path.exists(processed_img):
                        st.image(processed_img, caption="背景削除済み画像")

        except Exception as e:
            st.error(f"実行エラー: {str(e)}")