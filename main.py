import streamlit as st
from scrape import extract_download_links
from scrape import scrape_website
from scrape import (
    extract_body_content, 
    clean_body_content, 
    split_dom_content
)

st.title('RFP Scraper')
url = st.text_input("Enter a Website Url: ")

if st.button("Scrape"):
    st.write("Scraping the Website")
    result = scrape_website(url)
    body_content = extract_body_content(result)
    cleaned_content = clean_body_content(body_content)
    
    
    # Extract and organize download links
    # Pass the original URL for resolving relative paths
    download_links = extract_download_links(result, base_url=url)  
    
    st.session_state.dom_content = cleaned_content
    st.session_state.download_links = download_links

    with st.expander("View Content"):
        st.text_area("DOM Content", cleaned_content, height = 300)
    st.subheader("Downloadable Files")
    for category, links in download_links.items():
        if links:  # Only show categories with links
            with st.expander(f"{category} ({len(links)})"):
                for link in links:
                    st.markdown(f"[{link}]({link})")