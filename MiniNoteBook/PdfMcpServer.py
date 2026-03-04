from mcp.server.fastmcp import FastMCP
import requests
import uuid
from typing import List, Dict

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

mcp = FastMCP()

# -----------------------------
# In-memory stores (replace later with DB)
# -----------------------------
PDF_STORE: Dict[str, List[str]] = {}
EMBEDDING_STORE: Dict[str, List[List[float]]] = {}

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
@mcp.tool(
    name="ingest_and_query_pdf",
    description="Ingest a PDF (chunk, embed, store), then retrieve relevant chunks to answer a query."
)
def ingest_and_query_pdf(pdf_path: str, query: str) -> dict:
    print(f"Received PDF path: {pdf_path}, Query: {query}")
    if not pdf_path:
        raise ValueError("pdf_path is required")

    if not query:
        raise ValueError("query is required")

    reader = PdfReader(pdf_path)
    full_text = ""

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    if not full_text.strip():
        raise ValueError("No text found in PDF")

    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start = end - overlap

        return chunks

    chunks = chunk_text(full_text)

    embeddings = embedding_model.encode(chunks, convert_to_numpy=True).tolist()

    pdf_id = str(uuid.uuid4())
    PDF_STORE[pdf_id] = chunks
    EMBEDDING_STORE[pdf_id] = embeddings

    query_embedding = embedding_model.encode(query, convert_to_numpy=True)

    def cosine_similarity(a, b):
        return sum(x * y for x, y in zip(a, b)) / (
            (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
        )

    scored_chunks = [
        (chunk, cosine_similarity(query_embedding, emb))
        for chunk, emb in zip(chunks, embeddings)
    ]

    top_chunks = sorted(scored_chunks, key=lambda x: x[1], reverse=True)[:2]

    return {
        "chunks": top_chunks
    }

def main():
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()