import faiss
import numpy as np
import os
from typing import List, Dict, Any


class FaissManager:
    def __init__(self, dim: int, index_path: str | None = None):
        self.dim = dim
        self.index_path = index_path
        self.index = faiss.IndexFlatIP(dim)  # use inner product; we'll normalize embeddings
        self.id_to_meta: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0

    def add(self, embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        arr = np.array(embeddings, dtype="float32")
        # normalize rows
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1
        arr = arr / norms
        self.index.add(arr)
        for meta in metadatas:
            self.id_to_meta[self.next_id] = meta
            self.next_id += 1
        if self.index_path:
            self.save(self.index_path)

    def save(self, path: str):
        faiss.write_index(self.index, path)
        # save metadata next to it
        meta_path = path + ".meta.npy"
        np.save(meta_path, self.id_to_meta, allow_pickle=True)

    def load(self, path: str):
        if os.path.exists(path):
            self.index = faiss.read_index(path)
            meta_path = path + ".meta.npy"
            if os.path.exists(meta_path):
                self.id_to_meta = np.load(meta_path, allow_pickle=True).item()
                self.next_id = max(self.id_to_meta.keys()) + 1

    def query(self, query_embedding: List[float], top_k: int = 5):
        arr = np.array(query_embedding, dtype="float32").reshape(1, -1)
        # normalize
        arr = arr / np.linalg.norm(arr, axis=1, keepdims=True)
        D, I = self.index.search(arr, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            meta = self.id_to_meta.get(int(idx), {})
            results.append({"score": float(score), "metadata": meta})
        return results
