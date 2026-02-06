"""
Diagnostic script to understand FAISS index structure and test retrieval
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.embedder.embedder import BioClinicalEmbedder
from modules.retriever.faiss_manager import FaissManager
import json

print("Loading RAG components...")
embedder = BioClinicalEmbedder('emilyalsentzer/Bio_ClinicalBERT')
faiss = FaissManager(dim=768, index_path='../faiss_index.index')
faiss.load('../faiss_index.index')

print(f"\nFAISS index size: {faiss.index.ntotal} vectors")
print(f"Metadata size: {len(faiss.id_to_meta)} entries")

# Show first few metadata entries
print("\nFirst 5 metadata entries:")
for i in range(min(5, len(faiss.id_to_meta))):
    meta = faiss.id_to_meta.get(i, {})
    print(f"\nIndex {i}:")
    print(f"  chunk_index: {meta.get('chunk_index')}")
    print(f"  source: {meta.get('source', 'N/A')}")
    print(f"  text: {meta.get('text', '')[:100]}...")

# Test retrieval
print("\n" + "="*80)
print("Testing Retrieval")
print("="*80)

test_questions = [
    "What are the advantages of laparoscopic appendectomy compared to open appendectomy in pregnant patients?",
    "What is the diagnostic performance of ultrasound for appendicitis?",
    "What are complications of appendectomy?"
]

for q in test_questions:
    print(f"\nQuestion: {q[:80]}...")
    
    query_emb = embedder.embed_texts([q])[0]
    results = faiss.query(query_emb, top_k=10)
    
    print(f"Retrieved {len(results)} results:")
    for i, r in enumerate(results):
        meta = r.get('metadata', {})
        print(f"  {i+1}. Score: {r['score']:.4f}, chunk_index: {meta.get('chunk_index')}, source: {meta.get('source', 'N/A')[:30]}")
        print(f"     Text: {meta.get('text', '')[:80]}...")

print("\n" + "="*80)

# Check for specific indices from test set
test_indices = [236, 121, 14, 60, 33]
print(f"\nChecking specific test indices: {test_indices}")
for idx in test_indices:
    if idx in faiss.id_to_meta:
        meta = faiss.id_to_meta[idx]
        print(f"\nFAISS index {idx} exists:")
        print(f"  chunk_index: {meta.get('chunk_index')}")
        print(f"  source: {meta.get('source')}")
        print(f"  text: {meta.get('text', '')[:100]}...")
    else:
        print(f"\n❌ FAISS index {idx} NOT FOUND in metadata!")

print(f"\n\nTotal FAISS vectors: {faiss.index.ntotal}")
print(f"Total metadata entries: {len(faiss.id_to_meta)}")
print(f"Max metadata key: {max(faiss.id_to_meta.keys()) if faiss.id_to_meta else 0}")
