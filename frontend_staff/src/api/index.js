import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1/",
  timeout: 5000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Token Injection
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

export default api;
