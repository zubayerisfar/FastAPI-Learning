from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time


app = FastAPI()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, dispatch=None):
        super().__init__(app, dispatch)
        self.rate_limit_records = {}

    async def dispatch(self, request, call_next):
        print(self.rate_limit_records)
        client_ip = request.client.host
        current_time = time.time()
        window_time = 1  # 1 second window
        max_requests = 2  # Max 2 requests per second
        if client_ip not in self.rate_limit_records:
            self.rate_limit_records[client_ip] = []
            print("New IP added:", client_ip)
            
        request_times = self.rate_limit_records[client_ip]
        print("Before cleanup:", request_times)
        
        # Remove timestamps outside the current window or older than 1 second
        request_times = [t for t in request_times if t > current_time - window_time]
        print("After cleanup:", request_times)
        
        # Add current timestamp
        request_times.append(current_time)
        print("After adding current time:", request_times)
        
        self.rate_limit_records[client_ip] = request_times
        print("Updated records:", self.rate_limit_records)
        # Check if rate limit exceeded
        if len(request_times) > max_requests:
            return Response(
                content='{"error": "Rate limit exceeded. Max 2 requests per second allowed."}',
                status_code=429,
                media_type="application/json"
            )
        response = await call_next(request)
        return response


app.add_middleware(RateLimitMiddleware)


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


@app.get("/test")
async def read_test():
    return {"message": "This is a test endpoint."}
