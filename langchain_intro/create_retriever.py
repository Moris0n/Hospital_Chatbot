import pandas as pd
from uuid import uuid4

from langchain_elasticsearch import ElasticsearchStore
from langchain_core.documents import Document
from elasticsearch import Elasticsearch

import os
import dotenv
import sentence_transformers

dotenv.load_dotenv(encoding='utf-8')

# File paths and other configurations
REVIEWS_CSV_PATH = "data/reviews.csv"
ELASTICSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "reviews_index"

# Delete the index if exists
# Initialize Elasticsearch client
es_client = Elasticsearch(
    hosts=[ELASTICSEARCH_URL],  
    http_auth=("elastic", "changeme")  
)

# Check if the index exists, and delete it if it does
es_client.indices.delete(index=INDEX_NAME, ignore_unavailable=True)

# Load CSV data with pandas, ensuring UTF-8 encoding
df = pd.read_csv(REVIEWS_CSV_PATH, encoding='utf-8')

# Configure ElasticsearchStore (OpenAI embedding is too big )
elastic_vector_search = ElasticsearchStore(
    es_url=ELASTICSEARCH_URL,
    index_name=INDEX_NAME,
    es_user="elastic",
    es_password="changeme",
    strategy=ElasticsearchStore.ApproxRetrievalStrategy(
        query_model_id="sentence-transformers/all-MiniLM-L6-v2"
    ),
)

# Function to create documents with UUID, content, and metadata
def create_documents(df):
    # Create Document objects
    documents = []
    uuids = []

    for _, row in df.iterrows():
        doc_id = str(uuid4())
        documents.append(Document(
            page_content=row["review"],  # Use the "review" column for content
            metadata={
                "review_id": row["review_id"],
                "visit_id": row["visit_id"],
                "physician_name": row["physician_name"],
                "hospital_name": row["hospital_name"],
                "patient_name": row["patient_name"]
            }
        ))
        uuids.append(doc_id)

    return documents, uuids

# Create a list of documents from the DataFrame
documents, uuids = create_documents(df)

try:
    elastic_vector_search.add_documents(documents=documents, ids=uuids,)
    print("Documents have been indexed successfully.")
except Exception as e:
    print(f"An error occurred: {e}")

