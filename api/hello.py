from fastapi import FastAPI

# Minimal FastAPI app to verify Vercel Python routing
app = FastAPI(title="Hello Function")

@app.get("/")
def hello():
    return {"status": "ok", "message": "hello from serverless"}