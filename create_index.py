import requests
from bs4 import BeautifulSoup
from llama_index.core import Document
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.llms.anthropic import Anthropic
from llama_index.core import Settings
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def scrape_product_page(url: str):
    """
    Fetch the product URL, parse it, and return a tuple of:
      (title, product_text, metadata_dict).
    Return None if the request fails or the page is inaccessible.
    """

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"[WARN] Skipping {url}, status code: {resp.status_code}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # ---------------------------
        # EXTRACT KEY DATA FIELDS
        # ---------------------------

        # 1) Product Title
        #    <h1 class="product__title"> PRISTINE ... </h1>
        h1_title_el = soup.select_one("h1.product__title")
        product_title = h1_title_el.get_text(strip=True) if h1_title_el else "Untitled Product"

        # 2) Price
        #    Usually found in <div class="product__price" data-product-price="">₹649</div>
        price_el = soup.select_one("div.product__price span[data-product-price]")
        if not price_el:
            # fallback: check standard price container
            price_el = soup.select_one("div.product__price span")
        product_price = price_el.get_text(strip=True) if price_el else "Unknown"

        # 3) Main Description
        #    Usually the product description can be in multiple places; 
        #    in your snippet, a good fallback is inside ".product__description"
        #    or the 'Description' tab content in ".tab-content-0"
        description_el = soup.select_one(".tab-content-0 .tab-content__entry")
        product_description = (
            description_el.get_text(separator="\n", strip=True) if description_el else ""
        )

        # 4) Ingredients
        #    In your snippet, there's a collapsible "Ingredients" section:
        #    <button class="accordionn"><span>Ingredients</span></button>
        #    <div class="accordion-content-main">...</div>
        #    We'll look for a known heading or text like "Ingredients"
        ingredients_text = ""
        # A simple approach: search for the <button> that has text "Ingredients"
        # Then get the next sibling or the .accordion-content-main
        # This can vary if your markup changes for other products
        ingredients_button = soup.find("button", string=lambda t: t and "Ingredients" in t)
        if ingredients_button:
            # .parent or next sibling approach
            next_div = ingredients_button.find_next("div", class_="accordion-content-main")
            if next_div:
                ingredients_text = next_div.get_text(separator=" ", strip=True)

        # 5) Usage or “How To Use”
        #    In your snippet, there's a <section> with an <h2> = "HOW TO USE"
        #    Or a <p> inside .standard__rte that mentions usage instructions
        usage_instructions = ""
        how_to_use_section = soup.select_one("h2.h4.standard__heading:-soup-contains('HOW TO USE')")
        if how_to_use_section:
            # The usage text is in the next sibling or the associated <section>
            # For your snippet, we see it's in the same <section> but in a .standard__rte.
            # We'll do a broad approach:
            parent_section = how_to_use_section.find_parent("section")
            if parent_section:
                usage_paragraph = parent_section.select_one(".standard__rte p")
                if usage_paragraph:
                    usage_instructions = usage_paragraph.get_text(separator=" ", strip=True)

        # 6) Combine these textual elements into a single doc body
        #    This ensures the retrieval step has everything in one place.
        doc_text = (
            f"PRODUCT TITLE:\n{product_title}\n\n"
            f"PRICE:\n{product_price}\n\n"
            f"DESCRIPTION:\n{product_description}\n\n"
            f"INGREDIENTS:\n{ingredients_text}\n\n"
            f"HOW TO USE:\n{usage_instructions}\n"
        )

        # 7) Attach metadata
        metadata = {
            "url": url,
            "title": product_title,
            "price": product_price,
            "type": "product"
        }

        return (product_title, doc_text, metadata)

    except Exception as e:
        print(f"[ERROR] Failed to scrape {url}: {e}")
        return None

def create_product_index():
    # 1. Load all URLs
    with open("product_urls.txt", 'r') as f:
        urls = [u.strip() for u in f if u.strip()]

    all_docs = []
    
    # 2. Scrape each product URL individually
    for url in urls:
        result = scrape_product_page(url)
        if not result:
            continue  # skip if page is inaccessible or error occurred
        
        product_title, doc_text, metadata = result
        
        # Create one doc per product
        doc = Document(
            text=doc_text,
            metadata=metadata
        )
        all_docs.append(doc)
    
    print(f"Collected {len(all_docs)} product docs out of {len(urls)} URLs.")
    
    # 3. Build the index
    #   - Use Anthropic with a low temperature
    llm = Anthropic(
        model="claude-3-sonnet-20240229",  # or claude-3 etc.
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0.0
    )
    
    # Update the settings globally
    Settings.llm = llm
    
    # Create index directly without service_context
    index = VectorStoreIndex.from_documents(all_docs)
    
    # 4. Persist to disk
    storage_context = index.storage_context
    storage_context.persist(persist_dir="backend/data/product_index")

    print("Product index created and persisted successfully!")

if __name__ == "__main__":
    create_product_index()
