import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools2 import product_web_research, background_removal_and_resize

# --- 【最重要修正】 道具箱を壊さず、適切にキーをセットします ---
try:
    google_api_key = st.secrets
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")

    # システムが要求する環境変数をすべて網羅（辞書を壊さない [" "] 形式）
    os.environ = google_api_key
    os.environ = google_api_key
    os.environ = google_api_key
    os.environ = "NA" # バリデーション回避用のダミー

    if firecrawl_api_key:
        os.environ = firecrawl_api_key

except Exception as e:
    st.error(f"Secrets設定エラー: {str(e)}")
    st.stop()

# 2026年3月現在の最新安定モデル
MODEL_NAME = "gemini/gemini-2.5-flash"

st.set_page_config(page_title="EC自動化エージェント：最終版", layout="wide")
st.title("🚀 EC商品登録：クリエイティブ・エージェント")

# --- UI：設定エリア (サイドバー) ---
with st.sidebar:
    st.header("⚙️ 出力設定")
    num_variants = st.number_input("各文字数の出力案数", min_value=1, max_value=5, value=3, key="cfg_v")
    
    st.subheader("パターンの文字数指定")
    l1 = st.number_input("パターン1", value=10, key="cfg_l1")
    l2 = st.number_input("パターン2", value=20, key="cfg_l2")
    l3 = st.number_input("パターン3", value=30, key="cfg_l3")
    l4 = st.number_input("パターン4", value=40, key="cfg_l4")
    
    st.divider()
    enable_text_overlay = st.checkbox("画像に商品名を印字する", value=False, key="cfg_text")
    selected_color = st.color_picker("印字する文字色", "#000000", key="cfg_color")
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="cfg_web")

# --- UI：メイン入力エリア ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名", key="f_p_name")
    manual_features = st.text_area("補足情報（色・サイズ等）", key="f_p_feat")
    image_input = st.file_uploader("画像（背景削除用）", type=["jpg", "png", "jpeg"], key="f_p_img")

if st.button("コピー生成開始", key="f_p_submit") and name_input:
    agent_tools = [product_web_research] if use_web_research else []

    native_llm = LLM(model=MODEL_NAME, api_key=google_api_key, temperature=1.0)

    with st.spinner("AIエージェントが複数の案を考案中..."):
        try:
            analyst = Agent(
                role='商品分析官',
                goal=f'商品「{name_input}」の魅力を最大化する',
                backstory='20年のEC経験を持つ専門家。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )
            copywriter = Agent(
                role='戦略的ライター',
                goal='刺さるコピー案の作成',
                backstory='売上を伸ばす短文のプロ。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(description=f"商品「{name_input}」を分析せよ。補足：{manual_features}", expected_output="詳細分析", agent=analyst)
            task2 = Task(
                description=f"""分析結果を元に、以下につき【{num_variants}案ずつ】作成。
                1. {l1}文字以内、2. {l2}文字以内、3. {l3}文字以内、4. {l4}文字以内
                番号付き箇条書きで出力。要約ではなく、心に刺さる言葉を。""",
                expected_output="複数のコピー案",
                agent=copywriter,
                context=[task1]
            )

            crew = Crew(agents=[analyst, copywriter], tasks=[task1, task2], process=Process.sequential)
            result = crew.kickoff()

            st.success("全ての案が生成されました！")
            with col2:
                st.subheader("生成結果")
                st.markdown(result.raw)
                
                if image_input:
                    img_path = os.path.abspath(f"temp_{image_input.name}")
                    with open(img_path, "wb") as f:
                        f.write(image_input.getbuffer())
                    
                    # 【修正箇所】TypeErrorを解消するため辞書形式でツールを実行
                    text_to_draw = name_input if enable_text_overlay else ""
                    background_removal_and_resize.run({
                        "image_path": img_path, 
                        "text": text_to_draw, 
                        "text_color": selected_color
                    })
                    
                    processed_img = f"processed_{os.path.basename(img_path)}"
                    if os.path.exists(processed_img):
                        st.image(processed_img, caption="加工済み画像")
        except Exception as e:
            st.error(f"実行エラー: {str(e)}")