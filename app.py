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
                extracted = page.extract_text()
                if extracted:
                    pdf_text += extracted + "\n"
        except Exception as e:
            pass
    return pdf_text

local_pdf_context = load_local_pdfs()

# Sidebar එකේ PDF එකෙන් කියවාගත් Text එක පෙන්වීම (Debug කරගැනීමට)
with st.sidebar:
    st.subheader("📁 Upload කළ PDF තත්ත්වය")
    if local_pdf_context.strip():
        st.success(f"PDF සාර්ථකව කියවන ලදී! (අකුරු අක්ෂර ප්‍රමාණය: {len(local_pdf_context)})")
        with st.expander("කියවාගත් Text කොටස බලන්න"):
            st.text(local_pdf_context[:1500]) # මුල් අකුරු 1500 පෙන්වයි
    else:
        st.warning("data/ folder එකේ කියවිය හැකි PDF හමු නොවීය, නැතහොත් PDF එකේ අකුරු Image ලෙස ඇත.")

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

# User Input එකක් ලබාගත් විට
if user_query := st.chat_input("A/L Technology ප්‍රශ්නය මෙතැනින් අසන්න..."):
    if not api_key:
        st.error("කරුණාකර OpenRouter API Key එක සකසන්න.")
    else:
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("DeepSeek AI එක මගින් පිළිතුර සකස් කරමින් පවතියි..."):
                
                live_web_context = search_web_knowledge(user_query)

                prompt = f"""
                ඔබ ශ්‍රී ලංකාවේ A/L Technology (ET, BST, SFT) විෂයයන් පිළිබඳ ප්‍රවීණ AI ගුරුවරයෙකි.
                පහත දක්වා ඇති පෙළපොත් සටහන් (Local PDFs) සහ අන්තර්ජාලයෙන් සොයාගත් තොරතුරු (Web Results) ප්‍රධාන වශයෙන් භාවිත කරමින් සිසුවාගේ ප්‍රශ්නයට A/L විභාග ලකුණු දීමේ පටිපාටියට (Marking Scheme) අනුව නිවැරදි සිංහලෙන් පිළිතුර ලබා දෙන්න.

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

                    with st.expander("AI එක භාවිතා කළ මූලාශ්‍ර (Context)"):
                        st.write("**PDF සටහන් වලින් භාවිත කළ කොටස්:**")
                        st.text(local_pdf_context[:1000] if local_pdf_context else "PDF සටහන් හමු නොවීය.")
                        st.write("**අන්තර්ජාල මූලාශ්‍ර:**")
                        st.text(live_web_context)

                except Exception as e:
                    st.error(f"Error: {e}")
