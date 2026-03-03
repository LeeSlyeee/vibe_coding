import axios from "axios";

// Flask API (킥 분석 전용)
const kickApi = axios.create({
  baseURL: "/api/kick/",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Token Injection
kickApi.interceptors.request.use(
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

export default kickApi;
