import os
import glob
import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
from pypdf import PdfReader

# Streamlit Page Setup
st.set_page_config(page_title="A/L Tech Smart AI Tutor", page_icon="🎓", layout="centered")
st.title("🎓 A/L Technology AI Tutor")
st.caption("අන්තර්ජාලය, NIE තොරතුරු සහ විෂය නිර්දේශ සටහන් ඇසුරෙන් ස්වයංක්‍රීයව පිළිතුරු සපයයි.")

# Streamlit Secrets හෝ Sidebar මගින් API Key එක ලබා ගැනීම
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    api_key = st.sidebar.text_input("OpenRouter API Key එක ඇතුළත් කරන්න:", type="password")

# GitHub Repo එකේ 'data' folder එකේ ඇති PDFs ස්වයංක්‍රීයව කියවීම
@st.cache_data
def load_local_pdfs():
    pdf_text = ""
    pdf_files = glob.glob("data/*.pdf")
    for file in pdf_files:
        try:
            reader = PdfReader(file)
            for page in reader.pages:
                pdf_text += page.extract_text() + "\n"
        except Exception:
            pass
    return pdf_text

local_pdf_context = load_local_pdfs()

# DuckDuckGo හරහා අන්තර්ජාලයෙන් NIE සහ Subject කරුණු සෙවීම
def search_web_knowledge(query):
    search_results = ""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"Sri Lanka AL Technology NIE {query}", max_results=5))
            for r in results:
                search_results += f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n\n"
    except Exception:
        search_results = "Web search automated fetching failed."
    return search_results

# Chat History සැකසීම
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# User Input එකක් ලබාගත් විට
if user_query := st.chat_input("A/L Technology ප්‍රශ්නය මෙතැනින් අසන්න..."):
    if not api_key:
        st.error("කරුණාකර OpenRouter API Key එක සකසන්න.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("DeepSeek AI එක මගින් පිළිතුර පරීක්ෂා කරමින් පවතියි..."):
                
                live_web_context = search_web_knowledge(user_query)

                prompt = f"""
                ඔබ ශ්‍රී ලංකාවේ A/L Technology (ET, BST, SFT) විෂයයන් පිළිබඳ ප්‍රවීණ AI ගුරුවරයෙකි.
                පහත දක්වා ඇති අන්තර්ජාලයෙන් ස්වයංක්‍රීයව සොයාගත් NIE/විෂය කරුණු (Web Results) සහ පෙළපොත් සටහන් (Local PDFs) භාවිත කරමින් සිසුවාගේ ප්‍රශ්නයට A/L විභාග ලකුණු දීමේ පටිපාටියට (Marking Scheme) අනුව නිවැරදි සිංහලෙන් පිළිතුර ලබා දෙන්න.

                --- අන්තර්ජාලයෙන් ස්වයංක්‍රීයව සොයාගත් තොරතුරු ---
                {live_web_context}

                --- ස්වයංක්‍රීය පෙළපොත් සටහන් (තිබේ නම්) ---
                {local_pdf_context[:4000]}

                --- සිසුවාගේ ප්‍රශ්නය ---
                {user_query}
                """

                try:
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=api_key,
                    )
                    # DeepSeek Model එක භාවිත කිරීම
                    response = client.chat.completions.create(
                        model="deepseek/deepseek-chat",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    answer = response.choices[0].message.content
                    
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                    with st.expander("AI එක ස්වයංක්‍රීයව සෙවූ මූලාශ්‍ර (Auto-searched Context)"):
                        st.text(live_web_context)

                except Exception as e:
                    st.error(f"Error: {e}")
