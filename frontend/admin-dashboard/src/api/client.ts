import axios from 'axios';

const AUTH_BASE_URL = import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8001';
const POI_BASE_URL = import.meta.env.VITE_POI_API_URL || 'http://localhost:8002';

export const apiClient = axios.create({
  baseURL: AUTH_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const poiClient = axios.create({
  baseURL: POI_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const attachAuthInterceptor = (instance: any) => {
  instance.interceptors.request.use((config: any) => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  instance.interceptors.response.use(
    (response: any) => response,
    (error: any) => {
      if (error.response && error.response.status === 401) {
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('user_info');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
  );
};

attachAuthInterceptor(apiClient);
attachAuthInterceptor(poiClient);
