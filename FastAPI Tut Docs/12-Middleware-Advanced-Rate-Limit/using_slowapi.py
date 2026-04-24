from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


limiter = Limiter(key_func=get_remote_address,
                default_limits=["2/second"],
                storage_uri="memory://",
                headers_enabled=True,
                strategy="fixed-window")

app = FastAPI()
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "You have exceeded the allowed number of requests. Please try again later."
        }
    )
    return response


@app.get("/")
@limiter.limit("2/second")
async def read_root(request: Request, response: Response):
    return {"message": "Hello, World!"}
