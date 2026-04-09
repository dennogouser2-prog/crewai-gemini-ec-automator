import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# --- [最重要] AttributeError対策 ---
# 道具箱(os.environ)を壊さず、中にダミーキーを1つ入れる正しい記法です
#os.environ = "NA"

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


# 2026年3月現在の最新安定モデル
MODEL_NAME = "gemini/gemini-2.5-flash"

st.set_page_config(page_title="EC自動化：プロ仕様版", layout="wide")
st.title("🚀 EC商品登録：文字数・案数カスタムエージェント")

# --- UI：設定エリア (サイドバー) ---
with st.sidebar:
    st.header("⚙️ 出力設定")
    num_variants = st.number_input("各文字数の出力案数", min_value=1, max_value=5, value=3, key="cfg_num_v")
    
    st.subheader("パターンの文字数指定")
    l1 = st.number_input("パターン1", value=10, key="cfg_l1")
    l2 = st.number_input("パターン2", value=20, key="cfg_l2")
    l3 = st.number_input("パターン3", value=30, key="cfg_l3")
    l4 = st.number_input("パターン4", value=40, key="cfg_l4")
    
    st.divider()
    use_web_research = st.checkbox("WEB調査を実行する", value=False, key="cfg_web")

# --- UI：メイン入力エリア ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名", key="f_prod_name")
    manual_features = st.text_area("補足情報（色・サイズ等）", key="f_prod_feat")
    image_input = st.file_uploader("画像（背景削除用）", type=["jpg", "png", "jpeg"], key="f_prod_img")

if st.button("コピー生成開始", key="f_btn_submit") and name_input:
    agent_tools = [product_web_research] if use_web_research else []

    native_llm = LLM(
        model=MODEL_NAME,
        api_key=google_api_key,
        temperature=1.0
    )

    with st.spinner("AIエージェントが複数の案を考案中..."):
        try:
            # 1. 商品特性アナリスト
            analyst = Agent(
                role='商品特性アナリスト',
                goal=f'商品「{name_input}」から、訴求力の高い特徴を抽出する',
                backstory='20年のEC経験に基づき、商品名からインサイトを抽出する専門家。',
                llm=native_llm,
                tools=agent_tools,
                max_iter=1,
                verbose=True
            )

            # 2. 戦略的コピーライター
            copywriter = Agent(
                role='戦略的コピーライター',
                goal=f'文字数制限を厳守し、{num_variants}案ずつのバリエーションを作成する',
                backstory='SEOとユーザー心理を熟知し、ABテストに耐えうる多様なコピー案を生み出すプロ。',
                llm=native_llm,
                max_iter=1,
                verbose=True
            )

            task1 = Task(
                description=f"商品「{name_input}」を分析せよ。補足：{manual_features}",
                expected_output="商品のベネフィットをまとめたレポート",
                agent=analyst
            )
            
            # 文字数と案数を動的に指示に組み込む
            task2 = Task(
                description=f"""分析結果を元に、以下の各文字数につき【{num_variants}案ずつ】コピーを作成してください。
                1. {l1}文字以内
                2. {l2}文字以内
                3. {l3}文字以内
                4. {l4}文字以内
                各案は比較しやすいように番号付きの箇条書きで出力してください。""",
                expected_output=f"各文字数制限を守った、計{num_variants * 4}個のコピー案",
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
                    background_removal_and_resize.run(image_path=img_path)
                    processed_img = f"processed_{os.path.basename(img_path)}"
                    if os.path.exists(processed_img):
                        st.image(processed_img, caption="背景削除・リサイズ済み画像")
        except Exception as e:
            st.error(f"実行中にエラーが発生しました: {str(e)}")