"""
Improved Evaluation Runner - Fixes chunk ID mismatch and adds better metrics
This version uses the FAISS-based test dataset and properly handles chunk_index mapping
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np

# Add parent directory to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import RAG components
from modules.embedder.embedder import BioClinicalEmbedder
from modules.retriever.faiss_manager import FaissManager
from modules.generator.generator import Generator

# Import metrics
from metrics.retrieval_metrics import RetrievalMetrics
from metrics.qa_metrics import evaluate_qa
try:
    from metrics.semantic_metrics import evaluate_semantic_similarity
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False


class ImprovedEvaluator:
    """Enhanced evaluator with proper chunk mapping and semantic metrics"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize RAG components
        print("Initializing RAG components...")
        self.embedder = BioClinicalEmbedder('emilyalsentzer/Bio_ClinicalBERT')
        self.faiss = FaissManager(dim=768, index_path='../faiss_index.index')
        
        # Load FAISS index
        if Path('../faiss_index.index').exists():
            self.faiss.load('../faiss_index.index')
            print(f"✅ FAISS index loaded: {self.faiss.index.ntotal} vectors")
        else:
            print("⚠️  FAISS index not found!")
        
        # Initialize generator
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            self.generator = Generator(
                openai_api_key=api_key,
                base_url='https://openrouter.ai/api/v1',
                model='openai/gpt-4o'
            )
            print("✅ Generator initialized")
        else:
            self.generator = None
            print("⚠️  OpenRouter API key not found")
        
        self.results = {
            'experiment_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'timestamp': datetime.now().isoformat()
        }
    
    def load_faiss_test_data(self) -> List[Dict]:
        """Load test data generated from FAISS index"""
        test_file = Path('test_data/test_qa_pairs_from_faiss.json')
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return []
        
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        qa_pairs = data.get('qa_pairs', [])
        print(f"✅ Loaded {len(qa_pairs)} QA pairs from FAISS-based test set")
        
        # Show sample
        if qa_pairs:
            print(f"\nSample QA pair:")
            print(f"  Q: {qa_pairs[0]['question'][:100]}...")
            print(f"  A: {qa_pairs[0]['answer'][:100]}...")
            print(f"  FAISS Index: {qa_pairs[0].get('faiss_index')}")
        
        return qa_pairs
    
    def evaluate_retrieval_with_faiss_mapping(self, test_data: List[Dict]) -> Dict:
        """Evaluate retrieval using FAISS index positions"""
        print("\n" + "="*80)
        print("RETRIEVAL EVALUATION")
        print("="*80)
        
        metrics = RetrievalMetrics()
        k_values = [1, 3, 5, 10]
        
        all_results = {
            'per_k': {k: {'recall': [], 'precision': [], 'ndcg': []} for k in k_values},
            'mrr': [],
            'map': [],
            'avg_retrieved': []
        }
        
        for i, qa in enumerate(test_data):
            question = qa['question']
            faiss_index = qa.get('faiss_index')
            
            # Skip if no FAISS index
            if faiss_index is None:
                continue
            
            # Query FAISS
            try:
                query_emb = self.embedder.embed_texts([question])[0]
                # Do manual FAISS search to get actual indices
                arr = np.array(query_emb, dtype="float32").reshape(1, -1)
                arr = arr / np.linalg.norm(arr, axis=1, keepdims=True)
                D, I = self.faiss.index.search(arr, 10)
                
                # Get unique FAISS IDs
                retrieved_indices = []
                seen = set()
                for idx in I[0]:
                    if idx not in seen and idx >= 0:  # FAISS uses -1 for empty
                        retrieved_indices.append(int(idx))
                        seen.add(int(idx))
                
                all_results['avg_retrieved'].append(len(retrieved_indices))
                
                # Evaluate against ground truth FAISS index
                relevant_ids = [faiss_index]
                
                # Calculate metrics for each k
                for k in k_values:
                    recall = metrics.recall_at_k(retrieved_indices, relevant_ids, k)
                    precision = metrics.precision_at_k(retrieved_indices, relevant_ids, k)
                    ndcg = metrics.ndcg_at_k(retrieved_indices, relevant_ids, k)
                    
                    all_results['per_k'][k]['recall'].append(recall)
                    all_results['per_k'][k]['precision'].append(precision)
                    all_results['per_k'][k]['ndcg'].append(ndcg)
                
                # MRR and MAP
                mrr = metrics.mean_reciprocal_rank(retrieved_indices, relevant_ids)
                map_score = metrics.average_precision(retrieved_indices, relevant_ids)
                
                all_results['mrr'].append(mrr)
                all_results['map'].append(map_score)
                
                if i < 3:  # Show first 3 examples
                    print(f"\nExample {i+1}:")
                    print(f"  Question: {question[:80]}...")
                    print(f"  Ground truth index: {faiss_index}")
                    print(f"  Retrieved indices: {retrieved_indices[:5]}")
                    print(f"  Recall@5: {recall:.4f}")
                
            except Exception as e:
                print(f"  Error processing question {i+1}: {e}")
                continue
        
        # Calculate averages
        summary = {
            'avg_retrieved_docs': np.mean(all_results['avg_retrieved']) if all_results['avg_retrieved'] else 0,
            'mrr': np.mean(all_results['mrr']) if all_results['mrr'] else 0,
            'map': np.mean(all_results['map']) if all_results['map'] else 0
        }
        
        for k in k_values:
            summary[f'recall@{k}'] = np.mean(all_results['per_k'][k]['recall']) if all_results['per_k'][k]['recall'] else 0
            summary[f'precision@{k}'] = np.mean(all_results['per_k'][k]['precision']) if all_results['per_k'][k]['precision'] else 0
            summary[f'ndcg@{k}'] = np.mean(all_results['per_k'][k]['ndcg']) if all_results['per_k'][k]['ndcg'] else 0
        
        print(f"\n📊 RETRIEVAL RESULTS:")
        print(f"  Average docs retrieved: {summary['avg_retrieved_docs']:.2f}")
        print(f"  Recall@1:  {summary['recall@1']:.4f}")
        print(f"  Recall@5:  {summary['recall@5']:.4f}")
        print(f"  Recall@10: {summary['recall@10']:.4f}")
        print(f"  MRR:       {summary['mrr']:.4f}")
        print(f"  MAP:       {summary['map']:.4f}")
        
        return summary
    
    def evaluate_answer_quality(self, test_data: List[Dict]) -> Dict:
        """Evaluate answer generation quality"""
        print("\n" + "="*80)
        print("ANSWER QUALITY EVALUATION")
        print("="*80)
        
        if not self.generator:
            print("⚠️  Generator not available, skipping QA evaluation")
            return {}
        
        predictions = []
        
        for i, qa in enumerate(test_data[:10]):  # Evaluate first 10 to save API calls
            question = qa['question']
            reference = qa['answer']
            
            try:
                # Retrieve context
                query_emb = self.embedder.embed_texts([question])[0]
                contexts = self.faiss.query(query_emb, top_k=5)
                
                # Generate answer
                generated = self.generator.generate_answer(question, contexts, level="Advanced")
                
                predictions.append({
                    'prediction': generated,
                    'reference': reference
                })
                
                if i < 2:  # Show first 2 examples
                    print(f"\nExample {i+1}:")
                    print(f"  Question: {question[:80]}...")
                    print(f"  Reference: {reference[:100]}...")
                    print(f"  Generated: {generated[:100]}...")
                
            except Exception as e:
                print(f"  Error generating answer {i+1}: {e}")
                continue
        
        # Calculate metrics
        if predictions:
            # Traditional metrics
            results = evaluate_qa(predictions)
            
            # Add semantic metrics
            if HAS_SEMANTIC:
                semantic_results = evaluate_semantic_similarity(predictions)
                results.update(semantic_results)
                print(f"\n📊 QA RESULTS (with semantic similarity):")
            else:
                print(f"\n📊 QA RESULTS:")
            
            for metric, score in results.items():
                print(f"  {metric}: {score:.4f}")
            
            return results
        
        return {}
    
    def calculate_context_relevance(self, test_data: List[Dict]) -> Dict:
        """Calculate how relevant retrieved contexts are"""
        print("\n" + "="*80)
        print("CONTEXT RELEVANCE EVALUATION")
        print("="*80)
        
        relevance_scores = []
        
        for i, qa in enumerate(test_data[:10]):  # Sample 10
            question = qa['question']
            ground_truth_text = qa.get('chunk_text', '')
            
            try:
                # Retrieve top 5 contexts
                query_emb = self.embedder.embed_texts([question])[0]
                results = self.faiss.query(query_emb, top_k=5)
                
                # Check if any retrieved context contains similar content
                retrieved_texts = [r.get('metadata', {}).get('text', '') for r in results]
                
                # Simple keyword overlap metric
                question_words = set(question.lower().split())
                
                for text in retrieved_texts[:3]:  # Top 3
                    if text:
                        text_words = set(text.lower().split())
                        overlap = len(question_words & text_words) / len(question_words) if question_words else 0
                        relevance_scores.append(overlap)
                
            except Exception as e:
                print(f"  Error processing {i+1}: {e}")
                continue
        
        avg_relevance = np.mean(relevance_scores) if relevance_scores else 0
        
        print(f"\n📊 CONTEXT RELEVANCE:")
        print(f"  Average keyword overlap: {avg_relevance:.4f}")
        
        return {'avg_context_relevance': avg_relevance}
    
    def generate_report(self):
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f'evaluation_report_{timestamp}.txt'
        json_file = self.output_dir / f'evaluation_results_{timestamp}.json'
        
        # Write text report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("IMPROVED RAG SYSTEM EVALUATION REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Experiment ID: {self.results['experiment_id']}\n")
            f.write(f"Generated: {self.results['timestamp']}\n\n")
            
            for section, data in self.results.items():
                if section not in ['experiment_id', 'timestamp']:
                    f.write(f"\n{section.upper().replace('_', ' ')}\n")
                    f.write("-"*80 + "\n")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            f.write(f"{key}: {value:.4f}\n" if isinstance(value, float) else f"{key}: {value}\n")
                    else:
                        f.write(f"{data}\n")
        
        # Write JSON results
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Report saved to: {report_file}")
        print(f"✅ JSON results saved to: {json_file}")
    
    def run_full_evaluation(self):
        """Run complete evaluation pipeline"""
        print("\n" + "="*80)
        print("STARTING IMPROVED RAG EVALUATION")
        print("="*80)
        
        # Load test data
        test_data = self.load_faiss_test_data()
        
        if not test_data:
            print("❌ No test data available!")
            return
        
        self.results['dataset_stats'] = {
            'num_examples': len(test_data),
            'avg_question_length': np.mean([len(qa['question']) for qa in test_data]),
            'avg_answer_length': np.mean([len(qa['answer']) for qa in test_data])
        }
        
        # Run evaluations
        self.results['retrieval_metrics'] = self.evaluate_retrieval_with_faiss_mapping(test_data)
        self.results['qa_metrics'] = self.evaluate_answer_quality(test_data)
        self.results['context_relevance'] = self.calculate_context_relevance(test_data)
        
        # Generate report
        self.generate_report()
        
        print("\n" + "="*80)
        print("✅ EVALUATION COMPLETE!")
        print("="*80)


async def main():
    """Main entry point"""
    evaluator = ImprovedEvaluator()
    evaluator.run_full_evaluation()


if __name__ == "__main__":
    asyncio.run(main())
