"""FastAPI server for TouriBot dashboard chat."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tools.api.chat_handler import router as chat_router

app = FastAPI(title="TouriBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
