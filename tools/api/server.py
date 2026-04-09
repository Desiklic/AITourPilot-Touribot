"""FastAPI server for TouriBot dashboard chat."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tools.api.chat_handler import router as chat_router
from tools.api.calendar_routes import router as calendar_router
from tools.api.email_routes import router as email_router
from tools.api.file_handler import router as files_router

app = FastAPI(title="TouriBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat")
app.include_router(calendar_router, prefix="/api/calendar")
app.include_router(email_router, prefix="/api/email")
app.include_router(files_router, prefix="/api/files")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8766)
