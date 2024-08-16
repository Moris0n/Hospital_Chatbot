import pandas as pd
import uuid
import dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore

# Load environment variables
dotenv.load_dotenv()

# File paths and other configurations
REVIEWS_CSV_PATH = "data/reviews.csv"
ELASTICSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "langchain_index"

# Load CSV data with pandas
df = pd.read_csv(REVIEWS_CSV_PATH)

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings()

# Configure ElasticsearchStore
elastic_vector_search = ElasticsearchStore(
    es_url=ELASTICSEARCH_URL,
    index_name=INDEX_NAME,
    embedding=embeddings,
    es_user="elastic",
    es_password="changeme"
)

# Function to create documents with UUID, content, and metadata
def create_document(row):
    return {
        "uuid": str(uuid.uuid4()),       # Generate a unique UUID
        "content": row["review"],        # Content from the CSV
        "metadata": {                    # Custom metadata
            "review_id": row["review_id"],
            "visit_id": row["visit_id"],
            "physician_name": row["physician_name"],
            "hospital_name": row["hospital_name"],
            "patient_name": row["patient_name"]
        }
    }

# Create a list of documents from the DataFrame
documents = [create_document(row) for _, row in df.iterrows()]

# Index documents in Elasticsearch
elastic_vector_search.add_documents(documents)

print("Documents have been indexed successfully.")
