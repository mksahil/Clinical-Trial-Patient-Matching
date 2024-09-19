from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from qdrant_client import QdrantClient, models
from qdrant_client.http import exceptions
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_community.embeddings import FakeEmbeddings
embeddings = FakeEmbeddings(size=384)

qdrant_api_key = "ECvLB3zfrjse7K3MxaHbUFVXtApMZXFQx89_peQliaO4_N8nvXvO6Q"
qdrant_url = "https://829608f5-f58f-4547-b652-a824a3237a6f.us-east4-0.gcp.cloud.qdrant.io:6333"
collection_name = "WebsitesForRAG"
# embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
    timeout=600  # Increase timeout duration to 10 minutes
)

vector_store = Qdrant(
    client=client,
    collection_name=collection_name,
    embeddings=embeddings
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=20, 
    length_function=len
)

def create_collection(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
    )
    print(f"Collection {collection_name} created successfully")

def upload_website_to_collection(url: str, batch_size: int = 10):
    if not client.collection_exists(collection_name=collection_name):
        create_collection(collection_name)     
    loader = WebBaseLoader(url)
    docs = loader.load_and_split(text_splitter)
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        for doc in batch:
            doc.metadata = {"source_url": url}
        try:  
            vector_store.add_documents(batch)  
        except exceptions.ResponseHandlingException as e:
            print(f"Failed to upload batch {i//batch_size + 1}: {e}")
            continue
    print(f"Successfully uploaded {len(docs)} documents to collection {collection_name} from {url}") 
    return f"Successfully uploaded {len(docs)} documents to collection {collection_name} from {url}"

# create_collection(collection_name)
# upload_website_to_collection("https://www.analyticsvidhya.com/blog/2023/09/retrieval-augmented-generation-rag-in-ai/")
