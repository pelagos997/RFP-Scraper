import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from functools import lru_cache
from typing import Dict, List, Any
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Fixed import
import numpy as np
from sklearn.cluster import DBSCAN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File extension categories
FILE_EXTENSIONS = {
    ".pdf": "PDFs",
    ".xls": "Excel Files",
    ".xlsx": "Excel Files",
    ".csv": "CSV Files",
    ".zip": "Archives",
    ".doc": "Word Documents",
    ".docx": "Word Documents",
    ".txt": "Text Files",
    ".rtf": "Rich Text Files"
}

@lru_cache(maxsize=32)
def cached_scrape_website(url: str) -> str:
    """
    Scrape website content with caching.
    
    Args:
        url: Website URL to scrape
        
    Returns:
        str: HTML content of the website
        
    Raises:
        RuntimeError: If website cannot be accessed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch URL {url}: {str(e)}")
        raise RuntimeError(f"Failed to access website: {str(e)}")

def extract_body_content(html_content: str) -> str:
    """
    Extract the body content from HTML.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        str: Extracted body content
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        return str(soup.body) if soup.body else html_content
    except Exception as e:
        logger.error(f"Error extracting body content: {str(e)}")
        return html_content

def clean_body_content(body_content: str) -> str:
    """
    Clean and format body content.
    
    Args:
        body_content: Raw body content
        
    Returns:
        str: Cleaned content
    """
    try:
        soup = BeautifulSoup(body_content, 'lxml')
        
        # Remove unwanted elements
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'meta', 'link']):
            tag.decompose()
        
        # Get text with spacing
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error cleaning body content: {str(e)}")
        return body_content

def extract_download_links(html_content: str, base_url: str) -> Dict[str, List[str]]:
    """
    Extract and categorize downloadable file links.
    
    Args:
        html_content: HTML content to analyze
        base_url: Base URL for resolving relative links
        
    Returns:
        Dict[str, List[str]]: Categorized file links
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        organized_links: Dict[str, List[str]] = {
            category: [] for category in set(FILE_EXTENSIONS.values())
        }
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            try:
                full_url = urljoin(base_url, href)
                # Check for file extensions
                ext = href[href.rfind('.'):].lower() if '.' in href else ''
                if ext in FILE_EXTENSIONS:
                    category = FILE_EXTENSIONS[ext]
                    if full_url not in organized_links[category]:
                        organized_links[category].append(full_url)
            except Exception as e:
                logger.warning(f"Error processing link {href}: {str(e)}")
                continue
                
        return organized_links
    except Exception as e:
        logger.error(f"Error extracting download links: {str(e)}")
        return {category: [] for category in set(FILE_EXTENSIONS.values())}

def split_dom_content(content: str) -> List[str]:
    """
    Split content into manageable chunks for analysis.
    
    Args:
        content: Text content to split
        
    Returns:
        List[str]: List of content chunks
    """
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        return splitter.split_text(content)
    except Exception as e:
        logger.error(f"Error splitting content: {str(e)}")
        # If splitting fails, return content as a single chunk
        return [content] if content else []

def extract_projects(html_content: str, base_url: str) -> List[List[Dict[str, Any]]]:
    """
    Extract and cluster project-related content.
    
    Args:
        html_content: HTML content to analyze
        base_url: Base URL for resolving links
        
    Returns:
        List[List[Dict]]: Clustered project content
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        elements = soup.find_all(['div', 'p', 'h2', 'h3', 'h4', 'table'])
        
        blocks = []
        for idx, el in enumerate(elements):
            text = el.get_text(' ', strip=True)
            if not text:
                continue
                
            blocks.append({
                'text': text,
                'order': idx,
                'is_header': el.name.startswith('h'),
                'is_table': el.name == 'table',
                'hrefs': [urljoin(base_url, a['href']) 
                         for a in el.find_all('a', href=True)]
            })
        
        if not blocks:
            return []
            
        # Create feature matrix for clustering
        X = np.array([[b['order'], len(b['text'])] for b in blocks])
        
        # Normalize features
        X = (X - X.mean(axis=0)) / X.std(axis=0)
        
        # Perform clustering
        clustering = DBSCAN(eps=0.5, min_samples=2).fit(X)
        
        # Group blocks by cluster
        projects = []
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:  # Skip noise points
                continue
            cluster_blocks = [b for b, c in zip(blocks, clustering.labels_) 
                            if c == cluster_id]
            if cluster_blocks:
                projects.append(cluster_blocks)
        
        return projects
    except Exception as e:
        logger.error(f"Error extracting projects: {str(e)}")
        return []