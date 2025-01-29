from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup

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