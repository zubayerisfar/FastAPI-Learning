# Tutorial: Image Upload Handling with FastAPI (In-Depth)

## Overview

This project demonstrates how to build a server-rendered FastAPI form that:

- collects user text fields (`username`, `email`),
- receives an uploaded image file,
- saves the file on disk,
- serves saved files through a static route,
- and renders the submitted data + image preview in a response template.

This is a foundational pattern for profile image uploads, support ticket attachments, marketplace product images, and other media workflows.

---

## Project Structure

```text
10. Image Upload Handle/
|-- app.py
|-- static/
|   |-- files/
|   `-- uploads/
|-- templates/
|   |-- index.html
|   `-- output.html
`-- README.md
```

### Role of each folder

- `templates/`: HTML files rendered by Jinja2.
- `static/`: files served directly by the web server.
- `static/uploads/`: where uploaded files are stored.
- `app.py`: FastAPI app, routes, file-save logic, template rendering.

---

## Code in Small Pieces (Recommended)

Instead of reading one big code block, learn the app in these chunks.

---

### Piece 1: Imports

```python
from fastapi import FastAPI, Form, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import shutil
```

This imports everything needed for:

- routing,
- HTML rendering,
- form and file parsing,
- local file saving.

### Piece 2: App + Static + Templates Setup

```python
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "static/uploads/"
```

This section does project-level setup:

- creates the FastAPI app,
- exposes static files under `/static`,
- sets template directory,
- defines upload destination folder.

### Piece 3: GET Route (Show Form)

```python
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "name": "FastAPI Image Handling"}
    )
```

This route renders the upload form page.

### Piece 4: POST Route Signature (Receive Form + File)

```python
@app.post("/submit/")
async def submit_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...)
):
```

This route receives three required inputs:

- `username` from form data,
- `email` from form data,
- `file` from multipart file upload.

### Piece 5: Save Uploaded File

```python
file_location = os.path.join(UPLOAD_FOLDER, file.filename)
with open(file_location, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
```

This writes uploaded bytes to disk inside `static/uploads/`.

### Piece 6: Render Result Page

```python
filename = file.filename
image_path = f"{UPLOAD_FOLDER}{filename}"

return templates.TemplateResponse(
    "output.html",
    {
        "request": request,
        "username": username,
        "email": email,
        "image_path": image_path,
    },
)
```

This passes form values and image path to the output template.

---

## Import-Level Breakdown

### `from fastapi import FastAPI, Form, Request, File, UploadFile`

- `FastAPI`: app object.
- `Form`: parse text inputs from `multipart/form-data` or form posts.
- `Request`: required by Jinja template rendering context.
- `File`: marks a parameter as file input in request parsing.
- `UploadFile`: optimized file interface that wraps uploaded content and metadata (`filename`, `content_type`, `.file`).

### `from fastapi.responses import HTMLResponse`

- Forces route response type to HTML in docs and response handling.

### `from fastapi.templating import Jinja2Templates`

- Integrates Jinja2 with FastAPI.
- Lets you render `TemplateResponse(template_name, context_dict)`.

### `from fastapi.staticfiles import StaticFiles`

- Exposes a local directory over HTTP (for images/CSS/JS).

### `import os`, `import shutil`

- `os.path.join`: safe path building.
- `shutil.copyfileobj`: streams data from uploaded file object to destination file object.

---

## App Initialization

### `app = FastAPI()`

Creates the ASGI application instance.

### `app.mount("/static", StaticFiles(directory="static"), name="static")`

This line is critical for image preview.

- URL prefix `/static` is mapped to local folder `static`.
- Any file under `static` becomes reachable from browser.

Example mapping:

- local path: `static/uploads/photo.jpg`
- browser URL: `/static/uploads/photo.jpg`

### `templates = Jinja2Templates(directory="templates")`

Tells FastAPI where to find template files.

### `UPLOAD_FOLDER = "static/uploads/"`

Defines where uploads are stored on disk.

Important: the folder must exist. If missing, file writes fail.

---

## GET Route: Render Form Page

```python
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "name": "FastAPI Image Handling"}
    )
```

### What happens here

1. Browser requests `/`.
2. FastAPI calls `index()`.
3. Jinja renders `templates/index.html`.
4. Template receives:
   - `request` (required by Starlette/Jinja integration)
   - `name` (custom variable shown in heading)

---

## POST Route: Receive Form + File Upload

```python
@app.post("/submit/")
async def submit_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...)
):
```

### Parameter behavior

- `username` and `email` are extracted from form fields.
- `file` is parsed from multipart request body.
- `Form(...)` and `File(...)` with `...` mean required fields.

If any required field is missing, FastAPI returns validation error.

---

## Saving Uploaded File to Disk

```python
file_location = os.path.join(UPLOAD_FOLDER, file.filename)
with open(file_location, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
```

### Step-by-step

1. Build destination path using original uploaded filename.
2. Open destination in binary write mode (`wb`).
3. Copy bytes from uploaded file stream to destination file.

### Why binary mode (`wb`)

Images are binary data. Text mode would corrupt bytes.

### Why `copyfileobj`

It streams content directly between file-like objects, good for upload handling.

---

## Returning the Preview Page

```python
filename = file.filename
image_path = f"{UPLOAD_FOLDER}{filename}"
return templates.TemplateResponse(
    "output.html",
    {
        "request": request,
        "username": username,
        "email": email,
        "image_path": image_path,
    }
)
```

### How image display works

- `image_path` becomes something like `static/uploads/photo.png`.
- In HTML template, `<img src="{{ image_path }}">` requests that path from browser.
- Because `/static` is mounted, browser can load it.

Note: using `/static/uploads/photo.png` is the safest URL form for browser usage.

---

## Template Breakdown

## `templates/index.html`

Key part:

```html
<form action="/submit/" enctype="multipart/form-data" method="post"></form>
```

### Why `enctype="multipart/form-data"` is required

Without it, file bytes are not sent properly and backend cannot parse file content.

Other fields:

- `name="username"` maps to backend parameter `username`.
- `name="email"` maps to backend parameter `email`.
- `name="file"` maps to backend parameter `file`.

If names do not match, backend receives missing fields.

## `templates/output.html`

This template extends `index.html` and fills `body` block:

```html
<img src="{{ image_path }}" alt="Uploaded Image" style="max-width:300px;" />
```

This displays the uploaded file after successful save.

---

## Complete Request Lifecycle

1. User opens `/`.
2. `index.html` form is rendered.
3. User chooses image + enters fields.
4. Browser sends POST `/submit/` with multipart body.
5. FastAPI validates required fields.
6. FastAPI saves uploaded file to `static/uploads/`.
7. FastAPI renders `output.html` with submitted values.
8. Browser requests image URL from static mount.
9. Uploaded image is displayed on page.

---

## How to Run

Install dependencies:

```bash
pip install fastapi uvicorn jinja2 python-multipart
```

Run server (inside this folder):

```bash
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Common Errors and Fixes

### 1) "RuntimeError: Form data requires \"python-multipart\""

Fix:

```bash
pip install python-multipart
```

### 2) Uploaded image not showing in output page

Check:

- static mount exists: `app.mount("/static", ...)`
- file is actually saved in `static/uploads/`
- image path in template starts with `/static/...` or resolves correctly

### 3) File save error (directory missing)

Make sure `static/uploads/` exists before uploading.

### 4) Overwrite issue with same filename

Current code saves using original filename. If two uploads share same name, old file is replaced.

---

## Security and Production Notes

Current code is great for learning, but production upload systems should add checks:

1. Validate file type by MIME type and extension.
2. Enforce max file size.
3. Sanitize filename to prevent path traversal.
4. Generate unique filename (UUID/timestamp) to avoid overwrite.
5. Optionally scan uploads for malware.
6. Store uploads in cloud/object storage for scale.

---

## Suggested Improved Save Pattern

Example idea (not currently in your code):

```python
import uuid
from pathlib import Path

safe_name = f"{uuid.uuid4().hex}{Path(file.filename).suffix.lower()}"
file_location = os.path.join(UPLOAD_FOLDER, safe_name)
```

Benefits:

- unique file names,
- safer path behavior,
- lower chance of accidental replacement.

---

## Key Takeaways

1. `multipart/form-data` is mandatory for file uploads from HTML forms.
2. `UploadFile` gives metadata and a stream you can save efficiently.
3. Static file mounting is required to view uploaded files in browser.
4. Template context variables connect backend logic to frontend display.
5. Real-world upload flows need validation, limits, and safer naming.

---

## Full `app.py` Reference (Optional)

Use this only after understanding the pieces above.

```python
from fastapi import FastAPI, Form, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import shutil

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "static/uploads/"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # file name, arguments in dict form
    return templates.TemplateResponse("index.html", {"request": request, "name": "FastAPI Image Handling"})


@app.post("/submit/")
async def submit_form(request: Request, username: str = Form(...), email: str = Form(...), file: UploadFile = File(...)):
    # Process the form data
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb") as buffer:  # store the file in the path
        shutil.copyfileobj(file.file, buffer)

    # send the file location to the html form again
    filename = file.filename
    image_path = f"{UPLOAD_FOLDER}{filename}"
    print(f"Username: {username}, Email: {email}, Image Path: {image_path}")
    return templates.TemplateResponse("output.html", {"request": request, "username": username, "email": email, "image_path": image_path})
```
