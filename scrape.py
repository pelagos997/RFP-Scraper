import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from functools import lru_cache
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from sklearn.cluster import DBSCAN

file_extensions = {
    ".pdf": "PDFs",
    ".xls": "Excel/CSV",
    ".xlsx": "Excel/CSV",
    ".csv": "Excel/CSV",
    ".zip": "ZIPs",
    ".doc": "Documents",
    ".docx": "Documents"
}

@lru_cache(maxsize=32)
def cached_scrape_website(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL: {str(e)}")

def extract_projects(html_content, base_url):
    """Cluster content into projects with proper URL resolution"""
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = soup.find_all(['div', 'p', 'h2', 'h3', 'table'])
    
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
            'hrefs': [urljoin(base_url, a['href']) for a in el.find_all('a', href=True)]
        })
    
    X = np.array([[b['order'], len(b['text'])] for b in blocks])
    clustering = DBSCAN(eps=4, min_samples=2).fit(X)
    
    projects = []
    for cluster_id in set(clustering.labels_):
        if cluster_id == -1:
            continue
        cluster_blocks = [b for b, c in zip(blocks, clustering.labels_) if c == cluster_id]
        projects.append(cluster_blocks)
    
    return projects

def associate_documents(context, links):
    """Document association logic"""
    doc_patterns = {
        'plans': r'\b(plan|detail|drawing)\b',
        'specs': r'\b(spec|standard|requirement)\b',
        'bids': r'\b(bid|proposal|submission)\b',
        'reports': r'\b(report|analysis|assessment)\b'
    }
    
    associated = {k: [] for k in doc_patterns}
    associated['project_specific'] = []
    
    # First pass: Filename pattern matching
    for link in links:
        filename = link.split('/')[-1].lower()
        for doc_type, pattern in doc_patterns.items():
            if re.search(pattern, filename):
                associated[doc_type].append(link)
                break
    
    # Second pass: Contextual project ID matching
    project_ids = re.findall(r'\b[A-Z]{2,4}-\d{4}\b', context)
    for link in links:
        if any(pid in link for pid in project_ids):
            associated['project_specific'].append(link)
    
    return associated

# Rest of existing scrape.py functions remain unchanged...