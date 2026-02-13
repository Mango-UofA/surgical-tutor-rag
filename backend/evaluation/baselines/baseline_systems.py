"""
Baseline Comparison Systems
Implements various baseline RAG configurations for comparison
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional
import numpy as np
from rank_bm25 import BM25Okapi
import aiohttp


class BM25Retriever:
    """BM25 lexical retrieval baseline"""
    
    def __init__(self, documents: List[Dict]):
        """
        Initialize BM25 retriever
        
        Args:
            documents: List of dicts with 'id', 'text' keys
        """
        self.documents = documents
        self.doc_ids = [doc['id'] for doc in documents]
        
        # Tokenize documents
        tokenized_docs = [doc['text'].lower().split() for doc in documents]
        
        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_docs)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search using BM25
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of retrieved documents with scores
        """
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'doc_id': self.doc_ids[idx],
                'text': self.documents[idx]['text'],
                'score': float(scores[idx]),
                'method': 'bm25'
            })
        
        return results


class OpenAIEmbeddingRetriever:
    """OpenAI embeddings baseline (general-purpose)"""
    
    def __init__(
        self,
        documents: List[Dict],
        api_key: str,
        model: str = "text-embedding-3-small"
    ):
        """
        Initialize OpenAI embedding retriever
        
        Args:
            documents: List of dicts with 'id', 'text' keys
            api_key: OpenRouter API key
            model: Embedding model name
        """
        self.documents = documents
        self.doc_ids = [doc['id'] for doc in documents]
        self.api_key = api_key
        self.model = model
        self.embeddings = None
    
    async def build_index(self):
        """Build embedding index for all documents"""
        import aiohttp
        
        embeddings = []
        
        async with aiohttp.ClientSession() as session:
            for doc in self.documents:
                embedding = await self._get_embedding(session, doc['text'])
                embeddings.append(embedding)
        
        self.embeddings = np.array(embeddings)
    
    async def _get_embedding(self, session: aiohttp.ClientSession, text: str) -> np.ndarray:
        """Get embedding for text"""
        async with session.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "input": text
            }
        ) as resp:
            result = await resp.json()
            return np.array(result['data'][0]['embedding'])
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search using OpenAI embeddings
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of retrieved documents with scores
        """
        if self.embeddings is None:
            await self.build_index()
        
        # Get query embedding
        async with aiohttp.ClientSession() as session:
            query_embedding = await self._get_embedding(session, query)
        
        # Compute cosine similarity
        scores = np.dot(self.embeddings, query_embedding)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'doc_id': self.doc_ids[idx],
                'text': self.documents[idx]['text'],
                'score': float(scores[idx]),
                'method': 'openai_embedding'
            })
        
        return results


class VanillaGPTBaseline:
    """GPT-4o without retrieval (no RAG)"""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4o"):
        """
        Initialize vanilla GPT baseline
        
        Args:
            api_key: OpenRouter API key
            model: LLM model name
        """
        self.api_key = api_key
        self.model = model
    
    async def answer_question(
        self,
        question: str,
        system_prompt: str = "You are a helpful surgical education assistant."
    ) -> str:
        """
        Answer question using LLM only (no retrieval)
        
        Args:
            question: User question
            system_prompt: System prompt
            
        Returns:
            Generated answer
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "temperature": 0.0
                }
            ) as resp:
                result = await resp.json()
                return result['choices'][0]['message']['content']


class DenseRetrievalBaseline:
    """Standard dense retrieval with general BERT"""
    
    def __init__(
        self,
        documents: List[Dict],
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize dense retrieval baseline
        
        Args:
            documents: List of dicts with 'id', 'text' keys
            model_name: Sentence transformer model
        """
        self.documents = documents
        self.doc_ids = [doc['id'] for doc in documents]
        self.embedder = Embedder(model_name=model_name)
        self.embeddings = None
    
    def build_index(self):
        """Build embedding index"""
        embeddings = []
        for doc in self.documents:
            embedding = self.embedder.embed_text(doc['text'])
            embeddings.append(embedding)
        
        self.embeddings = np.array(embeddings)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search using dense embeddings"""
        if self.embeddings is None:
            self.build_index()
        
        # Get query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Compute cosine similarity
        scores = np.dot(self.embeddings, query_embedding)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'doc_id': self.doc_ids[idx],
                'text': self.documents[idx]['text'],
                'score': float(scores[idx]),
                'method': 'dense_retrieval'
            })
        
        return results


def compare_baselines(
    test_queries: List[Dict],
    documents: List[Dict],
    api_key: str,
    evaluation_function
) -> Dict[str, Dict]:
    """
    Compare all baseline systems
    
    Args:
        test_queries: List of test queries with ground truth
        documents: Document corpus
        api_key: API key for external APIs
        evaluation_function: Function to evaluate results
        
    Returns:
        Dict mapping baseline names to metrics
    """
    results = {}
    
    # BM25 baseline
    print("Evaluating BM25 baseline...")
    bm25 = BM25Retriever(documents)
    bm25_predictions = []
    for query_data in test_queries:
        retrieved = bm25.search(query_data['query'], top_k=5)
        bm25_predictions.append({
            'query': query_data['query'],
            'retrieved': retrieved,
            'ground_truth': query_data.get('relevant_doc_ids', [])
        })
    results['BM25'] = evaluation_function(bm25_predictions)
    
    # Dense retrieval baseline
    print("Evaluating dense retrieval baseline...")
    dense = DenseRetrievalBaseline(documents)
    dense_predictions = []
    for query_data in test_queries:
        retrieved = dense.search(query_data['query'], top_k=5)
        dense_predictions.append({
            'query': query_data['query'],
            'retrieved': retrieved,
            'ground_truth': query_data.get('relevant_doc_ids', [])
        })
    results['Dense Retrieval (General BERT)'] = evaluation_function(dense_predictions)
    
    return results


if __name__ == "__main__":
    # Example usage
    test_docs = [
        {'id': 'doc_1', 'text': 'Central line insertion can cause pneumothorax.'},
        {'id': 'doc_2', 'text': 'Appendicitis requires surgical intervention.'}
    ]
    
    bm25 = BM25Retriever(test_docs)
    results = bm25.search('complications of central line', top_k=2)
    
    print("BM25 Results:")
    for r in results:
        print(f"  {r['doc_id']}: {r['score']:.4f}")
