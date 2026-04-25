# Tutorial: Understanding Middleware in FastAPI

## Overview

**Middleware** is code that intercepts every request and response. Think of it as a **security checkpoint** that inspects everything coming in and out of your application.

**Middleware runs:**

1. **Before** your endpoint code (to inspect/modify the request)
2. **After** your endpoint code (to inspect/modify the response)

This tutorial builds a simple middleware that **measures how long each request takes**.

## Project Structure

```
06-Middleware/
└── main.py    # FastAPI app with custom middleware
```

---

## How Middleware Works (Visual Flow)

Imagine a request coming to your API:

```
┌─────────────────────────────────────────────────────┐
│  Client makes request: GET /slow                    │
└────────────────┬────────────────────────────────────┘
                 ↓
        ┌────────────────────┐
        │ MIDDLEWARE STARTS  │
        │ Record start time  │
        └────────┬───────────┘
                 ↓
        ┌────────────────────┐
        │ Run endpoint code  │
        │ (@app.get route)   │
        │ (takes 2 seconds)  │
        └────────┬───────────┘
                 ↓
        ┌────────────────────────┐
        │ MIDDLEWARE CONTINUES   │
        │ Calculate elapsed time │
        │ Add to response header │
        │ Log to console         │
        └────────┬───────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│  Response sent to client with header:               │
│  X-Process-Time: 2.0023                             │
│                                                     │
│  Console shows:                                     │
│    GET /slow took 2.0023 seconds                    │
└─────────────────────────────────────────────────────┘
```

---

## Step 1: Understanding the Middleware Code

### Import Required Modules

```python
from fastapi import FastAPI, Request
import time
```

**What each import does:**

- `FastAPI`: The web framework
- `Request`: Object containing information about the incoming HTTP request
- `time`: Python module to measure time with `time.time()`

### Create the App

```python
app = FastAPI()
```

---

## Step 2: Define the Middleware Function

```python
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):

    start_time = time.time()
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    
    print(f" {request.method} {request.url.path} took {process_time:.4f} seconds")
    return response
```

### Breaking It Down

#### The Decorator

```python
@app.middleware("http")
```

**Meaning:** "Register this function as middleware for all HTTP requests"

This tells FastAPI: "Run this function for **every request** before and after the endpoint code"

#### The Function Signature

```python
async def add_process_time_header(request: Request, call_next):
```

**Parameters:**

- `request: Request` - Information about the incoming request (method, URL, headers, etc.)
- `call_next` - A special function that passes the request to the next middleware/endpoint

**Why `async`?** - Middleware needs to be asynchronous to avoid blocking other requests

#### Inside the Function

**Line 1: Record start time**

```python
start_time = time.time()
```

- Gets current time in seconds since epoch
- Example: `1703088234.567`

**Line 2: Run the endpoint**

```python
response = await call_next(request)
```

- `call_next(request)` - Sends the request to your endpoint handler
- `await` - Wait for the endpoint to finish and return a response
- `response` - The response object from your endpoint

**Line 3: Calculate duration**

```python
process_time = time.time() - start_time
```

- Get current time and subtract start time
- Example: `1703088236.567 - 1703088234.567 = 2.0`

**Line 4: Add header to response**

```python
response.headers["X-Process-Time"] = str(process_time)
```

- Adds a custom HTTP header to the response
- Header name: `X-Process-Time`
- Header value: Duration as a string (e.g., "2.0")
- Client can read this header to see how long the request took

**Line 5: Log to console**

```python
print(f"{request.method} {request.url.path} took {process_time:.4f} seconds")
```

- Prints to your terminal/logs
- Example output: `GET /slow took 2.0023 seconds`
- `:.4f` means: show 4 decimal places

**Line 6: Return the response**

```python
return response
```

- Send the modified response back to the client

---

## Step 3: Create Endpoints to Test

```python
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/slow")
async def slow_endpoint():
    time.sleep(2)  # Wait 2 seconds
    return {"message": "This was slow!"}
```

**What these do:**

- `/` - Returns instantly
- `/slow` - Waits 2 seconds before returning

This lets you test the middleware with different response times.

---

## Running the Application

```bash
python -m uvicorn main:app --reload
```

Output should show:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## Testing the Middleware

### Test 1: Fast Endpoint

Open your browser and go to: **http://127.0.0.1:8000/**

**In your console, you'll see:**

```
 GET / took 0.0012 seconds
```

**In browser response headers include:**

```
X-Process-Time: 0.0012345
```

### Test 2: Slow Endpoint

Open your browser and go to: **http://127.0.0.1:8000/slow**

Wait 2 seconds...

**In your console, you'll see:**

```
 GET /slow took 2.0023 seconds
```

---

## Understanding the Flow (Step by Step)

### What Happens When You Visit `/slow`:

1. **Request arrives** at FastAPI
2. **Middleware starts:**
   - Records `start_time = 1234567890.123`
   - Calls `call_next(request)`
3. **Your endpoint runs:**
   - `time.sleep(2)` pauses for 2 seconds
   - Returns `{"message": "This was slow!"}`
4. **Middleware continues:**
   - Records `end_time = 1234567892.125`
   - Calculates `process_time = 2.002`
   - Adds header: `X-Process-Time: 2.002`
   - Prints: `✓ GET /slow took 2.0023 seconds`
5. **Response sent to client** with the extra header

---

## Real-World Middleware Use Cases

### 1. Logging Requests

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"Outgoing: Status {response.status_code}")
    return response
```

### 2. Add Custom Headers

```python
@app.middleware("http")
async def add_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Custom-Header"] = "MyValue"
    return response
```

### 3. Rate Limiting (Block Too Many Requests)

```python
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host
    # Check if IP has made too many requests
    # If yes, return error
    response = await call_next(request)
    return response
```

---