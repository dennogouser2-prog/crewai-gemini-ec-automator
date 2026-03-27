import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from tools import product_web_research, background_removal_and_resize

# Secrets
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
os.environ["FIRECRAWL_API_KEY"] = st.secrets["FIRECRAWL_API_KEY"]

# Gemini LLM
llm = LLM(
    model="gemini/gemini-2.5-flash",
    temperature=0.7
)

st.title("EC商品ページ自動生成AI")

product_name = st.text_input("商品名を入力")

if st.button("生成"):
    researcher = Agent(
        role="商品リサーチ担当",
        goal="商品の特徴・強み・競合情報を調査",
        backstory="ECマーケター",
        tools=[product_web_research],
        llm=llm
    )

    writer = Agent(
        role="EC商品ページライター",
        goal="売れる商品説明を作成",
        backstory="ECコピーライター",
        llm=llm
    )

    task1 = Task(
        description=f"{product_name} の商品情報をWebで調査",
        agent=researcher
    )

    task2 = Task(
        description=f"{product_name} の売れる商品説明文を作成",
        agent=writer
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        process=Process.sequential
    )

    result = crew.kickoff()
    st.write(result)