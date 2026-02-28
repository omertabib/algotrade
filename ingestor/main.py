import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

# נניח שזה הרכיב שמנהל את הזרמת הנתונים
# מתוך ה-AlpacaDataProvider שבנינו
from services.ingestor import DataIngestor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    ingestor = DataIngestor()
    # הרצת ה-Ingestor במשימת רקע (Background Task)
    task = asyncio.create_task(ingestor.start_streaming())

    yield

    # Shutdown:
    task.cancel()
    await ingestor.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "provider": "Alpaca"}


if __name__ == "__main__":
    import uvicorn

    # הרצת השרת על פורט 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)