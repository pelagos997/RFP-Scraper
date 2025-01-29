import streamlit as st
import json  # Added JSON import
from scrape import extract_download_links, cached_scrape_website
from scrape import extract_body_content, clean_body_content, split_dom_content
from parse import parse_with_ollama
import re

# Initialize session state with proper structure
if "dom_content" not in st.session_state:
    st.session_state.dom_content = ""
if "projects" not in st.session_state:
    st.session_state.projects = []
if "editing_project" not in st.session_state:
    st.session_state.editing_project = None

def edit_project_interface():
    """Interface for editing project documents"""
    project_idx = st.session_state.editing_project
    project = st.session_state.projects[project_idx]
    
    st.subheader(f"Editing Project {project_idx + 1}")
    
    # Display current documents
    with st.expander("Current Documents"):
        for category, links in project['download_links'].items():
            st.write(f"**{category}**")
            for link in links:
                st.markdown(f"- [{link}]({link})")
    
    # Add document editing controls
    new_links = st.text_area("Add/Modify Links (one per line)", 
                           value="\n".join([link for links in project['download_links'].values() for link in links]))
    
    if st.button("Save Changes"):
        # Update links in session state
        updated_links = extract_download_links("\n".join(new_links.split("\n")), st.session_state.current_url)
        st.session_state.projects[project_idx]['download_links'] = updated_links
        st.session_state.editing_project = None
        st.experimental_rerun()

st.title('RFP Scraper')
url = st.text_input("Enter a Website URL: ")
st.session_state.current_url = url  # Store current URL for editing

if st.button("Scrape"):
    st.write("Scraping the Website...")
    try:
        html_content = cached_scrape_website(url)
        body_content = extract_body_content(html_content)
        cleaned_content = clean_body_content(body_content)
        
        download_links = extract_download_links(html_content, base_url=url)
        
        # Store data in session state
        st.session_state.dom_content = cleaned_content
        st.session_state.download_links = download_links
        st.session_state.projects = [{
            'content': cleaned_content,
            'download_links': download_links
        }]

        with st.expander("View Cleaned Content"):
            st.text_area("Content", cleaned_content, height=300)
            
        st.subheader("Downloadable Files")
        for category, links in download_links.items():
            if links:
                with st.expander(f"{category} ({len(links)})"):
                    for link in links:
                        st.markdown(f"[{link}]({link})")
                        
    except Exception as e:
        st.error(f"Scraping failed: {str(e)}")

if st.session_state.dom_content:
    parse_query = st.text_area("What information do you want to extract?")
    
    if st.button("Parse Content") and parse_query:
        st.write("Processing with LLM...")
        with st.spinner("Analyzing content..."):
            dom_chunks = split_dom_content(st.session_state.dom_content)
            result = parse_with_ollama(dom_chunks, parse_query)
            st.subheader("Extracted Results")
            st.write(result)

# Project editing interface
if st.session_state.editing_project is not None:
    edit_project_interface()

# Add document export functionality
if st.session_state.projects:
    st.download_button(
        "Export Project Data (JSON)",
        data=json.dumps(st.session_state.projects, indent=2),
        file_name="project_data.json",
        mime="application/json"
    )