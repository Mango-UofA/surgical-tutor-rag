from typing import List
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch


class BioClinicalEmbedder:
    """Creates embeddings using a BioClinicalBERT-style model with mean pooling.

    Notes:
    - This uses huggingface AutoModel and AutoTokenizer.
    - Embedding dimension depends on the model (often 768).
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.eval()
        if torch.cuda.is_available():
            self.model.to("cuda")

    def embed_texts(self, texts: List[str], batch_size: int = 8) -> List[List[float]]:
        embeddings = []
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                # Explicitly set max_length=512 for proper truncation
                enc = self.tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt")
                if torch.cuda.is_available():
                    enc = {k: v.to("cuda") for k, v in enc.items()}
                    self.model.to("cuda")
                out = self.model(**enc)
                # mean pooling over token dim (take attention mask into account)
                last_hidden = out.last_hidden_state
                attention_mask = enc["attention_mask"].unsqueeze(-1)
                masked = last_hidden * attention_mask
                summed = masked.sum(1)
                counts = attention_mask.sum(1).clamp(min=1e-9)
                mean_pooled = summed / counts
                emb = mean_pooled.cpu().numpy()
                for v in emb:
                    embeddings.append(v.tolist())
        return embeddings

    def dim(self) -> int:
        # return hidden size
        return self.model.config.hidden_size
