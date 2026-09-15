from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pymupdf
from sentence_transformers import SentenceTransformer
import os
import numpy as np
import pymupdf


from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

app = FastAPI(
    title="FactoryMind API",
    version="0.1.0",
)

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

document_store = {
    "filename": None,
    "chunks": [],
    "chunk_metadata": [],
    "embeddings": None,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 800,
    overlap: int = 120,
):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

@app.get("/")
def root():
    return {"message": "FactoryMind backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    file_bytes = await file.read()

    try:
        pdf = pymupdf.open(stream=file_bytes, filetype="pdf")

        pages = []

        for page_number, page in enumerate(pdf):
            text = page.get_text()

            pages.append({
                "page": page_number + 1,
                "text": text
            })

        full_text = "\n".join(page["text"] for page in pages)

        chunks = []
        chunk_metadata = []

        for page in pages:
            page_chunks = split_text_into_chunks(page["text"])

            for chunk in page_chunks:
                chunks.append(chunk)

                chunk_metadata.append({
                    "page": page["page"]
                })

        embeddings = embedding_model.encode(
            chunks,
            normalize_embeddings=True,
        )
        document_store["filename"] = file.filename
        document_store["chunks"] = chunks
        document_store["chunk_metadata"] = chunk_metadata
        document_store["embeddings"] = embeddings
        result = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(file_bytes),
            "page_count": len(pdf),
            "character_count": len(full_text),

            "chunk_count": len(chunks),
            "chunks_preview": chunks[:3],

            "embedding_count": len(embeddings),
            "embedding_dimension": len(embeddings[0]) if len(embeddings) > 0 else 0,
            "embedding_preview": embeddings[0][:10].tolist()
            if len(embeddings) > 0
            else [],

            "text_preview": full_text[:1000],
            "message": "PDF text extracted, chunked and embedded successfully",
        }

        pdf.close()

        return result

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not process PDF: {str(e)}"
        )

from pydantic import BaseModel
import numpy as np


class SearchRequest(BaseModel):
    question: str


@app.post("/documents/search")
def search_document(request: SearchRequest):

    if not document_store["chunks"]:
        return {
            "message": "No document uploaded yet"
        }

    question_embedding = embedding_model.encode(
        request.question,
        normalize_embeddings=True,
    )

    similarities = np.dot(
        document_store["embeddings"],
        question_embedding,
    )

    top_k = 3

    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []

    for index in top_indices:
        results.append({
            "chunk_index": int(index),
            "page": document_store["chunk_metadata"][index]["page"],
            "similarity": float(similarities[index]),
            "text": document_store["chunks"][index],
        })

    return {
        "question": request.question,
        "filename": document_store["filename"],
        "results": results,
    }

@app.post("/documents/ask")
def ask_document(request: SearchRequest):

    if not document_store["chunks"]:
        raise HTTPException(
            status_code=400,
            detail="No document uploaded yet"
        )

    question_embedding = embedding_model.encode(
        request.question,
        normalize_embeddings=True,
    )

    similarities = np.dot(
        document_store["embeddings"],
        question_embedding,
    )

    top_k = 3
    similarity_threshold = 0.18

    sorted_indices = np.argsort(similarities)[::-1][:top_k]

    top_indices = [
        index
        for index in sorted_indices
        if similarities[index] >= similarity_threshold
    ]

    if len(top_indices) == 0:
        return {
            "question": request.question,
            "answer": "I could not find this information in the uploaded document.",
            "filename": document_store["filename"],
            "sources": [],
        }

    retrieved_chunks = [
        {
            "text": document_store["chunks"][index],
            "page": document_store["chunk_metadata"][index]["page"],
        }
        for index in top_indices
    ]

    retrieved_chunks = [
        {
            "text": document_store["chunks"][index],
            "page": document_store["chunk_metadata"][index]["page"],
        }
        for index in top_indices
    ]

    context = "\n\n---\n\n".join(
        f"[Page {chunk['page']}]\n{chunk['text']}"
        for chunk in retrieved_chunks
    )

    prompt = f"""
You are an engineering document assistant.

Answer the user's question only using the provided document context.

If the answer cannot be found in the context, say:
"I could not find this information in the uploaded document."

Document context:
{context}

Question:
{request.question}
"""

    response = openai_client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    sources = []

    for index in top_indices:
        sources.append({
            "chunk_index": int(index),
            "page": document_store["chunk_metadata"][index]["page"],
            "similarity": float(similarities[index]),
            "text": document_store["chunks"][index],
        })

    return {
        "question": request.question,
        "answer": response.output_text,
        "filename": document_store["filename"],
        "sources": sources,
    }