from fastapi import FastAPI, Request
import time

app = FastAPI()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):

    start_time = time.time()
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    
    print(f" {request.method} {request.url.path} took {process_time:.4f} seconds")
    return response


# Example endpoints
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/slow")
async def slow_endpoint():
    time.sleep(2)  # Simulate slow operation
    return {"message": "This was slow!"}

