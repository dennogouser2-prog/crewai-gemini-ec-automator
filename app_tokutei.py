import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# --- [最重要] AttributeErrorを解消する唯一の正しい書き方 ---
# os.environ全体を書き換えらえず、特定のキーにのみ値を代入します
os.environ = "NA"

try:
    # Streamlit CloudのSecretsからAPIキーを取得
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")
    
    if not google_api_key:
        st.error("🚨 Secretsに GOOGLE_API_KEY が設定されていません。")
        st.stop()
    
    # Firecrawlのキーを環境変数にセット
    if firecrawl_api_key:
        os.environ = firecrawl_api_key
        
except Exception:
    st.error("🚨 Streamlit Secretsの設定を確認してください。")
    st.stop()

# 2026年現在の推奨モデル
MODEL_NAME = "gemini/gemini-2.5-flash"

st.set_page_config(page_title="EC自動化エージェント", layout="wide")
st.title("🚀 EC商品登録：CrewAI安定稼働環境")

col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名", key="f_p_name")
    manual_features = st.text_area("補足情報（任意）", key="f_p_feat")
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="f_p_web")
    image_input = st.file_uploader("画像（背景削除）", type=["jpg", "png", "jpeg"], key="f_p_img")

if st.button("コピー生成開始", key="f_p_submit") and name_input:
    # ツールリストの安全な作成
    agent_tools = [product_web_research] if use_web_research else [""]

    # CrewAI v1.x ネイティブLLMクラスの定義
    native_llm = LLM(
        model=MODEL_NAME,
        api_key=google_api_key,
        temperature=1.0
    )

    with st.spinner("AIエージェントが連携して作業中..."):
        try:
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
                goal='10, 20, 30, 50文字の4パターンで、クリック率を最大化するコピーを作る',
                backstory='SEOタイトルの配置技術（前半15文字に重要キーワード）を熟知したプロ [1]。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(description=f"商品「{name_input}」を分析せよ", expected_output="詳細レポート", agent=analyst)
            task2 = Task(description="指定文字数で4案のコピーを出せ", expected_output="4案のコピー（箇条書き）", agent=copywriter, context=[task1])

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
            st.error(f"実行中にエラーが発生しました: {str(e)}")