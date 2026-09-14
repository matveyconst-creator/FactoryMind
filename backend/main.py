from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz

app = FastAPI(
    title="FactoryMind API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        pdf = fitz.open(stream=file_bytes, filetype="pdf")

        pages = []

        for page_number, page in enumerate(pdf):
            text = page.get_text()

            pages.append({
                "page": page_number + 1,
                "text": text
            })

        full_text = "\n".join(page["text"] for page in pages)

        result = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(file_bytes),
            "page_count": len(pdf),
            "character_count": len(full_text),
            "text_preview": full_text[:1000],
            "message": "PDF text extracted successfully"
        }

        pdf.close()

        return result

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not process PDF: {str(e)}"
        )