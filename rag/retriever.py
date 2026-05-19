import os
import re
from typing import List, Dict, Tuple


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i : i + chunk_size]
        chunks.append(" ".join(chunk))
        if i + chunk_size >= len(words):
            break
        i += chunk_size - overlap
    return chunks


def build_index(docs_dir: str) -> List[Dict]:
    """Reads all files in docs_dir and returns a flat list of chunks with metadata."""
    index: List[Dict] = []
    for fname in sorted(os.listdir(docs_dir)):
        fpath = os.path.join(docs_dir, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            text = _clean(f.read())
        chunks = chunk_text(text)
        for i, c in enumerate(chunks):
            tokens = set(re.findall(r"\w+", c.lower()))
            index.append({
                "doc": fname,
                "chunk_id": f"{fname}#{i}",
                "text": c,
                "tokens": tokens,
            })
    return index


def _score(query_tokens: set, chunk_tokens: set) -> float:
    if not chunk_tokens:
        return 0.0
    overlap = query_tokens.intersection(chunk_tokens)
    return len(overlap) / (len(chunk_tokens) + 1)


def retrieve_topk(index: List[Dict], query: str, k: int = 3) -> List[Tuple[Dict, float]]:
    q_tokens = set(re.findall(r"\w+", query.lower()))
    scored = []
    for ch in index:
        s = _score(q_tokens, ch["tokens"])
        scored.append((ch, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [(c, float(score)) for c, score in scored[:k] if score > 0]


def build_rag_prompt(chunks: List[Dict], question: str) -> str:
    context = "\n\n".join([f"- {c['text']}" for c in chunks])
    prompt = (
        "CONTEXT:\n" + context + "\n\n" + "QUESTION:\n" + question + "\n\n" +
        "Provide a JSON answer following the schema: {\n  \"ok\": boolean,\n  \"data\": {\n    \"answer\": string,\n    \"confidence\": number (0..1),\n    \"actions\": [string],\n    \"error\": null|string\n  }\n}\n"
    )
    return prompt
