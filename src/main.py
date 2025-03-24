import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

import uvicorn
import uuid
import redis
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.helpers.logger import logger, request_id_context
from src.exceptions.NotResume import NotResume

from src.routes import analyze_route

app = FastAPI(title="Backend Intelligent Resumer")


REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Conexão com Redis
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True,
    socket_timeout=5
)

RATE_LIMIT = int(os.getenv('RATE_LIMIT', 5)) 
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60 * 60 * 24 * 7))


@app.middleware('http')
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    if request.url.path.startswith('/analyze'):
        redis_key = f'rate_limit:{client_ip}'
        
        if not redis_client.exists(redis_key):
            
            pipe = redis_client.pipeline()
            pipe.lpush(redis_key, time.time())
            pipe.expire(redis_key, RATE_LIMIT_WINDOW)
            pipe.execute()
        else:
            count = redis.client.llen(redis_key)
            
            if count >= RATE_LIMIT:
                ttl = redis_client.ttl(redis_key)
                days =  int(ttl / (60 * 60 * 24))
                hours = int((ttl % (60 * 60 * 24)) / (60 * 60))
                
                error_response = {
                    "status": "error",
                    "message": f"Rate limit exceeded. Try again in {days} days and {hours} hours.",
                    "error": True,
                    "exception_id": str(uuid.uuid4()),
                    "x_request_id": request.headers.get('X-Request-ID', str(uuid.uuid4()))
                }
                return JSONResponse(content=error_response, status_code=429)
        
        redis_client.lpush(redis_key, time.time())
    
    return await call_next(request)
                
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
