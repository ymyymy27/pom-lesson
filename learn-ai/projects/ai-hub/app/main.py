from fastapi import FastAPI

app = FastAPI(title="AI Hub", version="0.1.0")


@app.get("/")
def root():
    return {"message": "Hello from AI Hub"}


@app.get("/health")
def health():
    return {"status": "ok"}
