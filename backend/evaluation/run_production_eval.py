"""
FINAL WORKING EVALUATION - Based on realistic use cases
Tests the system as it would actually be used in production
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import json
from datetime import datetime
from modules.embedder.embedder import BioClinicalEmbedder
from modules.retriever.faiss_manager import FaissManager

print("="*80)
print("PRODUCTION-REALISTIC RAG EVALUATION")
print("="*80)
print("\nThis evaluation tests the system as it would be used in practice:")
print("1. Can it retrieve relevant medical content for queries?")
print("2. Are the retrieved results semantically related to the query?")
print("3. Does it provide diverse results?")

# Initialize
print("\nInitializing RAG components...")
embedder = BioClinicalEmbedder('emilyalsentzer/Bio_ClinicalBERT')
faiss = FaissManager(dim=768, index_path='../faiss_index.index')
faiss.load('../faiss_index.index')

print(f"✅ FAISS index: {faiss.index.ntotal} vectors")
print(f"✅ Embedder: BioClinicalBERT (768 dim)")

# Define realistic medical queries based on the appendicitis domain
test_queries = [
    {
        'query': 'What are the diagnostic criteria for acute appendicitis?',
        'category': 'diagnosis',
        'expected_keywords': ['diagnosis', 'criteria', 'appendicitis', 'clinical', 'symptoms']
    },
    {
        'query': 'What are the complications of appendectomy?',
        'category': 'complications',
        'expected_keywords': ['complications', 'risks', 'appendectomy', 'surgical', 'infection']
    },
    {
        'query': 'What imaging modalities are recommended for diagnosing appendicitis?',
        'category': 'imaging',
        'expected_keywords': ['ultrasound', 'CT', 'MRI', 'imaging', 'diagnostic']
    },
    {
        'query': 'What is the role of ultrasound in pediatric appendicitis?',
        'category': 'pediatric',
        'expected_keywords': ['ultrasound', 'children', 'pediatric', 'diagnosis']
    },
    {
        'query': 'When should laparoscopic versus open appendectomy be performed?',
        'category': 'surgical',
        'expected_keywords': ['laparoscopic', 'open', 'appendectomy', 'surgical', 'approach']
    },
    {
        'query': 'What antibiotics are recommended for complicated appendicitis?',
        'category': 'treatment',
        'expected_keywords': ['antibiotics', 'treatment', 'complicated', 'infection']
    },
    {
        'query': 'What is the success rate of non-operative management for appendicitis?',
        'category': 'treatment',
        'expected_keywords': ['non-operative', 'conservative', 'management', 'success']
    },
    {
        'query': 'What are the advantages of laparoscopic appendectomy in pregnancy?',
        'category': 'special_populations',
        'expected_keywords': ['laparoscopic', 'pregnancy', 'pregnant', 'benefits']
    },
    {
        'query': 'What is the optimal timing for appendectomy?',
        'category': 'surgical_timing',
        'expected_keywords': ['timing', 'delay', 'emergency', 'hours']
    },
    {
        'query': 'How should appendiceal phlegmon be managed?',
        'category': 'complications',
        'expected_keywords': ['phlegmon', 'abscess', 'management', 'treatment']
    }
]

print(f"\n✅ Testing with {len(test_queries)} realistic medical queries")

# Run evaluation
results = {
    'experiment_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
    'timestamp': datetime.now().isoformat(),
    'faiss_index_size': faiss.index.ntotal,
    'num_queries': len(test_queries),
    'query_results': []
}

print("\n" + "="*80)
print("EVALUATION RESULTS")
print("="*80)

retrieval_scores = []
keyword_match_scores = []
diversity_scores = []

for i, test in enumerate(test_queries):
    query = test['query']
    expected_keywords = test['expected_keywords']
    
    print(f"\n{'─'*80}")
    print(f"Query {i+1}: {query}")
    print(f"Category: {test['category']}")
    
    # Query FAISS
    query_emb = embedder.embed_texts([query])[0]
    retrieved = faiss.query(query_emb, top_k=5)
    
    # Calculate metrics
    retrieved_texts = []
    keyword_matches = []
    sources = []
    
    for j, result in enumerate(retrieved):
        meta = result.get('metadata', {})
        text = meta.get('text', '').lower()
        source = meta.get('source', '')
        score = result.get('score', 0)
        
        retrieved_texts.append(text)
        sources.append(source)
        
        # Check keyword presence
        matches = sum(1 for kw in expected_keywords if kw.lower() in text)
        keyword_matches.append(matches)
        
        if j < 2:  # Show top 2
            print(f"\n  Result {j+1} (score: {score:.4f}):")
            print(f"    Source: {source}")
            print(f"    Text: {text[:150]}...")
            print(f"    Keyword matches: {matches}/{len(expected_keywords)}")
    
    # Calculate query-level metrics
    avg_retrieval_score = np.mean([r.get('score', 0) for r in retrieved])
    avg_keyword_match = np.mean(keyword_matches) / len(expected_keywords) if expected_keywords else 0
    result_diversity = len(set(sources)) / len(sources) if sources else 0
    
    retrieval_scores.append(avg_retrieval_score)
    keyword_match_scores.append(avg_keyword_match)
    diversity_scores.append(result_diversity)
    
    print(f"\n  📊 Metrics:")
    print(f"    Avg retrieval score: {avg_retrieval_score:.4f}")
    print(f"    Keyword relevance: {avg_keyword_match:.2%}")
    print(f"    Source diversity: {result_diversity:.2%}")
    
    results['query_results'].append({
        'query': query,
        'category': test['category'],
        'avg_score': float(avg_retrieval_score),
        'keyword_relevance': float(avg_keyword_match),
        'diversity': float(result_diversity),
        'num_results': len(retrieved)
    })

# Calculate overall metrics
results['overall_metrics'] = {
    'avg_retrieval_score': float(np.mean(retrieval_scores)),
    'avg_keyword_relevance': float(np.mean(keyword_match_scores)),
    'avg_diversity': float(np.mean(diversity_scores)),
    'retrieval_success_rate': float(np.mean([1.0 if s > 0 else 0.0 for s in retrieval_scores])),
    'high_relevance_rate': float(np.mean([1.0 if s > 0.3 else 0.0 for s in keyword_match_scores]))
}

# Print summary
print("\n" + "="*80)
print("OVERALL RESULTS")
print("="*80)

print(f"\n📊 RETRIEVAL PERFORMANCE:")
print(f"  Average retrieval score: {results['overall_metrics']['avg_retrieval_score']:.4f}")
print(f"  Retrieval success rate: {results['overall_metrics']['retrieval_success_rate']:.2%}")
print(f"  (% of queries that retrieved results)")

print(f"\n📊 CONTENT RELEVANCE:")
print(f"  Average keyword relevance: {results['overall_metrics']['avg_keyword_relevance']:.2%}")
print(f"  High relevance rate: {results['overall_metrics']['high_relevance_rate']:.2%}")
print(f"  (% of queries with >30% keyword match)")

print(f"\n📊 RESULT DIVERSITY:")
print(f"  Average source diversity: {results['overall_metrics']['avg_diversity']:.2%}")
print(f"  (% unique sources in top-5 results)")

# Category breakdown
print(f"\n📊 PERFORMANCE BY CATEGORY:")
category_stats = {}
for qr in results['query_results']:
    cat = qr['category']
    if cat not in category_stats:
        category_stats[cat] = []
    category_stats[cat].append(qr['keyword_relevance'])

for cat, scores in sorted(category_stats.items()):
    avg = np.mean(scores)
    print(f"  {cat:25s}: {avg:.2%} relevance")

# Save results
output_dir = Path('results')
output_dir.mkdir(exist_ok=True)

timestamp = results['experiment_id']
json_file = output_dir / f'production_evaluation_{timestamp}.json'
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Generate text report
report_file = output_dir / f'production_evaluation_{timestamp}.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("PRODUCTION-REALISTIC RAG EVALUATION REPORT\n")
    f.write("="*80 + "\n\n")
    f.write(f"Experiment ID: {timestamp}\n")
    f.write(f"Generated: {results['timestamp']}\n")
    f.write(f"FAISS Index Size: {faiss.index.ntotal} vectors\n")
    f.write(f"Number of Test Queries: {len(test_queries)}\n\n")
    
    f.write("OVERALL METRICS\n")
    f.write("-"*80 + "\n")
    for metric, value in results['overall_metrics'].items():
        f.write(f"{metric}: {value:.4f}\n")
    
    f.write("\n\nPER-QUERY RESULTS\n")
    f.write("-"*80 + "\n")
    for qr in results['query_results']:
        f.write(f"\nQuery: {qr['query']}\n")
        f.write(f"  Category: {qr['category']}\n")
        f.write(f"  Retrieval Score: {qr['avg_score']:.4f}\n")
        f.write(f"  Keyword Relevance: {qr['keyword_relevance']:.2%}\n")
        f.write(f"  Diversity: {qr['diversity']:.2%}\n")

# Generate markdown for publication
md_file = output_dir / f'production_evaluation_{timestamp}.md'
with open(md_file, 'w', encoding='utf-8') as f:
    f.write("# RAG System Evaluation Report\n\n")
    f.write(f"**Evaluation Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n")
    
    f.write("## System Configuration\n\n")
    f.write(f"- **Embedder:** BioClinicalBERT (768 dimensions)\n")
    f.write(f"- **Vector Database:** FAISS with {faiss.index.ntotal} medical text chunks\n")
    f.write(f"- **Retrieval Method:** Dense semantic search with cosine similarity\n\n")
    
    f.write("## Evaluation Methodology\n\n")
    f.write(f"The system was evaluated using {len(test_queries)} realistic medical queries across multiple categories:\n\n")
    for cat in sorted(set(qr['category'] for qr in results['query_results'])):
        count = len([qr for qr in results['query_results'] if qr['category'] == cat])
        f.write(f"- {cat.replace('_', ' ').title()}: {count} queries\n")
    
    f.write("\n## Results\n\n")
    f.write("### Overall Performance\n\n")
    f.write("| Metric | Score |\n")
    f.write("|--------|-------|\n")
    for metric, value in results['overall_metrics'].items():
        metric_name = metric.replace('_', ' ').title()
        f.write(f"| {metric_name} | {value:.2%} |\n")
    
    f.write("\n### Performance by Query Category\n\n")
    f.write("| Category | Keyword Relevance |\n")
    f.write("|----------|-------------------|\n")
    for cat, scores in sorted(category_stats.items()):
        avg = np.mean(scores)
        cat_name = cat.replace('_', ' ').title()
        f.write(f"| {cat_name} | {avg:.2%} |\n")
    
    f.write("\n## Key Findings\n\n")
    
    avg_rel = results['overall_metrics']['avg_keyword_relevance']
    if avg_rel > 0.4:
        f.write(f"✅ **Strong Content Relevance**: The system achieves {avg_rel:.1%} average keyword relevance, indicating that retrieved content is highly relevant to queries.\n\n")
    elif avg_rel > 0.25:
        f.write(f"✓ **Good Content Relevance**: The system achieves {avg_rel:.1%} average keyword relevance, showing good matching of query intent.\n\n")
    else:
        f.write(f"⚠️ **Moderate Content Relevance**: The system achieves {avg_rel:.1%} average keyword relevance. Consider query expansion or relevance tuning.\n\n")
    
    f.write(f"- The system successfully retrieves results for {results['overall_metrics']['retrieval_success_rate']:.0%} of queries\n")
    f.write(f"- Average source diversity of {results['overall_metrics']['avg_diversity']:.0%} ensures varied perspectives\n")
    f.write(f"- System indexed {faiss.index.ntotal} medical text chunks for comprehensive coverage\n")

print(f"\n✅ Results saved:")
print(f"  JSON: {json_file}")
print(f"  Report: {report_file}")
print(f"  Markdown: {md_file}")

print("\n" + "="*80)
print("✅ EVALUATION COMPLETE!")
print("="*80)
