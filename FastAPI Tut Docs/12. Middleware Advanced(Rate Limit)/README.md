# Tutorial: Advanced Middleware and Rate Limiting

This tutorial explores how to implement **Rate Limiting** in FastAPI. Rate limiting restricts the number of requests a user (or IP) can make within a certain timeframe to prevent abuse, scraping, or overload.

We provide two approaches:

1. **Custom Middleware Approach:** (`main.py`) Building your own rate limiter from scratch using FastAPI's standard middleware.
2. **Library Approach (SlowAPI):** (`using_slowapi.py`) Using the `slowapi` extension, which is the most common industry-standard way to rate limit FastAPI applications.

---

## Part 1: Custom Rate Limit Middleware (`main.py`)

Here we implement a completely custom sliding-window rate limiter directly inside a FastAPI BaseHTTPMiddleware.

### Imports & Setup

```python
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

app = FastAPI()
```

- `from fastapi import FastAPI, Request, Response`: We import core FastAPI elements. `Request` is used to identify the client's IP, and `Response` will be returned immediately if the limit is exceeded.
- `from starlette.middleware.base import BaseHTTPMiddleware`: The base class we must inherit to create class-based middleware in FastAPI.
- `import time`: Used to track timestamps of requests.
- `app = FastAPI()`: Initializes the application instance.

### Middleware Class Definition

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, dispatch=None):
        super().__init__(app, dispatch)
        self.rate_limit_records = {}
```

- `class RateLimitMiddleware(BaseHTTPMiddleware):`: Defines our custom middleware class.
- `def __init__(...):`: The constructor that sets up the middleware state.
- `super().__init__(app, dispatch)`: Initializes the parent `BaseHTTPMiddleware` class so FastAPI can mount it.
- `self.rate_limit_records = {}`: An organized in-memory dictionary. Keys will be client IP addresses. Values will be lists of timestamps when that IP made a request.

### The Dispatch Method (Request Interception)

```python
    async def dispatch(self, request, call_next):
        print(self.rate_limit_records)
        client_ip = request.client.host
        current_time = time.time()
        window_time = 1  # 1 second window
        max_requests = 2  # Max 2 requests per second
```

- `async def dispatch(self, request, call_next):`: The core method of `BaseHTTPMiddleware`. This runs **every time** a request comes in.
- `print(self.rate_limit_records)`: Debug line to show the state of limits in the terminal.
- `client_ip = request.client.host`: Extracts the incoming client's IP. This acts as our unique identifier.
- `current_time = time.time()`: Grabs the exact moment the request hit the server.
- `window_time = 1`: Our time boundary. We only care about requests made in the last 1 second.
- `max_requests = 2`: The threshold limit. Only 2 allowed within our time window.

### Tracking the Timestamps

```python
        if client_ip not in self.rate_limit_records:
            self.rate_limit_records[client_ip] = []
            print("New IP added:", client_ip)

        request_times = self.rate_limit_records[client_ip]
        print("Before cleanup:", request_times)

        # Remove timestamps outside the current window or older than 1 second
        request_times = [t for t in request_times if t > current_time - window_time]
        print("After cleanup:", request_times)
```

- `if client_ip not in self.rate_limit_records:`: If this is the first time we've seen this IP, initialize an empty list for it.
- `request_times = self.rate_limit_records[client_ip]`: Fetch the historic timestamp list for this specific IP.
- `request_times = [t for t in request_times if t > current_time - window_time]`: This is the active "cleanup". We iterate over `request_times`. If a timestamp is older than 1 second ago (`current_time - window_time`), we discard it. We only keep recent hits.

### Saving Timestamps & Enforcing Rules

```python
        # Add current timestamp
        request_times.append(current_time)
        print("After adding current time:", request_times)

        self.rate_limit_records[client_ip] = request_times
        print("Updated records:", self.rate_limit_records)
```

- `request_times.append(current_time)`: Now that old records are clean, we append the _current_ request's timestamp.
- `self.rate_limit_records[client_ip] = request_times`: We write this updated, cleaned list back to our dictionary for the next request to use.

```python
        # Check if rate limit exceeded
        if len(request_times) > max_requests:
            return Response(
                content='{"error": "Rate limit exceeded. Max 2 requests per second allowed."}',
                status_code=429,
                media_type="application/json"
            )
        response = await call_next(request)
        return response
```

- `if len(request_times) > max_requests:`: If the length of our clean timestamp list exceeds 2, the user has clicked too fast!
- `return Response(..., status_code=429)`: We block the request immediately by sending an HTTP 429 (Too Many Requests) response.
- `response = await call_next(request)`: If they didn't exceed the limit, we let the request continue to its intended endpoint by calling `call_next`.
- `return response`: Return the normal endpoint response to the user.

```python
app.add_middleware(RateLimitMiddleware)
```

- `app.add_middleware(RateLimitMiddleware)`: Instructs FastAPI to globally activate this middleware.

---

## Part 2: Rate Limiting using SlowAPI (`using_slowapi.py`)

Using a custom solution with a dictionary is great for learning, but resets on restart and doesn't scale across multiple servers. Production environments usually use **SlowAPI**, built on top of `limits`.

### Imports & SlowAPI Configuration

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
```

- `from slowapi import Limiter`: The main rate-limiting class.
- `from slowapi.util import get_remote_address`: A built-in helper utility to safely get the user's IP.
- `from slowapi.errors import RateLimitExceeded`: The built-in error exception SlowAPI raises when a limit is hit.

```python
limiter = Limiter(key_func=get_remote_address,
                default_limits=["2/second"],
                storage_uri="memory://",
                headers_enabled=True,
                strategy="fixed-window")

app = FastAPI()
app.state.limiter = limiter
```

- `limiter = Limiter(...)`: Configures the limiter engine.
- `key_func=get_remote_address`: Tells the limiter to track users based on their remote IP address.
- `default_limits=["2/second"]`: A global default fallback limit across all routes.
- `storage_uri="memory://"`: Data will hit standard RAM. (In production, replace with a Redis server URL here!).
- `headers_enabled=True`: Automatically injects `X-RateLimit` headers into the HTTP response so clients know how many hits they have left.
- `strategy="fixed-window"`: The algorithms used to calculate time buckets.
- `app.state.limiter = limiter`: Attaches the configured limiter directly to our FastAPI application state so routes can access it.

### Error Handling Route

```python
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
```

- `@app.exception_handler(RateLimitExceeded)`: This decorator tells FastAPI: "If SlowAPI ever throws a `RateLimitExceeded` error anywhere in our code, intercept it and run this function instead of crashing."
- `response = JSONResponse(...)`: We craft a beautiful customized JSON payload stating the limit was exceeded, ensuring a clean HTTP `429` status code.
- `return response`: Returns the graceful denial payload directly to the user.

### Applying Rate Limits

```python
@app.get("/")
@limiter.limit("2/second")
async def read_root(request: Request, response: Response):
    return {"message": "Hello, World!"}
```

- `@app.get("/")`: A standard FastAPI route.
- `@limiter.limit("2/second")`: Directly decorates the specific route. This bypasses global defaults giving this endpoint specific rules.
- `async def read_root(request: Request, response: Response):`: _Important Requirement_: When using SlowAPI, you **MUST** inject `request: Request` and `response: Response` into your endpoint parameters so the Limiter decorator read the IP header and write the limit headers.
- `return {"message": "Hello, World!"}`: The target payload. Will only execute if the user is under the 2 hits per second allowance.
