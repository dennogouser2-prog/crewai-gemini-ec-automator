import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# --- [最重要] AttributeErrorを解消する環境変数の正しいセット方法 ---
# os.environ自体を文字列にせず、特定のキーのみに代入してシステムを壊さないようにします
os.environ = "NA"

try:
    # Streamlit CloudのSecretsからAPIキーを取得
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")
    
    if not google_api_key:
        st.error("🚨 Streamlit Secretsに GOOGLE_API_KEY が設定されていません。")
        st.stop()
except Exception:
    st.error("🚨 Streamlit Secrets（TOML形式）の設定を確認してください。")
    st.stop()

# 2026年3月現在の推奨モデル
MODEL_NAME = "gemini/gemini-2.5-flash"

st.set_page_config(page_title="EC自動化エージェント", layout="wide")
st.title("🚀 EC商品登録：CrewAI安定稼働版")

col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    # key引数を付けて DuplicateElementId エラーを防止
    name_input = st.text_input("商品名", key="f_input_name")
    manual_features = st.text_area("補足情報（任意）", key="f_input_feat")
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="f_check_web")
    image_input = st.file_uploader("画像（背景削除）", type=["jpg", "png", "jpeg"], key="f_uploader_img")

if st.button("コピー生成開始", key="f_btn_submit") and name_input:
    # --- [修正箇所] else の後に空のリスト を記述します ---
    agent_tools = [product_web_research] if use_web_research else []

    # CrewAI v1.x ネイティブLLMクラスの定義
    native_llm = LLM(
        model=MODEL_NAME,
        api_key=google_api_key,
        temperature=1.0
    )

    with st.spinner("AIエージェントが連携して作業中..."):
        try:
            # 1. 商品特性アナリスト
            analyst = Agent(
                role='商品特性アナリスト',
                goal=f'商品「{name_input}」の魅力を整理する',
                backstory='20年のEC運用経験を持つ専門家。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )

            # 2. 戦略的コピーライター
            copywriter = Agent(
                role='戦略的コピーライター',
                goal='文字数制限内でクリック率を最大化するコピーを作る',
                backstory='SEOタイトル配置技術（前半15文字に重要キーワード）のプロ。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(description=f"商品「{name_input}」を分析せよ", expected_output="詳細レポート", agent=analyst)
            task2 = Task(description="指定文字数で4案のコピーを出せ", expected_output="4つのコピー案（箇条書き）", agent=copywriter, context=[task1])

            crew = Crew(agents=[analyst, copywriter], tasks=[task1, task2], process=Process.sequential)
            result = crew.kickoff()

            st.success("生成が完了しました！")
            with col2:
                st.subheader("生成結果")
                st.markdown(result.raw)
                
                if image_input:
                    img_path = os.path.abspath(f"temp_{image_input.name}")
                    with open(img_path, "wb") as f:
                        f.write(image_input.getbuffer())
                    background_removal_and_resize.run(image_path=img_path)
                    processed_img = f"processed_{os.path.basename(img_path)}"
                    if os.path.exists(processed_img):
                        st.image(processed_img, caption="背景削除済み画像")
        except Exception as e:
            st.error(f"実行中にエラーが発生しました。時間を置いてお試しください。\\n詳細: {str(e)}")