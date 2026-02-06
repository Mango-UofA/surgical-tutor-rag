"""
Generate NEW test dataset from current FAISS index with proper IDs
This ensures ground truth indices match the current FAISS state
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.embedder.embedder import BioClinicalEmbedder
from modules.retriever.faiss_manager import FaissManager
from modules.generator.generator import Generator
import json
import os
import random
from datetime import datetime

print("Loading RAG components...")
embedder = BioClinicalEmbedder('emilyalsentzer/Bio_ClinicalBERT')
faiss = FaissManager(dim=768, index_path='../faiss_index.index')
faiss.load('../faiss_index.index')

api_key = os.getenv('OPENROUTER_API_KEY')
if api_key:
    generator = Generator(
        openai_api_key=api_key,
        base_url='https://openrouter.ai/api/v1',
        model='openai/gpt-4o'
    )
    print("✅ Generator initialized")
else:
    generator = None
    print("⚠️  OpenRouter API key not found - will create simple QA pairs")

print(f"\nFAISS index: {faiss.index.ntotal} vectors")
print(f"Metadata: {len(faiss.id_to_meta)} entries")

# Sample random chunks for test set
num_test_samples = 20
faiss_indices = random.sample(range(len(faiss.id_to_meta)), min(num_test_samples, len(faiss.id_to_meta)))

print(f"\nGenerating {len(faiss_indices)} test QA pairs...")

qa_pairs = []

for i, faiss_id in enumerate(faiss_indices):
    meta = faiss.id_to_meta[faiss_id]
    chunk_text = meta.get('text', '')
    source = meta.get('source', '')
    chunk_index = meta.get('chunk_index')
    
    if not chunk_text or len(chunk_text) < 50:
        continue
    
    print(f"\n{i+1}/{len(faiss_indices)} - FAISS ID: {faiss_id}, chunk_index: {chunk_index}")
    print(f"  Source: {source}")
    print(f"  Text: {chunk_text[:100]}...")
    
    # Create QA pair
    if generator:
        try:
            # Generate question using GPT-4
            prompt = f"""Based on this medical text excerpt, generate ONE specific factual question that can be answered using ONLY the information in this text.

Text:
{chunk_text}

Generate a question that:
- Is specific and answerable from this text alone
- Tests medical knowledge
- Is clear and unambiguous

Return ONLY the question, nothing else."""
            
            question = generator.client.chat.completions.create(
                model=generator.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            ).choices[0].message.content.strip()
            
            # Generate answer
            answer_prompt = f"""Answer this question using ONLY the information in the provided text. Be concise and accurate.

Question: {question}

Text:
{chunk_text}

Answer:"""
            
            answer = generator.client.chat.completions.create(
                model=generator.model,
                messages=[{"role": "user", "content": answer_prompt}],
                max_tokens=150,
                temperature=0.3
            ).choices[0].message.content.strip()
            
        except Exception as e:
            print(f"  Error generating QA: {e}")
            # Fallback to simple QA
            question = f"What information is provided about {source.replace('.pdf', '')}?"
            answer = chunk_text[:200]
    else:
        # Simple QA without API
        question = f"What medical information is discussed in this excerpt from {source.replace('.pdf', '')}?"
        answer = chunk_text[:200] + "..."
    
    qa_pairs.append({
        "question": question,
        "answer": answer,
        "faiss_id": faiss_id,  # The actual FAISS ID
        "chunk_index": chunk_index,  # The chunk index from metadata
        "source": source,
        "chunk_text": chunk_text[:500]  # Store first 500 chars for reference
    })
    
    print(f"  Q: {question[:80]}...")
    print(f"  A: {answer[:80]}...")

# Save dataset
output = {
    "version": "2.0",
    "created_at": datetime.now().isoformat(),
    "num_examples": len(qa_pairs),
    "faiss_total_vectors": faiss.index.ntotal,
    "metadata": {
        "description": "Test QA pairs with correct FAISS IDs from current index",
        "generator": "GPT-4o" if generator else "Manual"
    },
    "qa_pairs": qa_pairs
}

output_file = Path('test_data/test_qa_pairs_current_faiss.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved {len(qa_pairs)} QA pairs to: {output_file}")

# Verify by doing a test retrieval
print("\n" + "="*80)
print("VERIFICATION TEST")
print("="*80)

if qa_pairs:
    test_qa = qa_pairs[0]
    print(f"\nTest Question: {test_qa['question']}")
    print(f"Ground truth FAISS ID: {test_qa['faiss_id']}")
    
    # Query
    query_emb = embedder.embed_texts([test_qa['question']])[0]
    import numpy as np
    arr = np.array(query_emb, dtype="float32").reshape(1, -1)
    arr = arr / np.linalg.norm(arr, axis=1, keepdims=True)
    D, I = faiss.index.search(arr, 10)
    
    print(f"\nTop 10 retrieved FAISS IDs: {I[0].tolist()}")
    print(f"Ground truth in results: {test_qa['faiss_id'] in I[0]}")
    
    if test_qa['faiss_id'] in I[0]:
        rank = list(I[0]).index(test_qa['faiss_id']) + 1
        print(f"✅ Ground truth found at rank {rank}")
    else:
        print(f"❌ Ground truth NOT in top 10 (this is OK for newly generated questions)")
