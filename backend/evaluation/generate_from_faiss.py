"""
Generate evaluation test dataset from actual FAISS index
This ensures chunk IDs match what's in your vector database
"""

import sys
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.embedder.embedder import BioClinicalEmbedder
from modules.retriever.faiss_manager import FaissManager
from modules.generator.generator import Generator


def generate_test_dataset_from_faiss(
    faiss_index_path: str = "../faiss_index.index",
    num_samples: int = 10,
    output_file: str = "test_data/test_qa_pairs_from_faiss.json"
):
    """
    Generate test QA pairs from existing FAISS index
    
    This creates a test dataset where chunk IDs match the actual
    FAISS index metadata, ensuring retrieval evaluation works correctly.
    """
    print("=" * 80)
    print("GENERATING TEST DATASET FROM FAISS INDEX")
    print("=" * 80)
    
    # Initialize components
    print("\n1. Initializing components...")
    embedder = BioClinicalEmbedder('emilyalsentzer/Bio_ClinicalBERT')
    faiss = FaissManager(dim=embedder.dim(), index_path=faiss_index_path)
    faiss.load(faiss_index_path)
    print(f"   Loaded FAISS index: {faiss.index.ntotal} vectors")
    
    # Initialize generator with OpenRouter API key
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY or OPENAI_API_KEY environment variable must be set")
    
    # Use OpenRouter base URL
    base_url = "https://openrouter.ai/api/v1"
    generator = Generator(openai_api_key=api_key, base_url=base_url, model="openai/gpt-4o")
    print(f"   Initialized GPT-4o generator (via OpenRouter)")
    
    # Sample chunks from FAISS
    print(f"\n2. Sampling {num_samples} chunks from index...")
    import random
    total_chunks = faiss.index.ntotal
    sampled_indices = random.sample(range(total_chunks), min(num_samples, total_chunks))
    
    qa_pairs = []
    
    for idx in sampled_indices:
        # Get metadata for this chunk
        if idx not in faiss.id_to_meta:
            print(f"   Skipping index {idx} (no metadata)")
            continue
            
        metadata = faiss.id_to_meta[idx]
        chunk_text = metadata.get('text', '')
        
        if not chunk_text or len(chunk_text) < 100:
            print(f"   Skipping index {idx} (text too short)")
            continue
        
        # Extract chunk identifier
        chunk_id = metadata.get('chunk_index')
        source = metadata.get('source', metadata.get('title', 'unknown'))
        
        print(f"\n   Processing chunk {idx} (chunk_index={chunk_id}, source={source[:50]}...)")
        print(f"   Text length: {len(chunk_text)} chars")
        
        # Generate QA pair using GPT-4o
        prompt = f"""Based on this medical/surgical text, generate a factual extractive question-answer pair.

Text:
{chunk_text[:1500]}

IMPORTANT: Generate a question that:
1. Uses specific terminology and key phrases from the text
2. Is directly answerable from the text (extractive, not abstractive)
3. Tests factual recall of surgical procedures, clinical guidelines, or medical facts
4. Includes at least 2-3 key terms from the original text

Generate a concise answer (1-2 sentences) using EXACT phrases from the text.

Respond in JSON format:
{{
    "question": "...",
    "answer": "..."
}}"""

        try:
            response = generator.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            
            qa_pairs.append({
                "question": result['question'],
                "answer": result['answer'],
                "chunk_id": chunk_id,  # Use chunk_index from FAISS
                "source": source,
                "faiss_index": idx
            })
            
            print(f"   [OK] Generated Q: {result['question'][:60]}...")
            print(f"   [OK] Generated A: {result['answer'][:60]}...")
            
        except Exception as e:
            print(f"   [ERROR] Error generating QA for chunk {idx}: {e}")
            continue
    
    # Save dataset
    print(f"\n3. Saving dataset...")
    output_path = Path(__file__).parent / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    dataset = {
        "qa_pairs": qa_pairs,
        "metadata": {
            "num_pairs": len(qa_pairs),
            "faiss_index_path": faiss_index_path,
            "total_faiss_vectors": total_chunks,
            "generated_date": "2026-01-29"
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"   [OK] Saved {len(qa_pairs)} QA pairs to: {output_path}")
    
    # Print statistics
    if len(qa_pairs) > 0:
        print(f"\n{'=' * 80}")
        print("DATASET STATISTICS")
        print(f"{'=' * 80}")
        print(f"Total QA pairs:        {len(qa_pairs)}")
        print(f"Avg question length:   {sum(len(qa['question']) for qa in qa_pairs) / len(qa_pairs):.1f} chars")
        print(f"Avg answer length:     {sum(len(qa['answer']) for qa in qa_pairs) / len(qa_pairs):.1f} chars")
        print(f"Unique sources:        {len(set(qa['source'] for qa in qa_pairs))}")
        print(f"\nReady for evaluation! Update config.json:")
        print(f'  "test_file": "{output_file}"')
        print(f"{'=' * 80}")
    else:
        print("\n[WARNING] No QA pairs generated. Check API key and error messages above.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate test dataset from FAISS index")
    parser.add_argument("--num-samples", type=int, default=10, help="Number of QA pairs to generate")
    parser.add_argument("--output", type=str, default="test_data/test_qa_pairs_from_faiss.json", 
                       help="Output file path")
    
    args = parser.parse_args()
    
    generate_test_dataset_from_faiss(
        num_samples=args.num_samples,
        output_file=args.output
    )
