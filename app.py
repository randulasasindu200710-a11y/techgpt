import os
import streamlit as st
from pypdf import PdfReader
from bs4 import BeautifulSoup
import urllib.request
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

st.set_page_config(page_title="A/L Tech AI Tutor", page_icon="🎓", layout="wide")
st.title("🎓 A/L Technology Multi-Source AI Tutor")

# Streamlit Secrets හෝ Sidebar මගින් API Key එක ලබා ගැනීම
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    api_key = st.sidebar.text_input("OpenRouter API Key එක ඇතුළත් කරන්න:", type="password")

if api_key:
    # OpenRouter Client එක සෑදීම
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    col1, col2 = st.columns([1, 1])
    extracted_text = ""

    with col1:
        st.subheader("📁 1. PDF සටහන් Upload කරන්න")
        uploaded_files = st.file_uploader("A/L Tech PDF / Past Papers", type="pdf", accept_multiple_files=True)
        if uploaded_files:
            for uploaded_file in uploaded_files:
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    extracted_text += page.extract_text() + "\n"
            st.success("PDF දත්ත කියවන ලදී!")

    with col2:
        st.subheader("🌐 2. Web Links සහ 🎥 3. YouTube Links")
        web_url = st.text_input("NIE හෝ වෙනත් Web Page Link එකක්:")
        yt_url = st.text_input("YouTube Video Link එකක්:")

        if st.button("Links වලින් දත්ත ලබාගන්න"):
            if web_url:
                try:
                    req = urllib.request.Request(web_url, headers={'User-Agent': 'Mozilla/5.0'})
                    html = urllib.request.urlopen(req).read()
                    soup = BeautifulSoup(html, 'html.parser')
                    extracted_text += "\n" + soup.get_text()
                    st.success("Web Page එකෙන් දත්ත එකතු විය!")
                except Exception as e:
                    st.error(f"Web Link Error: {e}")

            if yt_url:
                try:
                    video_id = yt_url.split("v=")[-1].split("&")[0]
                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    yt_text = " ".join([t['text'] for t in transcript])
                    extracted_text += "\n" + yt_text
                    st.success("YouTube Video එකෙන් Transcripts එකතු විය!")
                except Exception as e:
                    st.error(f"YouTube Error (Subtitles තිබිය යුතුය): {e}")

    st.divider()
    user_query = st.text_input("A/L Tech ප්‍රශ්නය මෙතැනින් අසන්න:")

    if user_query:
        if not extracted_text:
            st.warning("කරුණාකර ප්‍රශ්නය ඇසීමට පෙර අවම වශයෙන් එක PDF එකක්, Web Link එකක් හෝ YouTube Link එකක් ලබා දෙන්න.")
        else:
            with st.spinner("Gemini AI මගින් පිළිතුර සකස් කරමින් පවතී..."):
                prompt = f"""
                ඔබ ශ්‍රී ලංකාවේ A/L Technology (ET, BST, SFT) විෂයයන් පිළිබඳ ප්‍රවීණ ගුරුවරයෙකි.
                පහත ලබා දී ඇති විෂය කරුණු (Context) පමණක් භාවිත කරමින් සිසුවාගේ ප්‍රශ්නයට අදාළව විභාග ලකුණු දීමේ පටිපාටියට (Marking Scheme) අනුව පැහැදිලි පිළිතුරක් ලබා දෙන්න.

                Context:
                {extracted_text[:10000]}

                Question:
                {user_query}
                """

                try:
                    response = client.chat.completions.create(
                        model="google/gemini-flash-1.5",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.subheader("💡 පිළිතුර:")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"API Error: {e}")
else:
    st.warning("කරුණාකර OpenRouter API Key එක සකසන්න.")
