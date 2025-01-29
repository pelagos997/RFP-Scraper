from pydantic import BaseModel, Field
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectInfo(BaseModel):
    title: Optional[str] = Field(default="", description="Project title")
    description: Optional[str] = Field(default="", description="Brief description")
    dates: Dict[str, str] = Field(
        default_factory=dict,
        description="Key dates in YYYY-MM-DD format"
    )
    key_details: Dict[str, str] = Field(
        default_factory=dict,
        description="Non-date critical information"
    )
    dates: Dict[str, str] = Field(
        default_factory=dict,
        description="Key project dates in key-value pairs (e.g., 'Submission Deadline': '2024-03-15')"
    )

def parse_with_ollama(content_chunks: List[str], query: str) -> Dict:
    """Enhanced parsing with better error handling"""
    try:
        llm = Ollama(model="deepseek-r1:1.5b", temperature=0.1)
        parser = PydanticOutputParser(pydantic_object=ProjectInfo)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an RFP analysis assistant. Follow these rules:
            1. Output ONLY valid JSON without markdown formatting
            2. Never include <think> blocks or explanations
            3. Dates must be in YYYY-MM-DD format
            4. Keep values under 40 characters"""),
            
            ("user", """Analyze this content: {content}
            
            User Question: {query}
            
            {format_instructions}
            
            Example Valid Response:
            {{
            "title": "Kansas City Metro",
            "description": "Road weather stations project",
            "dates": {{
                "Submission Deadline": "2024-03-15",
                "Start Date": "2024-04-01"
            }},
            "key_details": {{
                "Project Code": "KC-2024-RWS"
            }}
            }}""")
        ])
        marked_chunks = [f"[Chunk {i+1}]: {chunk}" for i, chunk in enumerate(content_chunks)]
        combined_content = "\n\n".join(marked_chunks)
        
        chain = prompt | llm | parser
        result = chain.invoke({
            "content": combined_content,
            "query": query,
            "format_instructions": parser.get_format_instructions()
        })
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Parsing error: {str(e)}")
        return {
            "error": f"Analysis failed: {str(e)}",
            "title": "",
            "description": "",
            "key_details": {},
            "dates": {}
        }