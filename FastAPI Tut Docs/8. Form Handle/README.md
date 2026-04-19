# Tutorial: Form Handling in FastAPI with Jinja2 Templates

## Overview

This example shows how to handle HTML form submission in FastAPI and render dynamic output using Jinja2 templates.

You will learn how to:

- render a form page,
- receive submitted form values using `Form(...)`,
- pass data to a template,
- show submitted values on a result page.

---

## Folder Structure

```text
8. Form Handle/
|-- app.py
|-- templates/
|   |-- index.html
|   `-- output.html
`-- README.md
```

---

## Step 1: FastAPI App Setup

In `app.py`:

```python
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")
```

### Explanation

- `FastAPI()` creates the API application.
- `Jinja2Templates(directory="templates")` tells FastAPI where template files are stored.
- `HTMLResponse` is used so the browser receives HTML pages.

---

## Step 2: Render the Form Page

In `app.py`:

```python
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "name": "FastAPI Form Handling"}
    )
```

### Explanation

- `@app.get("/")` creates the home route.
- `TemplateResponse("index.html", {...})` renders the HTML file.
- The `request` object must be passed for Jinja2 template rendering.
- `name` is a custom value used inside the template as `{{ name }}`.

---

## Step 3: Handle Form Submission

In `app.py`:

```python
@app.post("/submit/")
async def submit_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...)
):
    print(f"Username: {username}, Email: {email}")
    return templates.TemplateResponse(
        "output.html",
        {"request": request, "username": username, "email": email}
    )
```

### Explanation

- `@app.post("/submit/")` handles form submission.
- `Form(...)` tells FastAPI to read values from form fields.
- `username` and `email` names must match the HTML `name` attributes.
- On submit, data is printed to console and then sent to `output.html`.

---

## Template Walkthrough

## `templates/index.html`

- Contains the form UI.
- Uses:
  - `action="/submit/"` to send data to POST endpoint.
  - `method="post"` to submit securely in request body.
  - `name="username"` and `name="email"` for field binding.

## `templates/output.html`

- Extends `index.html` and overrides `{% block body %}`.
- Displays submitted values using:
  - `{{ username }}`
  - `{{ email }}`

---

## End-to-End Flow

1. User opens `/`.
2. FastAPI renders `index.html`.
3. User fills form and clicks submit.
4. Browser sends POST request to `/submit/`.
5. FastAPI reads form values with `Form(...)`.
6. FastAPI renders `output.html` with submitted values.
7. User sees success output page.

---

## How to Run

Install required packages:

```bash
pip install fastapi uvicorn jinja2 python-multipart
```

Start server:

```bash
uvicorn app:app --reload
```

Open in browser:

```text
http://127.0.0.1:8000/
```

---

## Common Mistakes

1. Missing `python-multipart`

- Symptom: form parsing errors.
- Fix: `pip install python-multipart`

2. Field names do not match

- If HTML uses `name="user_name"` but backend expects `username`, value will be missing.
- Keep form `name` attributes exactly the same as endpoint parameters.

3. Forgetting to pass `request` to template

- `TemplateResponse` needs `{"request": request}`.

4. Wrong template directory path

- Ensure `templates = Jinja2Templates(directory="templates")` points to the correct folder.

---

## Suggested Improvements

1. Add basic validation for empty username and invalid email format.
2. Show validation messages in template instead of only console logging.
3. Save submitted data to a database.
4. Add CSS for better form layout.

This folder demonstrates the core form-handling pattern you will reuse in most server-rendered FastAPI projects.
