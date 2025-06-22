import apiClient from './apiClient';
import type { UserCreateAPI } from '@/types/user'; // For registerUser payload type

// Define types for credentials and response data if not already globally available
interface LoginCredentials {
  username: string; // Corresponds to FastAPI's OAuth2PasswordRequestForm username field
  password: any;    // Corresponds to FastAPI's OAuth2PasswordRequestForm password field
}

interface TokenResponseData {
  access_token: string;
  token_type: string;
}

// User registration payload matches UserCreateAPI, but authService might adapt it if needed.

const loginUser = (credentials: LoginCredentials) => {
  // FastAPI's OAuth2PasswordRequestForm expects form data, not JSON.
  // Axios needs to send it as 'application/x-www-form-urlencoded'.
  const params = new URLSearchParams();
  params.append('username', credentials.username);
  params.append('password', credentials.password);
  // Grant_type is not explicitly needed if your backend OAuth2PasswordRequestForm doesn't require it,
  // but it's standard for OAuth2. If backend requires it, add: params.append('grant_type', 'password');

  return apiClient.post<TokenResponseData>('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
};

const registerUser = (userData: UserCreateAPI) => {
  // UserCreateAPI is already structured for JSON payload as expected by /auth/register
  return apiClient.post('/auth/register', userData);
  // The response for register is UserSchema as per API definition
};

// Optional: Fetch current user profile (if you have a /users/me endpoint)
// const fetchUserProfile = () => {
//   return apiClient.get<User>('/users/me'); // Assuming User type from types/user.ts
// };

const authService = {
  loginUser,
  registerUser,
  // fetchUserProfile,
};

export default authService;
```
