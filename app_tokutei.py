import streamlit as st
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import product_web_research, background_removal_and_resize

#.envファイルを読み込む
load_dotenv()

# --- 2026年3月現在の推奨安定モデル ---
# gemini-1.5-flashは廃止されたため、最新の2.5を使用します
MODEL_NAME = "gemini-2.5-flash" 

st.set_page_config(page_title="EC自動化：特定商品最適化版", layout="wide")
st.title("🚀 EC商品登録：特定名称・負荷軽減エージェント")

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("APIキーが設定されていません。.envファイルを確認してください。")
    st.stop()

# LLM設定
llm = ChatGoogleGenerativeAI(model=MODEL_NAME, api_key=api_key)

# --- UI：設定項目 ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("商品情報入力")
    name_input = st.text_input("商品名（例：バルミューダ ザ・トースター K11A-BK）")
    manual_features = st.text_area("補足情報（任意：色、サイズ、独自の売りなど）")
    
    # 429エラー回避のため、デフォルトはWEB調査OFF。特定商品ならAIの知識だけで十分なケースが多いです
    use_web_research = st.checkbox("WEB調査を実行する（より最新の情報が必要な場合のみON）", value=False)
    image_input = st.file_uploader("画像（背景削除・リサイズ用）", type=["jpg", "png", "jpeg"])

# --- 生成開始 ---
if st.button("コピー生成開始") and name_input:
    with st.spinner(f"AIが『{name_input}』の最適コピーを構成中..."):
        
        # 1. 商品特性を整理するエージェント
        # 【修正の核心】elseの後に空のリスト を指定し、末尾のカンマを正しく配置しました
        analyst = Agent(
            role='商品スペシャリスト',
            goal=f'商品名「{name_input}」のブランド価値と機能的特徴を、AIの知識と補足情報から抽出する',
            backstory='20年のEC運用経験を持つ専門家。商品名から即座にターゲット層と最大の魅力を特定するのが得意。',
            llm=llm,
            tools=[product_web_research] if use_web_research else,
            max_iter=1,
            verbose=True
        )

        # 2. セールスコピーライター
        copywriter = Agent(
            role='戦略的ライター',
            goal='10, 20, 30, 50文字の4パターンで、SEO効果の高いクリックしたくなるコピーを作る',
            backstory='SEOの30文字タイトルルール（前半15文字に重要語）を熟知したプロ [1]。スキー用品にも深い知識を持つ',
            llm=llm,
            max_iter=1,
            verbose=True
        )

        # タスク定義：特定商品名を優先的に深掘りするよう指示
        research_desc = f"商品名「{name_input}」について、あなたの知識と補足情報「{manual_features}」を統合して、主要なセールスポイントをまとめてください。"
        if use_web_research:
            research_desc += "必要に応じてWEBツールで最新の競合情報を確認してください。"

        task1 = Task(
            description=research_desc, 
            expected_output="商品の魅力とターゲットをまとめたレポート", 
            agent=analyst
        )
        
        task2 = Task(
            description="レポートを元に、10文字、20文字、30文字、50文字の日本語コピーを厳密に作成してください。", 
            expected_output="4パターンのコピー案（各文字数制限を厳守）", 
            agent=copywriter, 
            context=[task1]
        )

        crew = Crew(agents=[analyst, copywriter], tasks=[task1, task2], process=Process.sequential)
        
        try:
            # テキスト生成の実行
            result = crew.kickoff()
            
            # 画像処理の実行（ローカル環境のCPUで行うためGeminiの負荷制限には影響しません）
            if image_input:
                img_path = os.path.abspath(f"temp_{image_input.name}")
                with open(img_path, "wb") as f:
                    f.write(image_input.getbuffer())
                # rembgを使用して白背景・85%占有率の処理を実行 [2]
                background_removal_and_resize.run(image_path=img_path)

            st.success("生成が完了しました！")
            with col2:
                st.subheader("生成されたコピー案")
                st.markdown(result.raw)
                
                if image_input:
                    st.subheader("EC最適化済み画像")
                    processed_img = f"processed_{os.path.basename(img_path)}"
                    if os.path.exists(processed_img):
                        # 白背景かつ商品が85%を占めるAmazon規約準拠の画像を表示 [2]
                        st.image(processed_img, caption="背景削除・リサイズ済み")
                        
        except Exception as e:
            if "429" in str(e):
                st.error("APIのリミットエラーです。AI Studioで『新しいプロジェクト』でのキー再発行をお試しください。")
            else:
                st.error(f"実行エラー: {str(e)}")