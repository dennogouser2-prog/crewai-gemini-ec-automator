import streamlit as st
import os
import time
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import product_web_research, background_removal_and_resize

load_dotenv()

st.set_page_config(page_title="AI EC商品登録エージェント", layout="wide")
st.title("🚀 AI EC商品登録エージェント")

# --- APIキーのチェック ---
api_key = os.getenv("GOOGLE_API_KEY")

# --- LLMの設定 ---
# 最新かつ安定している gemini-2.0-flash を使用します
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    api_key=api_key
)

# --- エージェント定義 (max_rpmを低く設定) ---
# CrewAI内部での連続呼び出しを防ぐため、1分あたりのリクエスト数を「2」に制限します
analyst = Agent(
    role='商品特性アナリスト',
    goal='商品の独自の強みと差別化ポイントを特定する',
    backstory='20年のEC経験を持つエキスパート。',
    llm=llm,
    multimodal=True,
    tools=[product_web_research],
    max_rpm=2, 
    verbose=True
)

copywriter = Agent(
    role='戦略的コピーライター',
    goal='指定文字数で購買意欲をそそるコピーを作成する',
    backstory='売上を最大化するコピーの天才。',
    llm=llm,
    max_rpm=2,
    verbose=True
)

# --- Streamlit UI ---
col1, col2 = st.columns(2)
with col1:
    name_input = st.text_input("商品名を入力してください")
    image_input = st.file_uploader("商品画像をアップロードしてください", type=["jpg", "png", "jpeg"])

if st.button("生成開始") and name_input and image_input:
    img_path = os.path.abspath(f"temp_{image_input.name}")
    with open(img_path, "wb") as f:
        f.write(image_input.getbuffer())

    with st.spinner("API制限を回避するため、リクエスト速度を調整しながら実行中..."):
        # APIクォータを安定させるため、開始前に少し待機
        time.sleep(5) 

        task1 = Task(
            description=f"1. {img_path} の画像を解析してください。\\n2. '{name_input}' をWEB調査してください。",
            expected_output="分析レポート",
            agent=analyst
        )

        task2 = Task(
            description="10, 20, 30, 50文字のコピーを作成してください。",
            expected_output="4パターンのコピー案",
            agent=copywriter,
            context=[task1]
        )

        # Crew全体でもリクエスト頻度を制御
        crew = Crew(
            agents=[analyst, copywriter], 
            tasks=[task1, task2], 
            process=Process.sequential,
            max_rpm=2 
        )
        
        try:
            result = crew.kickoff()
            edit_status = background_removal_and_resize.run(image_path=img_path)
            
            st.success("全ての処理が完了しました！")
            with col2:
                st.subheader("生成結果")
                st.write(result.raw)
                processed_img = f"processed_{os.path.basename(img_path)}"
                if os.path.exists(processed_img):
                    st.image(processed_img, caption="加工済み画像")
        except Exception as e:
            if "429" in str(e):
                st.error("🚨 Gemini APIの無料枠制限に達しました。1分ほど待ってから再度「生成開始」を押してください。")
            else:
                st.error(f"エラーが発生しました: {str(e)}")