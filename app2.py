import streamlit as st
import os
import time
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import product_web_research, background_removal_and_resize

load_dotenv()

st.set_page_config(page_title="EC自動化ツール (シンプル版)", layout="wide")
st.title("🚀 AI EC商品登録エージェント (負荷軽減モード)")

api_key = os.getenv("GOOGLE_API_KEY")

# --- LLMの設定 ---
# 2.0-flashでエラーが出る場合は、下の行を "gemini-1.5-flash" に書き換えて試してください
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    api_key=api_key
)

# --- エージェント定義 (負荷を最小化) ---
analyst = Agent(
    role='商品リサーチャー',
    goal='商品名から市場の魅力を1つ特定する',
    backstory='効率重視のリサーチャー。最小限の情報で最大の価値を見つけます。',
    llm=llm,
    multimodal=False, # 画像解析を無効化して負荷を軽減
    tools=[product_web_research],
    max_rpm=1,      # 1分間に1回のリクエストに制限
    max_iter=1,     # エージェントの自問自答（ループ）を1回に制限 
    verbose=True
)

copywriter = Agent(
    role='戦略的ライター',
    goal='10/20/30/50文字のコピーを作成する',
    backstory='短文作成のスペシャリスト。',
    llm=llm,
    max_rpm=1,
    max_iter=1,
    verbose=True
)

# --- Streamlit UI ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("入力データ")
    name_input = st.text_input("商品名のみ入力してください (例: カレーパン)")
    image_input = st.file_uploader("画像 (背景削除用としてのみ使用されます)", type=["jpg", "png", "jpeg"])

if st.button("生成開始") and name_input:
    with st.spinner("AIが最小負荷で実行中です..."):
        # Task 1: テキストのみの調査
        task1 = Task(
            description=f"商品名 '{name_input}' について、WEBで最新のセールスポイントを1つだけ調査してください。",
            expected_output="商品の主要な特徴1点",
            agent=analyst
        )

        # Task 2: コピー生成
        task2 = Task(
            description="調査結果を元に、10, 20, 30, 50文字のコピーを日本語で作成してください。",
            expected_output="4パターンのコピー案",
            agent=copywriter,
            context=[task1]
        )

        crew = Crew(
            agents=[analyst, copywriter], 
            tasks=[task1, task2], 
            process=Process.sequential
        )
        
        try:
            # 1. テキスト生成を実行
            result = crew.kickoff()
            
            # 2. 画像処理（ローカルCPU実行なのでGeminiの制限に関係なく動作します）
            edit_status = "画像なし"
            if image_input:
                img_path = os.path.abspath(f"temp_{image_input.name}")
                with open(img_path, "wb") as f:
                    f.write(image_input.getbuffer())
                edit_status = background_removal_and_resize.run(image_path=img_path)
            
            st.success("処理が完了しました！")
            with col2:
                st.subheader("生成結果")
                st.write(result.raw)
                st.subheader("画像処理")
                st.info(edit_status)
                if image_input:
                    processed_img = f"processed_{os.path.basename(img_path)}"
                    if os.path.exists(processed_img):
                        st.image(processed_img, caption="白背景加工済み")

        except Exception as e:
            st.error(f"エラーが発生しました。詳細: {str(e)}")