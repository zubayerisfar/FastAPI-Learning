// jwt_client.js
// Example: Frontend logic for JWT authentication with refresh token support

// Store tokens after login
function storeTokens(accessToken, refreshToken) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
}

// Get tokens
function getAccessToken() {
    return localStorage.getItem('access_token');
}
function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

// Remove tokens (logout)
function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

// Make a protected API call with automatic refresh
async function fetchWithAuth(url, options = {}) {
    let token = getAccessToken();
    options.headers = options.headers || {};
    options.headers['Authorization'] = `Bearer ${token}`;

    let response = await fetch(url, options);
    if (response.status === 401) {
        // Try to refresh the access token
        const refreshToken = getRefreshToken();
        const refreshResponse = await fetch('/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (refreshResponse.ok) {
            const data = await refreshResponse.json();
            storeTokens(data.access_token, refreshToken); // Keep using the same refresh token
            // Retry the original request with new access token
            options.headers['Authorization'] = `Bearer ${data.access_token}`;
            response = await fetch(url, options);
        } else {
            // Refresh failed, force logout
            clearTokens();
            window.location.href = '/login'; // Redirect to login page
            throw new Error('Session expired. Please log in again.');
        }
    }
    return response;
}

// Example usage:
// fetchWithAuth('/protected')
//   .then(res => res.json())
//   .then(data => console.log(data))
//   .catch(err => alert(err.message));
