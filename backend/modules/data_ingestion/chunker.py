from typing import List


def simple_chunk_text(text: str, approx_tokens: int = 400) -> List[str]:
    """
    Simple whitespace-based chunker that aims for approx_tokens tokens per chunk.
    This is an approximation: tokens ~ words for English.
    We use 400 as default to stay well under the 512 token limit of BERT models.
    """
    words = text.split()
    chunks = []
    i = 0
    n = len(words)
    while i < n:
        j = min(n, i + approx_tokens)
        chunk = " ".join(words[i:j])
        chunks.append(chunk)
        i = j
    return chunks
