# app.py の該当箇所を修正
try:
    genai.configure(api_key=api_key)
    # 2.0が0制限なら、1.5-flash で疎通できるか試す
    model = genai.GenerativeModel('gemini-1.5-flash') 
    
    with st.spinner("通信中..."):
        response = model.generate_content("こんにちは、疎通確認です。")
    st.success("成功しました！")
    st.write("AIの回答:", response.text)