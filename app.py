from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.prompts import PromptTemplate
from typing import List, Dict
import json
from llama_index.llms.anthropic import Anthropic
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # Add this near the top of your file

# Initialize FastAPI app
app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Define request model
class ChatMessage(BaseModel):
    message: str
    history: List[Dict[str, str]] = []  # List of previous messages

# Initialize the query engine globally
query_engine = None

def format_chat_history(history: List[Dict[str, str]]) -> str:
    """Format chat history into a string"""
    formatted_history = ""
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Kaya"
        formatted_history += f"{role}: {msg.get('content')}\n"
    return formatted_history

def init_query_engine():
    try:
        storage_context = StorageContext.from_defaults(persist_dir="backend/data/product_index")
        if not storage_context:
            print("Error: Storage context is empty")
            return None
            
        index = load_index_from_storage(storage_context)
        if not index:
            print("Error: Could not load index from storage")
            return None
        
        # Initialize Anthropic LLM
        llm = Anthropic(model="claude-3-sonnet-20240229", api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        custom_prompt = PromptTemplate("""You are Kaya, BOHECO's (Bombay Hemp Company, India's Most Trusted CBD Brand) expert virtual assistant. 
        Your responses should be professional yet warm and engaging.

        Context information from product catalog:
        ----------------
        {context_str}
        ----------------

        Previous conversation:
        {query_str}

        Current user message: {query_str}

        Guidelines for your response:
        1. Be concise but informative - keep responses to 4 sentences maximum(important!)
        2. Always mention specific prices when available
        3. Include key active ingredients and their benefits
        4. Provide clear dosage instructions when relevant
        5. Use a friendly, conversational tone
        6. If discussing multiple products, clearly differentiate between them
        7. End with a question or suggestion to encourage engagement
        8. If you're unsure about any specific detail or if the question is outside your knowledge:
           - For general inquiries: Direct users to email info@boheco.com
           - For business/bulk queries: Direct users to email sales@boheco.com
        9. Reference previous messages when relevant to maintain conversation continuity

        Remember:
        - Don't make medical claims
        - Be accurate with pricing and product details
        - Focus on education rather than hard selling
        - Use natural, conversational language
        - If you cannot confidently answer a question, be honest and provide the appropriate email contact

        Response:""")
        
        return index.as_query_engine(
            text_qa_template=custom_prompt,
            llm=llm,
            similarity_top_k=3
        )
    except Exception as e:
        print(f"Error initializing query engine: {str(e)}")
        return None

# Initialize the query engine at startup
query_engine = init_query_engine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(message: ChatMessage):
    global query_engine
    
    if not message.message or not message.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    if query_engine is None:
        query_engine = init_query_engine()
        if query_engine is None:
            raise HTTPException(
                status_code=500,
                detail="Query engine initialization failed"
            )
    
    try:
        # Format chat history
        chat_history = format_chat_history(message.history)
        
        # Combine history with current message
        full_query = f"{chat_history}\nUser: {message.message}"
        
        response = query_engine.query(full_query)
        if not response:
            raise HTTPException(
                status_code=500,
                detail="No response generated"
            )
        
        # Collect all product links from source nodes
        products = []
        seen_urls = set()
        
        for node in response.source_nodes:
            url = node.metadata.get('url')
            if url and url not in seen_urls:
                products.append({
                    'url': url,
                    'title': node.metadata.get('title', 'BOHECO Product')
                })
                seen_urls.add(url)
        
        return {
            'response': str(response),
            'products': products
        }
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat: {str(e)}"
        )

@app.get("/chat-widget")
async def chat_widget(request: Request):
    return templates.TemplateResponse("widget.html", {"request": request})