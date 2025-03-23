import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

import uvicorn
import uuid

from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.helpers.logger import logger, request_id_context
from src.exceptions.NotResume import NotResume

from src.routes import analyze_route

app = FastAPI(title="Backend Intelligent Resumer")


@app.middleware('http')
async def catch_exception_middleware(request: Request, call_next):
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    token = request_id_context.set(request_id)

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except NotResume as exception:
        error_response = {
            "status": "error",
            "message": exception.message,
            "error": True,
            "exception_id": str(uuid.uuid4()),
            "x_request_id": request_id
        }
        return JSONResponse(content=error_response, status_code=400)
    except Exception as exception:
        error_response = {
            "status": "error",
            "message": str(exception),
            "error": True,
            "exception_id": str(uuid.uuid4()),
            "x_request_id": request_id
        }

        logger.send_error({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": type(exception).__name__,
            "message": str(exception),
            "exception_id": error_response["exception_id"],
            "x_request_id": request_id,
        })

        return JSONResponse(content=error_response, status_code=500)
    finally:
        request_id_context.reset(token)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_route.router, prefix="/analyze")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
