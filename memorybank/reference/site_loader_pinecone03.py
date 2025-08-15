from langchain_community.document_loaders.sitemap import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import Chroma
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

import os
import openai
from dotenv import load_dotenv, find_dotenv

from ruamel.yaml import YAML
from pathlib import Path
# from pinecone import Pinecone, ServerlessSpec

# Note this document is dependent on 'quick_sm2yaml.py' to go
# through a list of sitemaps and create a list of page URLs.
# This was done because of issues with using SiteMapLoader.
# Also note that 'certifi' needs to be installed and run to 
# avoid SSL errors.

# ----------------------------
# Constants
# ----------------------------

# DB_PATH = "./db/agrofresh01"
PAGES_TO_INGEST_PATH = "./xml/20241107/load20241108.yaml"
INDEX_NAME = "agrofresh01"
EMBEDDING_MODEL = "text-embedding-3-small"
USER_AGENT = "myagent"
# USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

# ----------------------------
# Initialize Classes
# ----------------------------

load_dotenv(find_dotenv())
openai.api_key = os.getenv("OPENAI_API_KEY")
embeddings_model = OpenAIEmbeddings(model=EMBEDDING_MODEL, show_progress_bar=True)
# os.environ['PINECONE_API_KEY'] = "pcsk_7VBb7V_3paXTh1gwNub2SstQ31RM4gADhhLRvzkWaqzymsGVBDsU34FciRNqRzg4bjqR6n"
os.getenv("PINECONE_API_KEY")

yaml=YAML()

# ----------------------------
# Load web pages into documents
# ----------------------------

pages_to_load = yaml.load(Path(PAGES_TO_INGEST_PATH))

# documents = []

# Initialize the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 500,
    chunk_overlap = 50
)

# Initizlize counter for number of pages to load
num_pages = len(pages_to_load["pages"])
print(f"Number of pages to load: {num_pages}")
pages_loaded = 0
chunks_loaded = 0

# Load the pages
for page in pages_to_load["pages"]:
    print(f"Loading {page}")
    loader = WebBaseLoader(
        web_path=page,
        header_template={"User-Agent": USER_AGENT}
    )
    document = loader.load()
    print("Document loaded.")
    print("Splitting documents into chunks.")
    split_doc = text_splitter.split_documents(document)
    num_chunks = len(split_doc)
    print(f"Split into {num_chunks} documents.")
    print("Saving document chunks into Pinecone.")
    vectorstore = PineconeVectorStore.from_documents(
        documents=split_doc,
        index_name=INDEX_NAME,
        embedding=embeddings_model,
    )
    print("Document chunks saved.")
    pages_loaded += 1
    chunks_loaded += num_chunks
    print(f"{pages_loaded} of {num_pages} pages loaded. Total of {chunks_loaded} chunks loaded.\n")
    
# ----------------------------
# Break up the documents into chunks
# ----------------------------
# print("\nSplitting documents into chunks")
# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size = 500,
#     chunk_overlap = 50
# )
# split_docs = text_splitter.split_documents(documents)

# print("Done splitting documents into chunks")

# ----------------------------
# Save to Database
# ----------------------------

# print("\nGenerate embeddings and save to Pinecone")

# pc.create_index(
#     name=INDEX_NAME,
#     dimension=2, # Replace with your model dimensions
#     metric="cosine", # Replace with your model metric
#     spec=ServerlessSpec(
#         cloud="aws",
#         region="us-east-1"
#     ) 
# )

# print(f"number of split documents: {len(split_docs)}\n")

# def split_list(input_list, chunk_size):
#     for i in range(0, len(input_list), chunk_size):
#         yield input_list[i:i + chunk_size]

# split_docs_chunked = split_list(split_docs, 1000)

# for split_docs_chunk in split_docs_chunked:
#     # vectorstore = Chroma.from_documents(
#     vectorstore = PineconeVectorStore.from_documents(
#         documents=split_docs_chunk,
#         index_name=INDEX_NAME,
#         embedding=embeddings_model,
#     )