from fastapi import FastAPI, Request
import time

app = FastAPI()


@app.middleware("http")
async def request_time_counter(request:Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    new_headers = {"X-Process-Time": str(time.time() - start_time)}
    response.headers.update(new_headers)
    process_time = time.time() - start_time
    print(
        f"Request method {request.method} at path {request.url} processed in {process_time} seconds")
    return response


@app.get("/",)
def read_root():
    return {"message": "Hello World"}
