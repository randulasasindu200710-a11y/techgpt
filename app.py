import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="A/L Tech Multi-Source AI", page_icon="🎓", layout="wide")
st.title("🎓 A/L Technology AI Tutor")

# Streamlit Secrets මගින් API Key එක auto-load කරගැනීම
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    api_key = st.sidebar.text_input("OpenRouter API Key එක ඇතුළත් කරන්න:", type="password")

if api_key:
    col1, col2 = st.columns([1, 1])
    documents = []

    with col1:
        st.subheader("📁 1. PDF සටහන් Upload කරන්න")
        uploaded_files = st.file_uploader("A/L Tech PDF / Past Papers", type="pdf", accept_multiple_files=True)
        if uploaded_files:
            for uploaded_file in uploaded_files:
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                loader = PyPDFLoader(uploaded_file.name)
                documents.extend(loader.load())
            st.success(f"{len(uploaded_files)} PDF එකතු කරන ලදී.")

    with col2:
        st.subheader("🌐 2. NIE Web Links සහ 🎥 3. YouTube Links")
        web_url = st.text_input("NIE Web Page Link එක ඇතුළත් කරන්න:")
        yt_url = st.text_input("YouTube Video Link එක ඇතුළත් කරන්න:")

        if st.button("Links වලින් දත්ත ලබාගන්න"):
            if web_url:
                try:
                    web_docs = WebBaseLoader(web_url).load()
                    documents.extend(web_docs)
                    st.success("Web Page එකෙන් දත්ත එකතු විය!")
                except Exception as e:
                    st.error(f"Web Link Error: {e}")

            if yt_url:
                try:
                    yt_docs = YoutubeLoader.from_youtube_url(yt_url, add_video_info=False).load()
                    documents.extend(yt_docs)
                    st.success("YouTube Video එකෙන් Transcripts එකතු විය!")
                except Exception as e:
                    st.error(f"YouTube Error: {e}")

    if documents:
        st.divider()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(splits, embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        system_prompt = (
            "ඔබ ශ්‍රී ලංකාවේ A/L Technology (ET, BST, SFT) විෂයයන් පිළිබඳ ප්‍රවීණ ගුරුවරයෙකි. "
            "ලබා දී ඇති සටහන් (Context) ඇසුරෙන් පමණක් Marking Scheme එකට අනුව නිවැරදිව පිළිතුරු සපයන්න.\n\n"
            "Context: {context}"
        )
        prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])

        llm = ChatOpenAI(
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            model_name="google/gemini-flash-1.5",
            temperature=0.3
        )

        rag_chain = create_retrieval_chain(retriever, create_stuff_documents_chain(llm, prompt))

        user_query = st.text_input("A/L Tech ප්‍රශ්නය මෙතැනින් අසන්න:")
        if user_query:
            with st.spinner("පිළිතුර සකස් කරමින් පවතී..."):
                response = rag_chain.invoke({"input": user_query})
                st.subheader("💡 පිළිතුර:")
                st.write(response["answer"])
else:
    st.warning("API Key එක සකසා නැත.")
