import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# --- 環境変数の設定 (AttributeError対策) ---
# CrewAI内部のバリデーターをパスさせるためのダミーキー。辞書形式で正しくセットします。
os.environ = "sk-dummy-key-for-validation"

try:
    # Streamlit CloudのSecretsから取得 [3]
    api_key = st.secrets
except Exception:
    st.error("🚨 Streamlit CloudのSecrets設定で GOOGLE_API_KEY が不足しています。")
    st.stop()

# 2026年3月時点の推奨モデル
MODEL_NAME = "google_genai/gemini-2.5-flash"

st.set_page_config(page_title="EC自動化エージェント：安定版", layout="wide")
st.title("🚀 EC商品登録：CrewAI安定稼働環境")

col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    # --- key引数を追加してDuplicateElementIdエラーを防止 ---
    name_input = st.text_input("商品名", key="widget_product_name")
    manual_features = st.text_area("補足情報（任意）", key="widget_features")
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="widget_use_web")
    image_input = st.file_uploader("画像（背景削除用）", type=["jpg", "png", "jpeg"], key="widget_uploader")

if st.button("コピー生成開始", key="widget_submit_btn") and name_input:
    # ツールリストの安全な作成
    agent_tools = [product_web_research] if use_web_research else []

    # CrewAIネイティブのLLM定義 (ValidationError対策)
    native_llm = LLM(
        model=MODEL_NAME,
        api_key=api_key,
        temperature=1.0
    )

    with st.spinner("AIエージェントが連携して動作中..."):
        try:
            # 1. 商品特性を整理するエージェント
            analyst = Agent(
                role='商品特性アナリスト',
                goal=f'商品「{name_input}」の独自の魅力を特定する',
                backstory='20年のEC運用経験に基づき、商品名からインサイトを抽出する専門家。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )

            # 2. 戦略的コピーライター
            copywriter = Agent(
                role='戦略的コピーライター',
                goal='10, 20, 30, 50文字の4パターンで、クリック率を最大化するコピーを作る',
                backstory='SEOタイトル（前半15文字に重要キーワード）の配置技術を熟知したプロ [4]。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(description=f"商品「{name_input}」を分析せよ", expected_output="分析レポート", agent=analyst)
            task2 = Task(description="指定文字数で4つのコピー案を出せ", expected_output="4案のコピー案を箇条書きで", agent=copywriter, context=[task1])

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
            st.error(f"実行中にエラーが発生しました。時間を置いてお試しください。\\n詳細: {str(e)}")