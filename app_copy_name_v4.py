import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools4 import product_web_research, background_removal_and_resize

# --- 成功した環境変数セット方法を継承 ---
try:
    google_api_key = st.secrets["GOOGLE_API_KEY"]
    firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")

    # Gemini / LiteLLM 用（全部入れる）
    os.environ["GEMINI_API_KEY"] = google_api_key
    os.environ["GOOGLE_API_KEY"] = google_api_key
    os.environ["GOOGLE_GENERATIVEAI_API_KEY"] = google_api_key

    if firecrawl_api_key:
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key
except Exception as e:
    st.error(f"Secrets設定エラー: {str(e)}")
    st.stop()

MODEL_NAME = "gemini/gemini-2.5-flash"

st.set_page_config(page_title="EC自動化エージェント", layout="wide")
st.title("🚀 EC商品登録：クリエイティブ・エージェント")

# --- UI：サイドバー設定エリア ---
with st.sidebar:
    st.header("⚙️ 出力設定")
    num_variants = st.number_input("各文字数の出力案数", min_value=1, max_value=5, value=1, key="v_cfg")
    
    st.subheader("パターンの文字数指定")
    l1 = st.number_input("パターン1", value=10, key="l1_cfg")
    l2 = st.number_input("パターン2", value=20, key="l2_cfg")
    l3 = st.number_input("パターン3", value=100, key="l3_cfg")
    l4 = st.number_input("パターン4", value=200, key="l4_cfg")
    
    st.divider()
    # 【新機能】文字入れと色選択
    enable_text = st.checkbox("画像に商品名を印字する", value=False, key="ov_check")
    # カラーピッカーの追加
    selected_color = st.color_picker("印字する文字色", "#000000", key="ov_color")
    
    use_web = st.checkbox("WEB調査を実行する", value=False, key="web_check")

col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名", key="p_name_input")
    manual_feat = st.text_area("補足情報", key="p_feat_input")
    image_input = st.file_uploader("画像（背景削除用）", type=["jpg", "png", "jpeg"], key="p_img_input")

if st.button("コピー生成開始", key="p_submit_btn") and name_input:
    agent_tools = [product_web_research] if use_web else []
    native_llm = LLM(model=MODEL_NAME, api_key=google_api_key, temperature=1.0)

    with st.spinner("AIエージェントが連携して作業中..."):
        try:
            # エージェントとタスク（安定稼働中のロジック）
            analyst = Agent(role='分析官', goal='魅力分析', backstory='ECプロ', llm=native_llm, tools=agent_tools, max_iter=1)
            copywriter = Agent(role='ライター', goal='コピー作成', backstory='短文プロ', llm=native_llm, max_iter=1)
            t1 = Task(description=f"「{name_input}」を分析せよ。{manual_feat}", expected_output="レポート", agent=analyst)
            t2 = Task(description=f"{l1},{l2},{l3},{l4}文字以内で各{num_variants}案作成せよ。", expected_output="案", agent=copywriter, context=[t1])
            
            crew = Crew(agents=[analyst, copywriter], tasks=[t1, t2], process=Process.sequential)
            result = crew.kickoff()

            st.success("生成が完了しました！")
            with col2:
                st.subheader("生成結果")
                st.markdown(result.raw)
                
                if image_input:
                    img_path = os.path.abspath(f"temp_{image_input.name}")
                    with open(img_path, "wb") as f:
                        f.write(image_input.getbuffer())
                    
                    # カラーピッカーの値をツールに渡して実行
                    text_to_draw = name_input if enable_text else ""
                    processed_path = background_removal_and_resize.func(
                        image_path=img_path, 
                        text=text_to_draw, 
                        text_color=selected_color
                    )
                    
            # 画像処理後のセクションにクリーンアップを追加
            if "画像処理エラー" not in processed_path and os.path.exists(processed_path):
                st.image(processed_path, caption="加工済み画像（背景削除・文字合成）")
                # 処理が終わったら一時ファイルを削除してストレージを守る
                try:
                    os.remove(img_path)
                    os.remove(processed_path)
                except:
                    pass
        except Exception as e:
            st.error(f"実行エラー: {str(e)}")