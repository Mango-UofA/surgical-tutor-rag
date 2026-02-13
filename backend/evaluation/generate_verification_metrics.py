"""
Generate Verification Metrics for MICCAI Paper

Standalone script to measure verification, abstention, and hallucination metrics
without requiring full sciSpaCy installation.

"""


import sys
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import os
from dotenv import load_dotenv



# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


# Add parent directory to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))



from modules.graph.neo4j_manager import Neo4jManager
from modules.verification.verification_pipeline import VerificationPipeline
from modules.generator.generator import Generator
from modules.retriever.faiss_manager import FaissManager
from modules.embedder.embedder import BioClinicalEmbedder


def load_test_set(test_file: str = "test_data/validated_50plus_test_set.json") -> List[Dict]:
    """Load test QA pairs from JSON file."""
    test_path = Path(__file__).parent / test_file
    with open(test_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('qa_pairs', [])


def initialize_system():
    """Initialize all RAG system components."""
    print("\n[OK] Initializing RAG System Components...")
    
    # Neo4j
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        raise ValueError("Missing Neo4j credentials in .env file")
    
    neo4j_manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
    print("[OK] Neo4j connected")
    
    # OpenAI/OpenRouter
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("MODEL", "openai/gpt-4o")
    
    if not openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY in .env file")
    
    # FAISS
    faiss_manager = FaissManager(
        dim=768,  # BioClinicalBERT dimension
        index_path=str(Path(__file__).parent.parent / "faiss_index.index")
    )
    faiss_manager.load(str(Path(__file__).parent.parent / "faiss_index.index"))
    print("[OK] FAISS loaded")
    
    # Generator
    generator = Generator(openai_api_key, openai_base_url, model)
    print("[OK] Generator initialized")
    
    # Embedder
    embedder = BioClinicalEmbedder(model_name="emilyalsentzer/Bio_ClinicalBERT")
    print("[OK] Embedder initialized")
    
    # Verification Pipeline (with abstention & taxonomy)
    verification_pipeline = VerificationPipeline(
        neo4j_manager=neo4j_manager,
        api_key=openai_api_key,
        base_url=openai_base_url,
        model=model,
        abstention_threshold=0.5,
        enable_abstention=True
    )
    print("[OK] Verification Pipeline initialized")
    
    return {
        'neo4j': neo4j_manager,
        'faiss': faiss_manager,
        'generator': generator,
        'embedder': embedder,
        'verifier': verification_pipeline
    }


def generate_answer(query: str, faiss_manager, generator, embedder) -> str:
    """Generate answer for a query using RAG."""
    # Query FAISS using the query method
    query_emb = embedder.embed_texts([query])[0]
    results = faiss_manager.query(query_emb, top_k=5)
    
    # Format contexts for generator (expects list of dicts with metadata)
    contexts = []
    for r in results:
        # Results already have proper structure from FAISS
        contexts.append(r)
    
    # Use top 3 contexts
    contexts = contexts[:3]
    
    # Generate answer using the generator
    result = generator.generate_answer(
        query=query,
        contexts=contexts,
        level="Advanced",
        enable_verification=False,  # We'll verify separately
        use_surgical_cot=False  # Disable CoT for faster generation
    )
    
    # Extract answer text from result dict
    return result.get('answer', '')


def compute_verification_metrics(verification_results: List[Dict]) -> Dict:
    """Compute aggregate verification metrics."""
    if not verification_results:
        return {
            'avg_verification_score': 0.0,
            'avg_safety_score': 0.0,
            'avg_certainty': 0.0,
            'abstention_rate': 0.0,
            'total_hallucinations': 0,
            'high_confidence_count': 0,
            'low_confidence_count': 0,
            'high_confidence_verification': 0.0,
            'low_confidence_verification': 0.0
        }
    
    total = len(verification_results)
    
    # Average scores
    avg_verification = sum(r['verification_score'] for r in verification_results) / total
    avg_safety = sum(r.get('safety_score', 0) for r in verification_results) / total
    avg_certainty = sum(r.get('certainty', 0) for r in verification_results) / total
    
    # Abstention rate
    abstentions = sum(1 for r in verification_results 
                     if r.get('abstention_decision', {}).get('should_abstain', False))
    abstention_rate = abstentions / total
    
    # Hallucinations
    total_hallucinations = sum(
        r.get('hallucination_analysis', {}).get('total_errors', 0)
        for r in verification_results
    )
    
    # Confidence levels
    high_conf = [r for r in verification_results if r['confidence_level'] == 'high']
    low_conf = [r for r in verification_results if r['confidence_level'] == 'low']
    
    high_conf_verification = (sum(r['verification_score'] for r in high_conf) / len(high_conf)
                             if high_conf else 0.0)
    low_conf_verification = (sum(r['verification_score'] for r in low_conf) / len(low_conf)
                            if low_conf else 0.0)
    
    return {
        'avg_verification_score': avg_verification,
        'avg_safety_score': avg_safety,
        'avg_certainty': avg_certainty,
        'abstention_rate': abstention_rate,
        'abstention_count': f"{abstentions}/{total}",
        'total_hallucinations': total_hallucinations,
        'high_confidence_count': len(high_conf),
        'low_confidence_count': len(low_conf),
        'high_confidence_verification': high_conf_verification,
        'low_confidence_verification': low_conf_verification
    }


def generate_report_txt(test_results: List[Dict], metrics: Dict, output_file: str):
    """Generate human-readable TXT report."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("VERIFICATION METRICS REPORT FOR MICCAI SUBMISSION\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Test Set Size: {len(test_results)} QA pairs\n\n")
        
        # Overall Metrics
        f.write("-" * 80 + "\n")
        f.write("OVERALL METRICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Average Verification Score:    {metrics['avg_verification_score']*100:.2f}%\n")
        f.write(f"Average Safety Score:          {metrics['avg_safety_score']*100:.2f}/100\n")
        f.write(f"Average Certainty:             {metrics['avg_certainty']*100:.2f}%\n")
        f.write(f"Abstention Rate:               {metrics['abstention_rate']*100:.2f}% ({metrics['abstention_count']})\n")
        f.write(f"Total Hallucinations Detected: {metrics['total_hallucinations']}\n\n")
        
        # Confidence Distribution
        f.write("-" * 80 + "\n")
        f.write("CONFIDENCE DISTRIBUTION\n")
        f.write("-" * 80 + "\n")
        f.write(f"High Confidence Answers:       {metrics['high_confidence_count']} "
                f"({metrics['high_confidence_count']/len(test_results)*100:.1f}%)\n")
        f.write(f"  - Avg Verification:          {metrics['high_confidence_verification']*100:.2f}%\n")
        f.write(f"Low Confidence Answers:        {metrics['low_confidence_count']} "
                f"({metrics['low_confidence_count']/len(test_results)*100:.1f}%)\n")
        f.write(f"  - Avg Verification:          {metrics['low_confidence_verification']*100:.2f}%\n\n")
        
        # Sample Answers
        f.write("-" * 80 + "\n")
        f.write("SAMPLE VERIFICATION RESULTS (First 5 examples)\n")
        f.write("-" * 80 + "\n\n")
        
        for i, result in enumerate(test_results[:5], 1):
            f.write(f"\n[EXAMPLE {i}]\n")
            f.write(f"Question: {result['question'][:150]}...\n\n")
            f.write(f"Generated Answer: {result['generated_answer'][:200]}...\n\n")
            f.write(f"Verification Score:    {result['verification']['verification_score']*100:.2f}%\n")
            f.write(f"Confidence Level:      {result['verification']['confidence_level'].upper()}\n")
            f.write(f"Safety Score:          {result['verification'].get('safety_score', 0)*100:.0f}/100\n")
            
            abstention = result['verification'].get('abstention_decision', {})
            should_abstain = abstention.get('should_abstain', False)
            f.write(f"Abstention:            {'YES' if should_abstain else 'NO'}\n")
            
            if should_abstain:
                f.write(f"  Reason: {abstention.get('reason', 'N/A')}\n")
                f.write(f"  Strategy: {abstention.get('strategy', 'N/A')}\n")
            
            hallucinations = result['verification'].get('hallucination_analysis', {})
            f.write(f"Hallucinations:        {hallucinations.get('total_errors', 0)} detected\n")
            
            f.write("\n" + "-" * 80 + "\n")
        
        f.write("\n[OK] Report complete\n")


def generate_report_json(test_results: List[Dict], metrics: Dict, output_file: str):
    """Generate JSON report."""
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'test_set_size': len(test_results),
            'script_version': '2.0'
        },
        'metrics': metrics,
        'results': test_results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def generate_latex_table(metrics: Dict, output_file: str):
    """Generate LaTeX table for paper."""
    latex = r"""\begin{table}[h]
\centering
\caption{Verification and Safety Metrics}
\begin{tabular}{lc}
\toprule
\textbf{Metric} & \textbf{Value} \\
\midrule
Verification Score & """ + f"{metrics['avg_verification_score']*100:.2f}\\%" + r""" \\
Safety Score & """ + f"{metrics['avg_safety_score']:.2f}/100" + r""" \\
Abstention Rate & """ + f"{metrics['abstention_rate']*100:.2f}\\%" + r""" \\
Hallucinations Detected & """ + f"{metrics['total_hallucinations']}" + r""" \\
High Confidence & """ + f"{metrics['high_confidence_count']} ({metrics['high_confidence_count']/(metrics['high_confidence_count']+metrics['low_confidence_count'])*100:.1f}\\%)" + r""" \\
Low Confidence & """ + f"{metrics['low_confidence_count']} ({metrics['low_confidence_count']/(metrics['high_confidence_count']+metrics['low_confidence_count'])*100:.1f}\\%)" + r""" \\
\bottomrule
\end{tabular}
\label{tab:verification_metrics}
\end{table}
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex)


def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("VERIFICATION METRICS GENERATOR FOR MICCAI PAPER")
    print("=" * 80 + "\n")
    
    # Load test set
    print("[OK] Loading test dataset...")
    test_qa_pairs = load_test_set()
    print(f"[OK] Loaded {len(test_qa_pairs)} QA pairs\n")
    
    # Initialize system
    components = initialize_system()
    
    # Run verification on all test pairs
    print("\n[OK] Running verification on test set...")
    print("-" * 80)
    
    test_results = []
    
    for i, qa_pair in enumerate(test_qa_pairs, 1):
        question = qa_pair['question']
        expected_answer = qa_pair.get('answer', '')
        
        print(f"\n[{i}/{len(test_qa_pairs)}] Processing: {question[:80]}...")
        
        # Generate answer
        generated_answer = generate_answer(
            question, 
            components['faiss'], 
            components['generator'],
            components['embedder']
        )
        
        # Verify answer
        verification_result = components['verifier'].verify_answer(question, generated_answer)
        
        # Extract key metrics
        verification_score = verification_result['verification_score']
        confidence = verification_result['confidence_level']
        should_abstain = verification_result.get('abstention_decision', {}).get('should_abstain', False)
        
        print(f"  Verification: {verification_score*100:.2f}% | Confidence: {confidence.upper()} | "
              f"Abstention: {'YES' if should_abstain else 'NO'}")
        
        # Store results
        test_results.append({
            'question': question,
            'expected_answer': expected_answer,
            'generated_answer': generated_answer,
            'verification': verification_result
        })
    
    print("\n" + "-" * 80)
    print("[OK] Verification complete\n")
    
    # Compute aggregate metrics
    print("[OK] Computing aggregate metrics...")
    metrics = compute_verification_metrics([r['verification'] for r in test_results])
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY METRICS")
    print("=" * 80)
    print(f"Verification Score:        {metrics['avg_verification_score']*100:.2f}%")
    print(f"Safety Score:              {metrics['avg_safety_score']:.2f}/100")
    print(f"Abstention Rate:           {metrics['abstention_rate']*100:.2f}%")
    print(f"Hallucinations:            {metrics['total_hallucinations']}")
    print(f"High Confidence:           {metrics['high_confidence_count']} ({metrics['high_confidence_verification']*100:.2f}% verified)")
    print(f"Low Confidence:            {metrics['low_confidence_count']} ({metrics['low_confidence_verification']*100:.2f}% verified)")
    print("=" * 80 + "\n")
    
    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    txt_file = output_dir / f"verification_report_{timestamp}.txt"
    json_file = output_dir / f"verification_report_{timestamp}.json"
    latex_file = output_dir / f"verification_table_{timestamp}.tex"
    
    print("[OK] Generating reports...")
    generate_report_txt(test_results, metrics, str(txt_file))
    print(f"[OK] TXT report: {txt_file}")
    
    generate_report_json(test_results, metrics, str(json_file))
    print(f"[OK] JSON report: {json_file}")
    
    generate_latex_table(metrics, str(latex_file))
    print(f"[OK] LaTeX table: {latex_file}")
    
    print("\n[OK] All reports generated successfully!\n")
    
    # Cleanup
    components['neo4j'].close()
    print("[OK] Neo4j connection closed")
    print("\n" + "=" * 80)
    print("VERIFICATION METRICS GENERATION COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
