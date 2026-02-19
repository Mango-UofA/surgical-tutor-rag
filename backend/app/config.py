import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/surgical_tutor")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
# Use absolute path for FAISS index to avoid write permission issues on Windows
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "faiss_index.index"))

# Image storage configuration
IMAGE_STORAGE_PATH = os.getenv("IMAGE_STORAGE_PATH", "./uploaded_images")
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
MAX_SIMILAR_IMAGES = int(os.getenv("MAX_SIMILAR_IMAGES", "5"))

# Graph database configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
SCISPACY_MODEL = os.getenv("SCISPACY_MODEL", "en_core_sci_md")

# Model name for BioClinicalBERT; if unavailable, adjust to a valid HF repo
BIOCLINICALBERT_MODEL = os.getenv("BIOCLINICALBERT_MODEL", "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext")
# Chunk target reduced to 400 to stay well under the 512 token limit of BERT models
CHUNK_TOKEN_TARGET = int(os.getenv("CHUNK_TOKEN_TARGET", 400))
