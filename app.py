import os
import glob
import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
from pypdf import PdfReader

# Web Page එක Gemini / ChatGPT Chat අතුරුමුහුණතක් ලෙස සැකසීම
st.set_page_config(page_title="A/L Tech Smart AI Tutor", page_icon="🎓", layout="centered")
st.title("🎓 A/L Technology AI Tutor")
st.caption("අන්තර්ජාලය, NIE තොරතුරු සහ විෂය නිර්දේශ සටහන් ඇසුරෙන් ස්වයංක්‍රීයව පිළිතුරු සපයයි.")

# Streamlit Secrets හෝ Sidebar මගින් API Key එක ලබා ගැනීම
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    api_key = st.sidebar.text_input("OpenRouter API Key එක ඇතුළත් කරන්න:", type="password")

# GitHub Repo එකේ 'data' folder එකේ ඇති PDFs තිබේ නම් ඒවා Auto-read කිරීම
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

# AI එක විසින්ම අන්තර්ජාලයෙන් (Google / NIE / YouTube notes) ස්වයංක්‍රීයව සෙවීම
def search_web_knowledge(query):
    search_results = ""
    try:
        with DDGS() as ddgs:
            # Sri Lanka A/L Tech විෂයට අදාළව අන්තර්ජාලය සෙවීම
            results = list(ddgs.text(f"Sri Lanka AL Technology NIE {query}", max_results=5))
            for r in results:
                search_results += f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n\n"
    except Exception:
        search_results = "Web search automated fetching failed."
    return search_results

# Chat History සකස් කිරීම
if "messages" not in st.session_state:
    st.session_state.messages = []

# පැරණි සංවාද UI එකේ පෙන්වීම
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# පරිශීලකයා ප්‍රශ්නයක් ඇසූ විට
if user_query := st.chat_input("A/L Technology ප්‍රශ්නය මෙතැනින් අසන්න..."):
    if not api_key:
        st.error("කරුණාකර API Key එක සකසන්න.")
    else:
        # පරිශීලකයාගේ ප්‍රශ්නය Chat එකට එකතු කිරීම
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("AI එක විසින් NIE සහ අන්තර්ජාල තොරතුරු ස්වයංක්‍රීයව පරීක්ෂා කරමින් පවතියි..."):
                
                # 1. ස්වයංක්‍රීයව Web Search කිරීම
                live_web_context = search_web_knowledge(user_query)

                # 2. Prompt එක සකස් කිරීම
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
                    response = client.chat.completions.create(
                        model="google/gemini-flash-1.5",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    answer = response.choices[0].message.content
                    
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                    # AI එක සොයාගත් මූලාශ්‍ර බලාගැනීමට
                    with st.expander("AI එක ස්වයංක්‍රීයව සෙවූ මූලාශ්‍ර (Auto-searched Context)"):
                        st.text(live_web_context)

                except Exception as e:
                    st.error(f"Error: {e}")
