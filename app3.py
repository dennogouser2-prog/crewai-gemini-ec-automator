import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

st.title("🛠️ API疎通確認テスト")

api_key = os.getenv("GOOGLE_API_KEY")

if st.button("APIテスト実行"):
    if not api_key:
        st.error("APIキーが設定されていません。")
        st.stop()
        
    try:
        # CrewAIを介さず、直接Googleのライブラリで呼び出し
        genai.configure(api_key=api_key)
        # 2.0-flashが制限されている可能性があるため、1.5-flashでテスト
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        with st.spinner("通信中..."):
            response = model.generate_content("ECサイトのキャッチコピーを作って。商品は『美味しいパン』です。10文字以内で。")
            
        st.success("成功しました！")
        st.write("AIの回答:", response.text)
        
    except Exception as e:
        st.error(f"エラーが発生しました。詳細: {str(e)}")
        if "429" in str(e):
            st.warning("やはりお支払い設定がAPIキーに反映されていません（Tier 1になっていない）。")