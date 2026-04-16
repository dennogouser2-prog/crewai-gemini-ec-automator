import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# システム設定の整合性維持
try:
    google_api_key = st.secrets["GOOGLE_API_KEY"]
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")

    # Gemini / LiteLLM 用（全部入れる）
    os.environ["GEMINI_API_KEY"] = google_api_key
    os.environ["GOOGLE_API_KEY"] = google_api_key
    os.environ["GOOGLE_GENERATIVEAI_API_KEY"] = google_api_key

    if firecrawl_api_key:
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

MODEL_NAME = "gemini/gemini-2.5-flash"

st.set_page_config(page_title="EC自動化エージェント", layout="wide")
st.title("🚀 EC商品登録：クリエイティブ・エージェント")

# --- UI設定 ---
with st.sidebar:
    st.header("⚙️ 出力設定")
    num_variants = st.number_input("各文字数の出力案数", min_value=1, max_value=5, value=1, key="v_cnt")
    st.subheader("パターンの文字数指定")
    l1 = st.number_input("パターン1", value=10, key="l1")
    l2 = st.number_input("パターン2", value=20, key="l2")
    l3 = st.number_input("パターン3", value=100, key="l3")
    l4 = st.number_input("パターン4", value=200, key="l4")
    st.divider()
    enable_text_overlay = st.checkbox("画像に商品名を印字する", value=False, key="ov_check")
    selected_color = st.color_picker("印字色", "#000000", key="ov_color")
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="web_check")

col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名", key="p_name")
    manual_features = st.text_area("補足情報", key="p_feat")
    image_input = st.file_uploader("画像（背景削除用）", type=["jpg", "png", "jpeg"], key="p_img")

if st.button("コピー生成開始", key="p_submit") and name_input:
    agent_tools = [product_web_research] if use_web_research else []
    native_llm = LLM(model=MODEL_NAME, api_key=google_api_key, temperature=1.0)

    with st.spinner("AIエージェントが作業中..."):
        try:
            # エージェントとタスク（中略：動作確認済みのロジックを維持）
            analyst = Agent(role='分析官', goal='特徴抽出', backstory='プロ', llm=native_llm, tools=agent_tools, max_iter=1)
            copywriter = Agent(role='ライター', goal='コピー作成', backstory='プロ', llm=native_llm, max_iter=1)
            t1 = Task(description=f"商品「{name_input}」を分析。{manual_features}", expected_output="レポート", agent=analyst)
            t2 = Task(description=f"{l1},{l2},{l3},{l4}文字以内で【{num_variants}案ずつ】作成せよ。", expected_output="コピー案", agent=copywriter, context=[t1])
            crew = Crew(agents=[analyst, copywriter], tasks=[t1, t2], process=Process.sequential)
            result = crew.kickoff()

            st.success("全ての案が生成されました！")
            with col2:
                st.subheader("生成結果")
                st.markdown(result.raw)
                
                if image_input:
                    # 一時保存
                    img_path = os.path.abspath(f"temp_{image_input.name}")
                    with open(img_path, "wb") as f:
                        f.write(image_input.getbuffer())
                    
                    # 【修正箇所】TypeErrorを回避するため.func(...) で直接呼び出し
                    text_to_draw = name_input if enable_text_overlay else ""
                    processed_path = background_removal_and_resize.func(
                        image_path=img_path, 
                        text=text_to_draw, 
                        text_color=selected_color
                    )
                    
                    # 画像を表示
                    if "ERROR" not in processed_path and os.path.exists(processed_path):
                        st.image(processed_path, caption="加工済み画像（背景削除・文字合成）")
                    else:
                        st.warning(f"画像処理エラー: {processed_path}")
        except Exception as e:
            st.error(f"実行エラー: {str(e)}")