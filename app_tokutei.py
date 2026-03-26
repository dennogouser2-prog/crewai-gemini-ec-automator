import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# --- ネイティブ・プロバイダーのインポート・エラー対策 ---
# CrewAI内部のバリデーターをパスさせるため、ダミーのキーをセットします
os.environ = "sk-dummy-key-for-validation"

try:
    api_key = st.secrets
except Exception:
    st.error("🚨 Streamlit CloudのSecretsに GOOGLE_API_KEY が設定されていません。")
    st.stop()

# 2026年3月現在の最新安定モデル。プレフィックスを google_genai/ に変更します
MODEL_NAME = "google_genai/gemini-2.5-flash" 

st.set_page_config(page_title="EC自動化：最終修正版", layout="wide")
st.title("🚀 EC商品登録：CrewAIネイティブ環境")

col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名")
    manual_features = st.text_area("補足情報")
    use_web_research = st.checkbox("WEB調査を実行する", value=False)
    image_input = st.file_uploader("画像", type=["jpg", "png", "jpeg"])

if st.button("コピー生成開始") and name_input:
    agent_tools = [product_web_research] if use_web_research else []

    # LLMインスタンスの定義
    native_llm = LLM(
        model=MODEL_NAME,
        api_key=api_key,
        temperature=1.0 # Gemini 3以降の最適値
    )

    with st.spinner(f"AIエージェントが連携して動作中..."):
        try:
            analyst = Agent(
                role='商品スペシャリスト',
                goal=f'商品「{name_input}」の独自の魅力を特定する',
                backstory='20年のEC運用経験を持つ専門家。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )

            copywriter = Agent(
                role='戦略的ライター',
                goal='10, 20, 30, 50文字の4パターンでコピー案を出す',
                backstory='SEOタイトル（前半15文字に重要キーワード）の達人 [1]。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(description=f"商品「{name_input}」を分析せよ", expected_output="分析レポート", agent=analyst)
            task2 = Task(description="10/20/30/50文字のコピーを作成せよ", expected_output="4案のコピー", agent=copywriter, context=[task1])

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
                        st.image(processed_img, caption="背景削除・リサイズ済み")
        except Exception as e:
            st.error(f"実行エラー: {str(e)}")