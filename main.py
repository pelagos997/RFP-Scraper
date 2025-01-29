import streamlit as st
import json
from scrape import extract_download_links, cached_scrape_website
from scrape import extract_body_content, clean_body_content, split_dom_content
from parse import parse_with_ollama

# Initialize session state
if "dom_content" not in st.session_state:
    st.session_state.dom_content = ""
if "projects" not in st.session_state:
    st.session_state.projects = []
if "editing_project" not in st.session_state:
    st.session_state.editing_project = None

st.title('RFP Document Analyzer')

# URL input
url = st.text_input("Enter RFP Website URL:")
st.session_state.current_url = url

if st.button("Analyze Website"):
    if url:
        with st.spinner("Analyzing website content..."):
            try:
                # Scrape and process content
                html_content = cached_scrape_website(url)
                body_content = extract_body_content(html_content)
                cleaned_content = clean_body_content(body_content)
                download_links = extract_download_links(html_content, base_url=url)
                
                # Store in session state
                st.session_state.dom_content = cleaned_content
                st.session_state.download_links = download_links
                st.session_state.projects = [{
                    'content': cleaned_content,
                    'download_links': download_links
                }]

                # Display results
                st.success("Website analyzed successfully!")
                
                with st.expander("View Processed Content"):
                    st.text_area("Content", cleaned_content, height=300)
                
                st.subheader("📎 Downloadable Files")
                for category, links in download_links.items():
                    if links:
                        with st.expander(f"{category} ({len(links)})"):
                            for link in links:
                                st.markdown(f"[{link}]({link})")
                        
            except Exception as e:
                st.error(f"Error analyzing website: {str(e)}")
    else:
        st.warning("Please enter a URL")

# Content analysis section
if st.session_state.dom_content:
    st.divider()
    st.subheader("🔍 Ask Questions About the Content")
    query = st.text_area("What would you like to know about this RFP?", 
                        placeholder="Example: What are the key dates and deadlines?")
    
    if st.button("Analyze") and query:
        with st.spinner("Processing your question..."):
            try:
                chunks = split_dom_content(st.session_state.dom_content)
                result = parse_with_ollama(chunks, query)
                
                st.subheader("📑 Analysis Results")
                
                # Display structured results
                if result.get("title"):
                    st.markdown(f"**Project Title:** {result['title']}")
                if result.get("description"):
                    st.markdown(f"**Description:** {result['description']}")
                if result.get("key_details"):
                    st.markdown("**Key Details:**")
                    for key, value in result["key_details"].items():
                        st.markdown(f"- {key}: {value}")
                if result.get("dates"):
                    st.markdown("**Important Dates:**")
                    for date_type, date in result["dates"].items():
                        st.markdown(f"- {date_type}: {date}")
                        
            except Exception as e:
                st.error(f"Error analyzing content: {str(e)}")

# Export functionality
if st.session_state.projects:
    st.divider()
    st.download_button(
        "💾 Export Analysis (JSON)",
        data=json.dumps(st.session_state.projects, indent=2),
        file_name="rfp_analysis.json",
        mime="application/json"
    )