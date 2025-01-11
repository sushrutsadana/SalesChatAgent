from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.readers.web import SimpleWebPageReader
from llama_index.llms.anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Configure the LLM before creating the index
Settings.llm = Anthropic(model="claude-3-sonnet-20240229")

def create_index():
    with open("product_urls.txt", 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print("Loading product pages...")
    documents = SimpleWebPageReader(html_to_text=True).load_data(urls=urls)
    
    # Enhance documents with metadata
    for doc, url in zip(documents, urls):
        doc.metadata = {
            'url': url,
            'title': doc.metadata.get('title', 'BOHECO Product'),
            'source': url
        }
    
    print("Creating index...")
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist("backend/data/product_index")
    print("Index created successfully!")

if __name__ == "__main__":
    create_index()