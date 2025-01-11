from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, PromptTemplate

# Initialize FastAPI app
app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Define request model
class ChatMessage(BaseModel):
    message: str

# Initialize the query engine globally
def init_query_engine():
    try:
        storage_context = StorageContext.from_defaults(persist_dir="backend/data/product_index")
        index = load_index_from_storage(storage_context)
        
        RESPONSE_TEMPLATE = """You are a helpful and knowledgeable sales assistant for BOHECO (Bombay Hemp Company). 
        Your goal is to provide informative, natural responses about their products.
        
        Context information from product catalog is below:
        ----------------
        {context_str}
        ----------------

        Using the context provided, please provide a helpful response to the user's question: {query_str}

        Your response should:
        1. Be conversational and empathetic
        2. Briefly explain why the suggested product(s) would help
        3. Include specific product features and benefits
        4. Always include the product prices if available
        5. End with a clear call to action

        Response:"""

        custom_prompt = PromptTemplate(RESPONSE_TEMPLATE)
        
        return index.as_query_engine(
            response_mode="compact",
            streaming=False,
            similarity_top_k=3,
            text_qa_template=custom_prompt,
            verbose=True
        )
    except Exception as e:
        print(f"Error initializing query engine: {str(e)}")
        return None

query_engine = init_query_engine()

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(message: ChatMessage):
    if query_engine is None:
        raise HTTPException(
            status_code=500, 
            detail="Query engine not initialized properly"
        )
    
    try:
        response = query_engine.query(message.message)
        
        # Debug print
        print("Source nodes:", [node.metadata for node in response.source_nodes])
        
        products = []
        for node in response.source_nodes:
            if node.metadata.get('url'):
                products.append({
                    'url': node.metadata.get('url'),
                    'title': node.metadata.get('title', 'BOHECO Product')
                })
        
        return {
            'response': response.response.strip(),
            'products': products
        }
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat: {str(e)}"
        )
