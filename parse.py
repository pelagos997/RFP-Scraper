from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StructuredOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
from scrape import associate_documents

class ProjectModel(BaseModel):
    identifiers: dict = Field(..., description="Contract numbers, project IDs")
    dates: dict = Field(..., description="Key project dates")
    documents: dict = Field(..., description="Categorized document links")
    entities: list = Field(..., description="Related organizations")

model = OllamaLLM(model="llama3:8b", temperature=0.1)

def parse_project_cluster(cluster, base_url):
    """Integrated parsing with proper imports"""
    context = "\n".join([item['text'] for item in cluster])
    links = [urljoin(base_url, item['href']) for item in cluster if item.get('href')]
    
    parser = StructuredOutputParser.from_pydantic(ProjectModel)
    prompt = ChatPromptTemplate.from_template("""
    Analyze this project cluster:
    {context}
    {format_instructions}
    """)
    
    chain = prompt | model | parser
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        future = executor.submit(
            chain.invoke,
            {"context": context, "format_instructions": parser.get_format_instructions()}
        )
        result = future.result().dict()
    
    result['documents'] = associate_documents(context, links)
    return result