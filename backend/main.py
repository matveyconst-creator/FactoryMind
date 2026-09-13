from fastapi import FastAPI

app = FastAPI(
    title="FactoryMind API",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "FactoryMind backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }