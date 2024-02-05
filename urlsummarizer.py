import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import openai

def scrape_webpage(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup.get_text()

def split_text_into_chunks(text, max_chunk_size=4000):
    words = text.split(' ')
    chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def summarize_chunk(chunk, openai_api_key):
    openai.api_key = openai_api_key
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=f"Summarize the following content in one paragraph:\n{chunk}",
        max_tokens=150,
        temperature=0.5,
        stop=["\n"]
    )
    return response.choices[0].text.strip()

def summarize_text(text, openai_api_key):
    chunks = split_text_into_chunks(text)
    summaries = [summarize_chunk(chunk, openai_api_key) for chunk in chunks]
    final_summary = ' '.join(summaries)
    return final_summary

def process_spreadsheet(uploaded_file, openai_api_key):
    df = pd.read_csv(uploaded_file)
    df['Summary'] = df['URL'].apply(lambda url: summarize_text(scrape_webpage(url), openai_api_key))
    return df

st.set_page_config(page_title="URL Summarizer")

if 'OPENAI_API_KEY' in st.secrets:
    openai_api_key = st.secrets['OPENAI_API_KEY']
else:
    st.error("OpenAI API key not found in Streamlit secrets.")
    st.stop()

uploaded_file = st.file_uploader("Upload your spreadsheet with URLs in 'URL' column", type=["csv", "xlsx"])

if uploaded_file is not None:
    with st.spinner('Processing...'):
        processed_df = process_spreadsheet(uploaded_file, openai_api_key)
    st.success('Processing complete!')
    st.dataframe(processed_df)
    st.download_button(
        label="Download updated spreadsheet",
        data=processed_df.to_csv(index=False).encode('utf-8'),
        file_name='updated_spreadsheet.csv',
        mime='text/csv',
    )
