import uvicorn
from fastapi import FastAPI

from src.routes import analyze_route

app = FastAPI()

app.include_router(analyze_route.router, prefix="/analyze")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8008)
