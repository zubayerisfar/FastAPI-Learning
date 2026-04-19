# Tutorial: Understanding Middleware in FastAPI

## Overview
This tutorial teaches you about **middleware** - one of the most powerful concepts in web frameworks. Middleware are functions that run **before and after** every request, allowing you to add cross-cutting functionality like logging, authentication, timing, CORS, and more. We'll build a simple request timing middleware that measures how long each request takes to process.

## Project Structure
```
6. Middleware/
└── main.py    # FastAPI app with custom middleware
```

---

## What is Middleware?

**Middleware** is code that sits between the client and your endpoint handlers. Think of it as a "wrapper" around your entire application.

### Request Flow with Middleware:

```
Client Request
     ↓
[Middleware: Before processing]
     ↓
Your Endpoint Handler (@app.get, @app.post, etc.)
     ↓
[Middleware: After processing]
     ↓
Response to Client
```

### Common Middleware Use Cases:
1. **Logging**: Log every request/response
2. **Authentication**: Check if user is logged in
3. **CORS**: Handle cross-origin requests
4. **Rate Limiting**: Prevent abuse
5. **Request Timing**: Measure performance
6. **Error Handling**: Catch and format errors
7. **Request ID**: Track requests across services
8. **Compression**: Compress responses

---

## The Complete Code (`main.py`)

Let's build a middleware that times how long each request takes to process.

```python
from fastapi import FastAPI
import time
```

**Line-by-line explanation:**
- `from fastapi import FastAPI`: Import FastAPI
- `import time`: Python's time module for measuring duration
  - We'll use `time.time()` to get timestamps

### Create the FastAPI App

```python
app = FastAPI()
```

**Line-by-line explanation:**
- `app = FastAPI()`: Create the application instance
- This must be created before defining middleware

---

## Defining Middleware

```python
@app.middleware("http")
async def request_time_counter(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(
        f"Request method {request.method} at path {request.url} processed in {process_time} seconds")
    return response
```

**This is where the magic happens!** Let's break it down line by line:

### The Decorator

```python
@app.middleware("http")
```

**Line-by-line explanation:**
- `@app.middleware("http")`: Register this function as HTTP middleware
  - `"http"`: The middleware type - processes HTTP requests
  - This decorator tells FastAPI to run this function for **every HTTP request**
  - Multiple middleware functions run in the order they're defined

### The Middleware Function

```python
async def request_time_counter(request, call_next):
```

**Line-by-line explanation:**
- `async def request_time_counter(...)`: Define an async middleware function
  - **Must be async** to work with FastAPI's async engine
  - Name can be anything - this one describes its purpose
  
- **Parameters:**
  - `request`: The incoming HTTP request object
    - Contains: `.method` (GET/POST/etc), `.url`, `.headers`, `.body`, etc.
    - Full FastAPI Request object with all request data
  
  - `call_next`: **Critical!** A function that continues the request chain
    - Calling `await call_next(request)` passes control to the next middleware or endpoint
    - Returns the response from the endpoint
    - This is the "dividing line" between before and after processing

### Before Processing (Request Phase)

```python
start_time = time.time()
```

**Line-by-line explanation:**
- `start_time = time.time()`: Record the current timestamp
  - `time.time()`: Returns current time in seconds since epoch (float)
  - Example: `1704900123.456789`
  - This runs **BEFORE** the endpoint handler is called
  - Every middleware operation before `call_next` is "pre-processing"

### Call the Next Handler

```python
response = await call_next(request)
```

**This is the most important line!**

**Line-by-line explanation:**
- `await call_next(request)`: Pass the request to the next layer
  - **What happens here:**
    1. If there are more middleware, call the next one
    2. If this is the last middleware, call your endpoint handler
    3. The endpoint processes the request
    4. The response comes back through all middleware layers
  
  - `await`: This is async - doesn't block other requests
  - Returns the Response object from the endpoint

**Visual representation:**
```
Middleware starts
    ↓ (before call_next)
record start_time
    ↓
await call_next(request) ← Your endpoint executes here
    ↓ (after call_next)
calculate duration
log the info
return response
```

### After Processing (Response Phase)

```python
process_time = time.time() - start_time
```

**Line-by-line explanation:**
- `process_time = time.time() - start_time`: Calculate request duration
  - `time.time()`: Current timestamp (after processing)
  - Subtract `start_time`: Get the difference in seconds
  - Example: `1704900123.789 - 1704900123.456 = 0.333` (333 milliseconds)
  - This runs **AFTER** the endpoint has finished

### Log the Information

```python
print(
    f"Request method {request.method} at path {request.url} processed in {process_time} seconds")
```

**Line-by-line explanation:**
- `print(...)`: Output to console (in production, use proper logging)
- `f"..."`: F-string for formatting
- `request.method`: The HTTP method
  - Examples: "GET", "POST", "PUT", "DELETE"
- `request.url`: The complete URL
  - Example: `http://127.0.0.1:8000/?name=Alice`
- `process_time`: The calculated duration in seconds

**Example output:**
```
Request method GET at path http://127.0.0.1:8000/ processed in 0.0023 seconds
Request method POST at path http://127.0.0.1:8000/items/ processed in 0.1567 seconds
```

### Return the Response

```python
return response
```

**Line-by-line explanation:**
- `return response`: Send the response back to the client
  - **Critical:** You must return the response!
  - The response flows back through all middleware layers
  - Finally reaches the client

**What if you don't return the response?**
- The client gets no response
- Request hangs or times out
- Always return the response (possibly modified)

---

## A Simple Endpoint

```python
@app.get("/",)
def read_root():
    return {"message": "Hello World"}
```

**Line-by-line explanation:**
- Basic GET endpoint for testing
- Returns a JSON response
- The middleware will time how long this takes

---

## How Middleware Execution Works

Let's trace a complete request:

### Request Flow:
```
1. Client sends GET request to http://127.0.0.1:8000/
   ↓
2. Middleware starts: request_time_counter() called
   ↓
3. start_time = time.time()  (e.g., 123.000)
   ↓
4. await call_next(request)  ← Calls read_root() endpoint
   ↓
5. read_root() executes and returns {"message": "Hello World"}
   ↓
6. Response comes back from call_next
   ↓
7. process_time = time.time() - start_time  (e.g., 0.002)
   ↓
8. print() logs the information to console
   ↓
9. return response sends response to client
   ↓
10. Client receives {"message": "Hello World"}
```

### Console Output:
```
Request method GET at path http://127.0.0.1:8000/ processed in 0.002154 seconds
```

---

## Multiple Middleware Example

You can stack multiple middleware. They execute in order:

```python
@app.middleware("http")
async def first_middleware(request, call_next):
    print("First middleware - BEFORE")
    response = await call_next(request)
    print("First middleware - AFTER")
    return response

@app.middleware("http")
async def second_middleware(request, call_next):
    print("Second middleware - BEFORE")
    response = await call_next(request)
    print("Second middleware - AFTER")
    return response

@app.get("/")
def endpoint():
    print("ENDPOINT")
    return {"msg": "ok"}
```

**Execution order:**
```
First middleware - BEFORE
Second middleware - BEFORE
ENDPOINT
Second middleware - AFTER
First middleware - AFTER
```

**Like layers of an onion:**
- Middleware wrap around each other
- Request goes inward (before call_next)
- Response goes outward (after call_next)

---

## Modifying Requests and Responses

Middleware can modify requests before processing and responses before sending:

### Example: Add Custom Header to All Responses

```python
@app.middleware("http")
async def add_custom_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time())
    return response
```

### Example: Block Requests Based on IP

```python
@app.middleware("http")
async def ip_filter(request, call_next):
    if request.client.host == "192.168.1.100":
        return JSONResponse(
            status_code=403,
            content={"detail": "IP blocked"}
        )
    response = await call_next(request)
    return response
```

### Example: Authentication Check

```python
@app.middleware("http")
async def auth_middleware(request, call_next):
    if request.url.path.startswith("/protected"):
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"}
            )
    response = await call_next(request)
    return response
```

---

## How to Run This Project

### 1. Install FastAPI
```bash
pip install fastapi uvicorn
```

### 2. Run the Server
```bash
uvicorn main:app --reload
```

### 3. Test the Endpoint
Visit `http://127.0.0.1:8000/` in your browser or use curl:
```bash
curl http://127.0.0.1:8000/
```

### 4. Check the Console
You'll see timing information:
```
INFO:     127.0.0.1:54321 - "GET / HTTP/1.1" 200 OK
Request method GET at path http://127.0.0.1:8000/ processed in 0.001234 seconds
```

---

## Built-in FastAPI Middleware

FastAPI includes several ready-to-use middleware:

### 1. CORS Middleware (Cross-Origin Resource Sharing)
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**Use case:** Allow your frontend (React/Vue) to call your API

### 2. Trusted Host Middleware
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)
```
**Use case:** Prevent host header attacks

### 3. GZIP Compression
```python
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```
**Use case:** Compress responses to save bandwidth

### 4. HTTPS Redirect
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```
**Use case:** Force HTTPS in production

---

## Practical Use Cases

### 1. Request ID Tracking
```python
import uuid

@app.middleware("http")
async def add_request_id(request, call_next):
    request_id = str(uuid.uuid4())
    print(f"[{request_id}] {request.method} {request.url}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### 2. Database Session Management
```python
@app.middleware("http")
async def db_session(request, call_next):
    session = SessionLocal()
    request.state.db = session
    try:
        response = await call_next(request)
    finally:
        session.close()
    return response
```

### 3. Rate Limiting
```python
from collections import defaultdict
import time

request_counts = defaultdict(list)

@app.middleware("http")
async def rate_limit(request, call_next):
    client_ip = request.client.host
    now = time.time()
    
    # Clean old requests
    request_counts[client_ip] = [
        t for t in request_counts[client_ip] if now - t < 60
    ]
    
    # Check limit
    if len(request_counts[client_ip]) >= 100:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    
    request_counts[client_ip].append(now)
    return await call_next(request)
```

---

## Common Mistakes and Solutions

### Mistake 1: Forgetting `await`
```python
# ❌ WRONG
response = call_next(request)  # Missing await

# ✅ CORRECT
response = await call_next(request)
```

### Mistake 2: Not Returning Response
```python
# ❌ WRONG
async def middleware(request, call_next):
    await call_next(request)
    # Forgot to return!

# ✅ CORRECT
async def middleware(request, call_next):
    response = await call_next(request)
    return response
```

### Mistake 3: Blocking Operations
```python
# ❌ WRONG - Blocks event loop
async def middleware(request, call_next):
    time.sleep(5)  # Blocking!
    response = await call_next(request)
    return response

# ✅ CORRECT - Async sleep
async def middleware(request, call_next):
    await asyncio.sleep(5)
    response = await call_next(request)
    return response
```

---

## Performance Considerations

1. **Keep middleware fast** - They run on EVERY request
2. **Use async operations** - Don't block the event loop
3. **Order matters** - Put cheap middleware first (auth before expensive operations)
4. **Avoid heavy computation** - Offload to background tasks if needed

---

## Key Concepts Summary

1. **Middleware**: Functions that wrap your entire application
2. **@app.middleware("http")**: Decorator to register HTTP middleware
3. **call_next**: Function that continues the request chain
4. **Execution Order**: Before call_next → Endpoint → After call_next
5. **Multiple Middleware**: Execute like nested layers (onion model)
6. **Request Phase**: Code before `await call_next(request)`
7. **Response Phase**: Code after `await call_next(request)`
8. **Must Return Response**: Always return the response object

## When to Use Middleware

**Use Middleware For:**
- Operations needed for EVERY request
- Cross-cutting concerns (logging, auth, timing)
- Request/response modification
- Global error handling

**Don't Use Middleware For:**
- Endpoint-specific logic (use dependencies instead)
- Business logic (belongs in endpoints)
- One-off operations

## Middleware vs Dependencies

| Feature | Middleware | Dependencies |
|---------|-----------|-------------|
| Runs on | All requests | Specific endpoints |
| Use for | Global concerns | Endpoint-specific logic |
| Can modify response | Yes | Limited |
| Performance impact | All requests | Only when used |

Middleware is a powerful tool for adding global functionality to your FastAPI application!
