from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pymupdf
from sentence_transformers import SentenceTransformer
import os
import numpy as np
import re

from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

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
    "documents": [],
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


@app.get("/documents")
def get_documents():
    return {
        "document_count": len(document_store["documents"]),
        "documents": document_store["documents"],
    }

@app.delete("/documents/{filename}")
def delete_document(filename: str):

    document_exists = any(
        document["filename"] == filename
        for document in document_store["documents"]
    )

    if not document_exists:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Find all chunks that do NOT belong to this document
    keep_indices = [
        index
        for index, metadata in enumerate(document_store["chunk_metadata"])
        if metadata["filename"] != filename
    ]

    # Remove document from document list
    document_store["documents"] = [
        document
        for document in document_store["documents"]
        if document["filename"] != filename
    ]

    # Keep only chunks belonging to other documents
    document_store["chunks"] = [
        document_store["chunks"][index]
        for index in keep_indices
    ]

    document_store["chunk_metadata"] = [
        document_store["chunk_metadata"][index]
        for index in keep_indices
    ]

    # Keep corresponding embeddings
    if keep_indices:
        document_store["embeddings"] = document_store["embeddings"][
            keep_indices
        ]
    else:
        document_store["embeddings"] = None

    return {
        "message": f"{filename} removed successfully",
        "document_count": len(document_store["documents"]),
    }


@app.delete("/documents")
def clear_documents():

    document_store["documents"] = []
    document_store["chunks"] = []
    document_store["chunk_metadata"] = []
    document_store["embeddings"] = None

    return {
        "message": "All documents removed successfully",
        "document_count": 0,
    }




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
                    "page": page["page"],
                    "filename": file.filename,
                })

        embeddings = embedding_model.encode(
            chunks,
            normalize_embeddings=True,
        )
        document_store["documents"].append({
            "filename": file.filename,
            "page_count": len(pdf),
            "character_count": len(full_text),
        })

        document_store["chunks"].extend(chunks)

        for metadata in chunk_metadata:
            metadata["filename"] = file.filename

        document_store["chunk_metadata"].extend(chunk_metadata)

        if document_store["embeddings"] is None:
            document_store["embeddings"] = embeddings
        else:
            document_store["embeddings"] = np.vstack([
                document_store["embeddings"],
                embeddings,
            ])
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


class ChatMessage(BaseModel):
    role: str
    content: str


class SearchRequest(BaseModel):
    question: str
    history: list[ChatMessage] = Field(default_factory=list)


def build_search_question(question: str, history: list[ChatMessage]) -> str:
    if not history:
        return question

    recent_history = history[-6:]

    conversation = "\n".join(
        f"{message.role}: {message.content}"
        for message in recent_history
    )

    prompt = f"""
You rewrite follow-up questions into standalone search queries.

Use the conversation history only to resolve references such as:
- it
- this
- that
- they
- the previous method
- the second document
- the difference
- this approach

Do not answer the question.

If the new question already makes sense by itself, return it unchanged.

Conversation history:
{conversation}

New question:
{question}

Return only the standalone question.
"""

    response = openai_client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    return response.output_text.strip()


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
            "filename": document_store["chunk_metadata"][index]["filename"],
            "page": document_store["chunk_metadata"][index]["page"],
            "similarity": float(similarities[index]),
            "text": document_store["chunks"][index],
        })

    return {
        "question": request.question,
        "results": results,
    }

def detect_retrieval_mode(question: str) -> str:
    question_lower = question.lower().strip()

    # Explicit phrases that clearly refer to the whole collection
    global_phrases = [
        "all documents",
        "all uploaded documents",
        "across documents",
        "across the documents",
        "across all documents",
        "compare documents",
        "compare the documents",
        "compare all",
        "all lectures",
        "across all lectures",
        "all files",
        "across all files",
        "summarize all",
        "overview of all",
        "every document",
        "every file",
        "every lecture",
    ]

    if any(phrase in question_lower for phrase in global_phrases):
        return "global"

    # Examples:
    # "all three documents"
    # "all 3 documents"
    # "all twenty lectures"
    # "all 20 files"
    numbered_collection_pattern = (
        r"\ball\s+(?:\d+|[a-z]+)\s+"
        r"(?:documents?|files?|lectures?|pdfs?)\b"
    )

    if re.search(numbered_collection_pattern, question_lower):
        return "global"

    return "local"


def retrieve_local(similarities, top_k=3, threshold=0.18):
    """
    Retrieve the most relevant chunks across all uploaded documents.
    """

    sorted_indices = np.argsort(similarities)[::-1]

    indices = [
        int(index)
        for index in sorted_indices
        if similarities[index] >= threshold
    ]

    return indices[:top_k]


def retrieve_global(similarities, top_k_per_document=2):
    """
    Retrieve relevant chunks from every uploaded document.
    """

    selected_indices = []

    for document in document_store["documents"]:
        filename = document["filename"]

        # Find all chunks belonging to this document
        document_indices = [
            index
            for index, metadata in enumerate(document_store["chunk_metadata"])
            if metadata["filename"] == filename
        ]

        # Sort only this document's chunks by similarity
        document_indices = sorted(
            document_indices,
            key=lambda index: similarities[index],
            reverse=True,
        )

        # Take the best chunks from this document
        selected_indices.extend(
            document_indices[:top_k_per_document]
        )

    return selected_indices

@app.post("/documents/ask")
def ask_document(request: SearchRequest):

    if not document_store["chunks"]:
        raise HTTPException(
            status_code=400,
            detail="No document uploaded yet"
        )
    
    retrieval_mode = detect_retrieval_mode(request.question)

    search_question = build_search_question(
        request.question,
        request.history,
    )

    # 1. Semantic search

    question_embedding = embedding_model.encode(
        search_question,
        normalize_embeddings=True,
    )

    similarities = np.dot(
        document_store["embeddings"],
        question_embedding,
    )

    similarity_threshold = 0.18

    if retrieval_mode == "local":

        # LOCAL:
        # Take the best chunks across ALL documents
        top_k = 3

        sorted_indices = np.argsort(similarities)[::-1]

        semantic_indices = [
            int(index)
            for index in sorted_indices
            if similarities[index] >= similarity_threshold
        ][:top_k]

    else:

        # GLOBAL:
        # Take the best chunks from EACH document
        top_k_per_document = 2

        sorted_indices = np.argsort(similarities)[::-1]

        document_indices = {}

        for index in sorted_indices:
            index = int(index)

            filename = document_store["chunk_metadata"][index]["filename"]

            if filename not in document_indices:
                document_indices[filename] = []

            if len(document_indices[filename]) < top_k_per_document:
                document_indices[filename].append(index)

        semantic_indices = []

        for filename, indices in document_indices.items():
            semantic_indices.extend(indices)

    # 2. Exact section/task reference search
    # Examples: 2.4, 3.1, 10.2
    exact_indices = []

    if retrieval_mode == "local":

        section_references = re.findall(
            r"\b\d+\.\d+\b",
            search_question
        )

        for section_reference in section_references:
            pattern = rf"(?m)^\s*{re.escape(section_reference)}(?:\s|$)"

            for index, chunk in enumerate(document_store["chunks"]):
                if re.search(pattern, chunk):
                    exact_indices.append(index)

    # 3. Combine exact + semantic results
    top_indices = []

    for index in exact_indices + semantic_indices:
        if index not in top_indices:
            top_indices.append(index)


    # Nothing relevant found
    if len(top_indices) == 0:
        return {
            "question": request.question,
            "search_question": search_question,
            "retrieval_mode": retrieval_mode,
            "answer": "I could not find this information in the uploaded documents.",
            "sources": [],
        }

    # 4. Build context
    retrieved_chunks = [
        {
            "text": document_store["chunks"][index],
            "page": document_store["chunk_metadata"][index]["page"],
            "filename": document_store["chunk_metadata"][index]["filename"],
        }
        for index in top_indices
    ]

    context = "\n\n---\n\n".join(
        f"[Document: {chunk['filename']}, Page {chunk['page']}]\n{chunk['text']}"
        for chunk in retrieved_chunks
    )

    history_text = "\n".join(
        f"{message.role}: {message.content}"
        for message in request.history
    )

    prompt = f"""
You are an engineering document assistant.

Answer the user's question only using the provided document context.

Use the conversation history to understand references and follow-up questions
such as "it", "this", "that", "why", or "how".
The conversation history is only for understanding the user's intent.
Factual claims in the answer must still be supported by the document context.

Format the answer using Markdown.

For mathematical expressions, use LaTeX:
- Use $...$ for inline mathematics.
- Use $$...$$ for display mathematics.
- Do not use \\( ... \\) or \\[ ... \\].

If the requested information cannot be found in the document context, say:
"I could not find this information in the uploaded document."

Conversation history:
{history_text}

Document context:
{context}

Current question:
{request.question}
"""

    response = openai_client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    # 5. Return sources
    sources = []

    for index in top_indices:
        sources.append({
            "chunk_index": int(index),
            "filename": document_store["chunk_metadata"][index]["filename"],
            "page": document_store["chunk_metadata"][index]["page"],
            "similarity": float(similarities[index]),
            "text": document_store["chunks"][index],
        })

    return {
        "question": request.question,
        "search_question": search_question,
        "retrieval_mode": retrieval_mode,
        "answer": response.output_text,
        "sources": sources,
    }