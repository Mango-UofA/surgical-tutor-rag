import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/surgical_tutor")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index.index")

# Model name for BioClinicalBERT; if unavailable, adjust to a valid HF repo
BIOCLINICALBERT_MODEL = os.getenv("BIOCLINICALBERT_MODEL", "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext")
# Chunk target reduced to 400 to stay well under the 512 token limit of BERT models
CHUNK_TOKEN_TARGET = int(os.getenv("CHUNK_TOKEN_TARGET", 400))
