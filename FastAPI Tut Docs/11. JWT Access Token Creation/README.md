# JWT Authentication System - README

## Overview

This is a complete JWT (JSON Web Token) authentication system with access and refresh token support using FastAPI (backend) and JavaScript (frontend).

---

## Backend (FastAPI)

### What the Backend Does:

1. **User Registration (`/register`)**

   - Accepts username, password, and email
   - Hashes the password using bcrypt
   - Stores user in the database
   - Returns success message

2. **User Login (`/login`)**

   - Accepts username and password
   - Verifies credentials against database
   - Issues two tokens:
     - **Access Token**: Short-lived (30 minutes) for accessing protected resources
     - **Refresh Token**: Long-lived (7 days) for obtaining new access tokens
   - Returns both tokens to the client

3. **Token Refresh (`/refresh`)**

   - Accepts a refresh token
   - Validates the refresh token
   - If valid, issues a new access token
   - If invalid/expired, returns 401 error

4. **Protected Route (`/protected`)**
   - Requires valid access token in Authorization header
   - Validates token and expiration
   - Returns protected data if token is valid
   - Returns 401 if token is invalid or expired

### Token Expiration Strategy:

- **Access Token**: 30 minutes (short-lived for security)
- **Refresh Token**: 7 days (longer for user convenience)

---

## Frontend/Client Side

### What the Client Needs to Do:

1. **Login Flow**

   ```javascript
   // Send login request
   fetch("/login", {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ username: "user", password: "pass" }),
   })
     .then((res) => res.json())
     .then((data) => {
       // Store both tokens
       localStorage.setItem("access_token", data.access_token);
       localStorage.setItem("refresh_token", data.refresh_token);
     });
   ```

2. **Accessing Protected Routes**

   ```javascript
   // Send access token in Authorization header
   const token = localStorage.getItem("access_token");
   fetch("/protected", {
     headers: { Authorization: `Bearer ${token}` },
   })
     .then((res) => res.json())
     .then((data) => console.log(data));
   ```

3. **Automatic Token Refresh**

   - When a protected request returns 401 (token expired):
     - Automatically call `/refresh` with the refresh token
     - Get a new access token
     - Retry the original request with the new token
   - If refresh fails (refresh token expired):
     - Clear all tokens
     - Redirect to login page

4. **Logout**
   ```javascript
   // Clear tokens from storage
   localStorage.removeItem("access_token");
   localStorage.removeItem("refresh_token");
   // Redirect to login
   window.location.href = "/login";
   ```

---

## Complete Flow Diagram

```
1. User Login
   └─> Backend validates credentials
       └─> Issues access_token (30 min) + refresh_token (7 days)
           └─> Client stores both tokens

2. Access Protected Resource
   └─> Client sends request with access_token
       └─> Backend validates token
           ├─> Valid: Return protected data
           └─> Invalid/Expired: Return 401

3. Token Expired (401 Error)
   └─> Client automatically calls /refresh with refresh_token
       └─> Backend validates refresh_token
           ├─> Valid: Issue new access_token
           │   └─> Client retries original request
           └─> Invalid/Expired: Return 401
               └─> Client redirects to login

4. Logout
   └─> Client clears all tokens
       └─> Redirects to login page
```

---

## Security Best Practices

### Backend:

- Use HTTPS in production
- Store passwords as bcrypt hashes
- Use strong SECRET_KEY
- Set appropriate token expiration times
- Validate tokens on every protected endpoint

### Frontend:

- Store tokens securely (consider httpOnly cookies for refresh tokens)
- Never expose tokens in URLs
- Clear tokens on logout
- Implement automatic refresh logic
- Handle expired sessions gracefully

---

## Files Structure

```
11. JWT Access Token Creation/
├── app.py                    # FastAPI backend with endpoints
├── auth_utils.py            # Token creation/validation utilities
├── database.py              # Database setup
├── models.py                # User model
├── jwt_client.js            # Frontend token management logic
├── jwt_real_life_overview.md # Conceptual overview
└── README.md                # This file
```

---

## Installation & Setup

### Backend:

```bash
pip install fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt]
uvicorn app:app --reload
```

### Frontend:

- Include `jwt_client.js` in your HTML
- Use `fetchWithAuth()` for all protected API calls
- Implement login/logout UI

---

## Testing the Flow

1. Register a user: `POST /register`
2. Login: `POST /login` → Get access_token and refresh_token
3. Access protected route: `GET /protected` with Authorization header
4. Wait 30 minutes (or manually invalidate token) and retry
5. Frontend should automatically refresh and retry
6. After 7 days, refresh token expires → User must login again

---

## Key Takeaways

- **Access tokens** are short-lived and used for API requests
- **Refresh tokens** are long-lived and used to get new access tokens
- Frontend handles token storage and automatic refresh
- Backend validates tokens and manages expiration
- This pattern provides security + user convenience
