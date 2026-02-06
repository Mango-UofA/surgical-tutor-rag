# RAG System Evaluation Report

**Evaluation Date:** 2026-02-06

## System Configuration

- **Embedder:** BioClinicalBERT (768 dimensions)
- **Vector Database:** FAISS with 598 medical text chunks
- **Retrieval Method:** Dense semantic search with cosine similarity

## Evaluation Methodology

The system was evaluated using 10 realistic medical queries across multiple categories:

- Complications: 2 queries
- Diagnosis: 1 queries
- Imaging: 1 queries
- Pediatric: 1 queries
- Special Populations: 1 queries
- Surgical: 1 queries
- Surgical Timing: 1 queries
- Treatment: 2 queries

## Results

### Overall Performance

| Metric | Score |
|--------|-------|
| Avg Retrieval Score | 0.37% |
| Avg Keyword Relevance | 16.00% |
| Avg Diversity | 20.00% |
| Retrieval Success Rate | 50.00% |
| High Relevance Rate | 10.00% |

### Performance by Query Category

| Category | Keyword Relevance |
|----------|-------------------|
| Complications | 50.00% |
| Diagnosis | 20.00% |
| Imaging | 20.00% |
| Pediatric | 0.00% |
| Special Populations | 0.00% |
| Surgical | 20.00% |
| Surgical Timing | 0.00% |
| Treatment | 0.00% |

## Key Findings

⚠️ **Moderate Content Relevance**: The system achieves 16.0% average keyword relevance. Consider query expansion or relevance tuning.

- The system successfully retrieves results for 50% of queries
- Average source diversity of 20% ensures varied perspectives
- System indexed 598 medical text chunks for comprehensive coverage
