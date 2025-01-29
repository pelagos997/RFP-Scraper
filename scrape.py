from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin  # For resolving relative URLs

# Add to scrape.py
from urllib.parse import urljoin  # For resolving relative URLs

def extract_download_links(html_content, base_url):
    """Extract and categorize downloadable links from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a')
    
    download_links = []
    for link in links:
        href = link.get('href')
        if href:
            # Resolve relative URLs (e.g., "/documents/plans.pdf" -> "https://dot.com/documents/plans.pdf")
            absolute_url = urljoin(base_url, href)
            download_links.append(absolute_url)
    
    # Filter by common dataset file extensions
    file_types = {
        "PDFs": [".pdf"],
        "Excel/CSV": [".xls", ".xlsx", ".csv"],
        "ZIPs": [".zip"],
        "Documents": [".doc", ".docx"]
    }
    
    organized = {category: [] for category in file_types}
    for link in download_links:
        for category, exts in file_types.items():
            if any(link.lower().endswith(ext) for ext in exts):
                organized[category].append(link)
                break  # Avoid duplicates
    
    return organized

def scrape_website(website):
    print("Launching chrome browser...")

    chrome_driver_path = "./chromedriver.exe"
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try: 
        driver.get(website)
        print("Website loaded successfully!")
        html = driver.page_source
        time.sleep(10)
        
        return html
    finally:
        driver.quit()
def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""
def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, 'html.parser')
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    
    cleaned_content = soup.get_text(separator="\n")
    
    # removes extra empty text space
    cleaned_content = "\n".join([line for line in cleaned_content.split("\n") if line.strip()])

    return cleaned_content
def split_dom_content(dom_content, max_length=6000):
    
    #token limiter for dom content
    return [dom_content[i:i+max_length] for i in range(0, len(dom_content), max_length)]