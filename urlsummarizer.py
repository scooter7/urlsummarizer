import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import replicate

# Function to scrape webpage
def scrape_webpage(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup.get_text()

# Function to summarize text using LLaMA 2
def summarize_text(text, replicate_api):
    client = replicate.Client(api_token=replicate_api)
    model = client.models.get("a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5")
    
    # Adjusting the prompt for a one-paragraph summary
    prompt = f"Please provide a one-paragraph summary of the following text:\n{text}"
    
    response = model.predict(prompt=prompt, temperature=0.5, max_length=512)
    return response[0]

# Function to process spreadsheet
def process_spreadsheet(uploaded_file, replicate_api):
    df = pd.read_csv(uploaded_file)
    df['Summary'] = df['URL'].apply(lambda url: summarize_text(scrape_webpage(url), replicate_api))
    return df

# App title
st.set_page_config(page_title="URL Summarizer")

# Replicate API key
if 'REPLICATE_API_TOKEN' in st.secrets:
    replicate_api = st.secrets['REPLICATE_API_TOKEN']
else:
    st.error("Replicate API key not found in Streamlit secrets.")
    st.stop()

# File uploader
uploaded_file = st.file_uploader("Upload your spreadsheet with URLs in 'URL' column", type=["csv", "xlsx"])

if uploaded_file is not None:
    with st.spinner('Processing...'):
        processed_df = process_spreadsheet(uploaded_file, replicate_api)

    st.success('Processing complete!')

    # Display processed data
    st.dataframe(processed_df)

    # Download button
    st.download_button(
        label="Download updated spreadsheet",
        data=processed_df.to_csv(index=False).encode('utf-8'),
        file_name='updated_spreadsheet.csv',
        mime='text/csv',
    )
