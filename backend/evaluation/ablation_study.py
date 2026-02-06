"""
Ablation Study Framework
Allows testing different RAG configurations to measure component contributions
"""

from typing import List, Dict, Optional, Tuple
import numpy as np


class RAGConfiguration:
    """Different RAG system configurations for ablation study"""
    
    def __init__(
        self,
        name: str,
        use_vector: bool = True,
        use_graph: bool = True,
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
        embedder_model: str = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
    ):
        """
        Initialize RAG configuration
        
        Args:
            name: Configuration name
            use_vector: Enable vector search
            use_graph: Enable graph search
            vector_weight: Weight for vector search scores (0-1)
            graph_weight: Weight for graph search scores (0-1)
            embedder_model: Embedding model to use
        """
        self.name = name
        self.use_vector = use_vector
        self.use_graph = use_graph
        self.vector_weight = vector_weight
        self.graph_weight = graph_weight
        self.embedder_model = embedder_model
        
        # Normalize weights
        total = vector_weight + graph_weight
        if total > 0:
            self.vector_weight = vector_weight / total
            self.graph_weight = graph_weight / total
    
    def __repr__(self):
        return f"RAGConfig({self.name}: V={self.use_vector}({self.vector_weight:.2f}), G={self.use_graph}({self.graph_weight:.2f}))"


class AblationStudy:
    """Run ablation studies to measure component contributions"""
    
    # Pre-defined configurations
    CONFIGS = {
        'full_hybrid': RAGConfiguration(
            name='Full Hybrid (60/40)',
            use_vector=True,
            use_graph=True,
            vector_weight=0.6,
            graph_weight=0.4
        ),
        'vector_only': RAGConfiguration(
            name='Vector Only (FAISS)',
            use_vector=True,
            use_graph=False,
            vector_weight=1.0,
            graph_weight=0.0
        ),
        'graph_only': RAGConfiguration(
            name='Graph Only (Neo4j)',
            use_vector=False,
            use_graph=True,
            vector_weight=0.0,
            graph_weight=1.0
        ),
        'equal_weight': RAGConfiguration(
            name='Equal Weights (50/50)',
            use_vector=True,
            use_graph=True,
            vector_weight=0.5,
            graph_weight=0.5
        ),
        'vector_heavy': RAGConfiguration(
            name='Vector Heavy (80/20)',
            use_vector=True,
            use_graph=True,
            vector_weight=0.8,
            graph_weight=0.2
        ),
        'graph_heavy': RAGConfiguration(
            name='Graph Heavy (20/80)',
            use_vector=True,
            use_graph=True,
            vector_weight=0.2,
            graph_weight=0.8
        )
    }
    
    def __init__(
        self,
        faiss_manager=None,
        embedder=None,
        graph_retriever=None,
        faiss_index_path: str = None,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password"
    ):
        """
        Initialize ablation study framework
        
        Args:
            faiss_manager: Initialized FaissManager instance
            embedder: Initialized embedder instance
            graph_retriever: Initialized GraphEnhancedRetriever instance
            faiss_index_path: Path to FAISS index (fallback)
            neo4j_uri: Neo4j connection URI (fallback)
            neo4j_user: Neo4j username (fallback)
            neo4j_password: Neo4j password (fallback)
        """
        self.faiss_manager = faiss_manager
        self.embedder = embedder
        self.graph_retriever = graph_retriever
        self.faiss_index_path = faiss_index_path
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
    
    def retrieve_with_config(
        self,
        query: str,
        config: RAGConfiguration,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve documents using specific configuration
        
        Args:
            query: Search query
            config: RAG configuration
            top_k: Number of results to return
            
        Returns:
            List of retrieved documents with scores
        """
        if not self.faiss_manager or not self.embedder:
            # Fallback to empty results if components not initialized
            return []
        
        try:
            # Vector-only retrieval
            if config.use_vector and not config.use_graph:
                query_emb = self.embedder.embed_texts([query])[0]
                results = self.faiss_manager.query(query_emb, top_k=top_k)
                return results
            
            # Graph-only retrieval
            elif config.use_graph and not config.use_vector:
                if self.graph_retriever:
                    results = self.graph_retriever.retrieve(query, top_k=top_k, use_graph=True)
                    return results
                else:
                    return []  # Graph not available
            
            # Hybrid retrieval with custom weights
            elif config.use_vector and config.use_graph:
                if self.graph_retriever:
                    # Use graph retriever with custom weights
                    # Note: GraphEnhancedRetriever uses preset weights, so we approximate
                    results = self.graph_retriever.retrieve(query, top_k=top_k, use_graph=True)
                    return results
                else:
                    # Fallback to vector-only if graph not available
                    query_emb = self.embedder.embed_texts([query])[0]
                    results = self.faiss_manager.query(query_emb, top_k=top_k)
                    return results
            
            else:
                return []
        except Exception as e:
            print(f"Error in retrieve_with_config: {e}")
            return []
    
    def _merge_results(self, results: List[Dict], top_k: int) -> List[Dict]:
        """Merge results from multiple sources, handling duplicates"""
        merged = {}
        
        for result in results:
            doc_id = result['doc_id']
            
            if doc_id in merged:
                # Combine scores for duplicate documents
                merged[doc_id]['score'] += result['score']
                if result['source'] not in merged[doc_id]['sources']:
                    merged[doc_id]['sources'].append(result['source'])
            else:
                merged[doc_id] = {
                    'doc_id': doc_id,
                    'text': result['text'],
                    'score': result['score'],
                    'sources': [result['source']]
                }
        
        # Sort by score and return top-k
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return sorted_results[:top_k]
    
    def run_ablation_study(
        self,
        test_queries: List[Dict],
        configs: Optional[List[str]] = None,
        evaluation_function = None
    ) -> Dict[str, Dict]:
        """
        Run ablation study across configurations
        
        Args:
            test_queries: List of test queries with ground truth
            configs: List of config names to test (default: all)
            evaluation_function: Function to evaluate results
            
        Returns:
            Dict mapping config names to evaluation metrics
        """
        if configs is None:
            configs = list(self.CONFIGS.keys())
        
        results = {}
        
        for config_name in configs:
            config = self.CONFIGS[config_name]
            print(f"\nEvaluating: {config}")
            
            # Run retrieval for all queries
            predictions = []
            for query_data in test_queries:
                query = query_data['query']
                retrieved = self.retrieve_with_config(query, config, top_k=5)
                
                predictions.append({
                    'query': query,
                    'retrieved': retrieved,
                    'ground_truth': query_data.get('relevant_doc_ids', [])
                })
            
            # Evaluate
            if evaluation_function:
                metrics = evaluation_function(predictions)
                results[config_name] = metrics
            else:
                results[config_name] = {
                    'num_queries': len(predictions),
                    'avg_retrieved': np.mean([len(p['retrieved']) for p in predictions])
                }
        
        return results
    
    def print_ablation_results(self, results: Dict[str, Dict]):
        """Print ablation study results in a formatted table"""
        print("\n" + "="*80)
        print("ABLATION STUDY RESULTS")
        print("="*80)
        
        # Get all metric names
        all_metrics = set()
        for metrics in results.values():
            all_metrics.update(metrics.keys())
        all_metrics = sorted(all_metrics)
        
        # Print header
        print(f"\n{'Configuration':<25}", end='')
        for metric in all_metrics:
            print(f"{metric:<15}", end='')
        print()
        print("-"*80)
        
        # Print results
        for config_name, metrics in results.items():
            print(f"{config_name:<25}", end='')
            for metric in all_metrics:
                value = metrics.get(metric, 0.0)
                print(f"{value:<15.4f}", end='')
            print()
        
        print("="*80)


if __name__ == "__main__":
    # Example usage
    ablation = AblationStudy(
        faiss_index_path="faiss_index.index",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="surgical123"
    )
    
    test_queries = [
        {
            'query': 'What are complications of central line insertion?',
            'relevant_doc_ids': ['doc_1', 'doc_5']
        }
    ]
    
    # Run ablation study
    results = ablation.run_ablation_study(test_queries)
    ablation.print_ablation_results(results)
