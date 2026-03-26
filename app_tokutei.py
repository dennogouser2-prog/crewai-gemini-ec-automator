import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# --- [最重要] 環境変数の正しいセット方法 ---
# os.environ = "..." と書くとシステムが壊れます。必ず以下の形式で書いてください。
os.environ = "sk-dummy-key-for-internal-validation"

try:
    # Streamlit CloudのSecretsからAPIキーを取得
    api_key = st.secrets
except Exception:
    st.error("🚨 Streamlit CloudのSecretsに GOOGLE_API_KEY が設定されていません。")
    st.stop()

# 2026年3月現在の推奨モデル。プレフィックスに gemini/ を付与します [5, 2]
MODEL_NAME = "gemini/gemini-2.5-flash"

st.set_page_config(page_title="EC自動化ツール：社内公開版", layout="wide")
st.title("🚀 EC商品登録：CrewAI安定稼働エージェント")

col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    # key引数を付けて DuplicateElementId エラーを防止
    name_input = st.text_input("商品名", key="inp_name")
    manual_features = st.text_area("補足情報（任意）", key="inp_features")
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="inp_web")
    image_input = st.file_uploader("画像（背景削除用）", type=["jpg", "png", "jpeg"], key="inp_img")

if st.button("コピー生成開始", key="btn_submit") and name_input:
    agent_tools = [product_web_research] if use_web_research else []

    # CrewAI v1.x ネイティブLLMクラスの定義 [4]
    native_llm = LLM(
        model=MODEL_NAME,
        api_key=api_key,
        temperature=1.0 # Gemini 3系列の推奨値 
    )

    with st.spinner("AIエージェントが連携して作業中..."):
        try:
            # 1. 商品特性アナリスト
            analyst = Agent(
                role='商品特性アナリスト',
                goal=f'商品「{name_input}」の独自の魅力を特定する',
                backstory='20年のEC経験を持つ専門家。画像やテキストから瞬時にベネフィットを抽出します。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )

            # 2. 戦略的コピーライター
            copywriter = Agent(
                role='戦略的コピーライター',
                goal='10, 20, 30, 50文字の4パターンで、クリック率を最大化するコピーを作る',
                backstory='SEOタイトル（前半15文字に重要キーワード）の配置技術を熟知したプロ 。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(description=f"商品「{name_input}」の魅力を分析せよ", expected_output="詳細レポート", agent=analyst)
            task2 = Task(description="指定文字数で4つのコピー案を箇条書きで出せ", expected_output="4案のコピー案", agent=copywriter, context=[task1])

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
                        st.image(processed_img, caption="背景削除済み（白背景・中央配置）")
        except Exception as e:
            st.error(f"実行中にエラーが発生しました。時間を置いてお試しください。\\n詳細: {str(e)}")