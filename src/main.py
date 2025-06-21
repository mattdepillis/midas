from dotenv import load_dotenv  # type: ignore
from fastapi import FastAPI  # type: ignore

from api.routes import router

load_dotenv()

app = FastAPI(title="Midas API", version="0.1")

app.include_router(router)


@app.get("/")
def health_check():
    return {"status": "ok"}
