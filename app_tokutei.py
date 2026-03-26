import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM # LLMを追加
from tools import product_web_research, background_removal_and_resize

# --- Streamlit Cloud設定：SecretsからAPIキーを取得 ---
# 管理画面の「Advanced Settings > Secrets」にキーが設定されている必要があります 
try:
    api_key = st.secrets
except Exception:
    st.error("🚨 Streamlit CloudのSecretsに GOOGLE_API_KEY が設定されていません。")
    st.stop()

# 2026年3月現在の最新安定モデル 
MODEL_NAME = "gemini/gemini-2.5-flash" 

st.set_page_config(page_title="EC自動化：完全修正版", layout="wide")
st.title("🚀 EC商品登録：CrewAIネイティブ・エージェント")

# --- UI：入力フォーム ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名（例：バルミューダ ザ・トースター）")
    manual_features = st.text_area("補足情報（任意）")
    use_web_research = st.checkbox("WEB調査を実行する", value=False)
    image_input = st.file_uploader("画像（背景削除用）", type=["jpg", "png", "jpeg"])

# --- 生成開始プロセス ---
if st.button("コピー生成開始") and name_input:
    # ツールリストの安全な作成
    agent_tools = [product_web_research] if use_web_research else []

    # 【重要】CrewAI専用のLLMインスタンスを作成。これがValidationErrorの特効薬です 
    native_llm = LLM(
        model=MODEL_NAME,
        api_key=api_key,
        temperature=1.0 # Gemini 3以降の推奨値 
    )

    with st.spinner(f"AIエージェントが作業中..."):
        try:
            # 1. 商品特性を整理するエージェント
            analyst = Agent(
                role='商品スペシャリスト',
                goal=f'商品「{name_input}」の魅力を整理する',
                backstory='20年のEC運用経験を持つプロフェッショナル。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1, # 429エラー防止のため最小回数に制限 [6, 7]
                verbose=True
            )

            # 2. セールスコピーライター
            copywriter = Agent(
                role='戦略的ライター',
                goal='指定文字数でCVRを最大化するコピーを作る',
                backstory='SEOタイトル（30文字前後）を熟知したプロ 。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(description=f"商品「{name_input}」の魅力を分析せよ", expected_output="詳細レポート", agent=analyst)
            task2 = Task(description="10, 20, 30, 50文字のコピーを作成せよ", expected_output="4案のコピー", agent=copywriter, context=[task1])

            crew = Crew(agents=[analyst, copywriter], tasks=[task1, task2], process=Process.sequential)
            result = crew.kickoff()

            st.success("生成が完了しました！")
            with col2:
                st.subheader("生成結果")
                st.markdown(result.raw)
                
                if image_input:
                    # 画像処理の実行
                    img_path = os.path.abspath(f"temp_{image_input.name}")
                    with open(img_path, "wb") as f:
                        f.write(image_input.getbuffer())
                    background_removal_and_resize.run(image_path=img_path)
                    
                    processed_img = f"processed_{os.path.basename(img_path)}"
                    if os.path.exists(processed_img):
                        st.image(processed_img, caption="加工済み画像")

        except Exception as e:
            st.error(f"実行エラーが発生しました。詳細はログを確認してください。\\n詳細: {str(e)}")