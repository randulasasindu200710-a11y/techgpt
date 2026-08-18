import os
import glob
import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
from pypdf import PdfReader

# Streamlit Page Setup
st.set_page_config(page_title="A/L Tech Smart AI Tutor", page_icon="🎓", layout="centered")
st.title("🎓 A/L Technology AI Tutor (IT, ET, SFT, BST)")
st.caption("IT, ET, SFT සහ BST විෂයයන්ට පමණක් අදාළව පිළිතුරු සපයයි.")

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
                extracted = page.extract_text()
                if extracted:
                    pdf_text += extracted + "\n"
        except Exception:
            pass
    return pdf_text

local_pdf_context = load_local_pdfs()

# DuckDuckGo හරහා අන්තර්ජාලයෙන් NIE සහ Subject කරුණු සෙවීම
def search_web_knowledge(query):
    search_results = ""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"Sri Lanka AL Technology IT ET SFT BST {query}", max_results=5))
            for r in results:
                search_results += f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n\n"
    except Exception:
        search_results = "Web search automated fetching failed."
    return search_results

# User Input එකක් ලබාගත් විට (පැරණි දත්ත රඳවා නොගනිමින් අලුත් ප්‍රශ්නය පමණක් පෙන්වයි)
if user_query := st.chat_input("IT, ET, SFT, හෝ BST ප්‍රශ්නය මෙතැනින් අසන්න..."):
    if not api_key:
        st.error("කරුණාකර OpenRouter API Key එක සකසන්න.")
    else:
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("AI එක මගින් විෂය පථය පරීක්ෂා කරමින් පවතියි..."):
                
                live_web_context = search_web_knowledge(user_query)

                prompt = f"""
                ඔබ ශ්‍රී ලංකාවේ A/L Technology විෂයයන් වන **IT (Information Technology), ET (Engineering Technology), SFT (Science for Technology), සහ BST (Bio-Systems Technology)** සඳහා පමණක් සීමා වූ දැඩි නීති රීති සහිත AI ගුරුවරයෙකි.

                --- ප්‍රධාන නීතිය ---
                සිසුවා අසන ප්‍රශ්නය ඉහත සඳහන් කළ විෂයයන් හතරට (**IT, ET, SFT, BST**) හෝ අපගේ PDF සටහන්වලට සම්පූර්ණයෙන්ම පිටස්තර ප්‍රශ්නයක් නම් (උදා: සාමාන්‍ය ලෝක ජනගහනය, ඉතිහාසය, කලා විෂයයන්, වෙනත් සාමාන්‍ය දැනීම ආදිය), කිසි විටෙකත් විස්තර ලබා දෙන්න එපා. හරියටම පහත සඳහන් වාක්‍ය පමණක් පිළිතුර ලෙස දෙන්න:
                "මෙම ප්‍රශ්නය IT, ET, SFT, හෝ BST (A/L Technology) විෂයයන්ට අදාළ නොවේ. කරුණාකර මෙම තාක්ෂණික විෂයයන්ට අදාළ ප්‍රශ්නයක් පමණක් අසන්න."

                ප්‍රශ්නය ඉහත සඳහන් තාක්ෂණික විෂයයන්ට අදාළ නම් පමණක්, පහත PDF සටහන් සහ අන්තර්ජාල තොරතුරු භාවිත කරමින් A/L විභාග ලකුණු දීමේ පටිපාටියට අනුව නිවැරදි සිංහලෙන් පිළිතුරු දෙන්න.

                --- අපගේ පෙළපොත් / PDF සටහන් ---
                {local_pdf_context[:6000]}

                --- අන්තර්ජාලයෙන් සොයාගත් තොරතුරු ---
                {live_web_context}

                --- සිසුවාගේ ප්‍රශ්නය ---
                {user_query}
                """

                try:
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=api_key,
                    )
                    response = client.chat.completions.create(
                        model="deepseek/deepseek-chat",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    answer = response.choices[0].message.content
                    
                    st.write(answer)

                except Exception as e:
                    st.error(f"Error: {e}")
