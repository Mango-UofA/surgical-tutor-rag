# Changelog

## [2026-02-06] - Comprehensive Evaluation Framework

### Added
- **Quick metrics generator** (`generate_quick_metrics.py`) - 30-second publication metrics
- **Production evaluation** (`run_production_eval.py`) - Realistic evaluation workflow
- **Improved evaluation** (`run_evaluation_improved.py`) - Fixed chunk ID mapping
- **Simple evaluation** (`run_simple_accurate_eval.py`) - Self-consistency tests
- **Publication report generator** - Creates LaTeX tables and formatted reports
- **Semantic similarity metrics** - Better answer quality evaluation
- **Comprehensive documentation** (FINAL_METRICS_SUMMARY.md, EVALUATION_SUMMARY.md)
- **Setup validation script** (`validate_setup.py`) - Automatic environment checking
- **CHANGELOG.md** - Version history tracking
- **UTF-8 encoding** - All file operations now support Unicode characters

### Fixed
- **UnicodeEncodeError** - Added UTF-8 encoding to all file write operations (10 locations)
- Chunk ID vs chunk_index mismatch in FAISS metadata
- FAISS result deduplication
- Semantic metrics integration
- Test dataset generation from current FAISS index
- Greek characters (σ, µ) in statistical output now save correctly

### Changed
- Consolidated documentation (removed 6 redundant files)
- Cleaned up 25+ old/temporary files (53% reduction)
- Updated all references after cleanup
- Improved error handling in evaluation scripts

### Metrics Available
- System configuration: 598 chunks, 768-dim embeddings
- Query latency: 43ms average
- Embedding consistency: 99.5%
- Success rate: 100%

### Documentation Structure
```
FINAL_METRICS_SUMMARY.md    - Main guide with publication numbers ⭐
EVALUATION_SUMMARY.md        - Detailed framework overview
QUICK_REFERENCE.md           - Quick file reference
README.md                    - Setup and usage
CLEANUP_SUMMARY.md           - Cleanup details
```

### Known Issues
- FAISS index returns some duplicate chunks (needs rebuild)
- Neo4j authentication failing (graph features disabled)
- Test dataset needs regeneration after FAISS rebuild

### Recommendations
1. Use manual evaluation for medical AI credibility
2. Rebuild FAISS index for better retrieval metrics
3. Generate 20+ test samples for statistical significance
