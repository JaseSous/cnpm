import axios from 'axios';

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL;

const AUTH_BASE_URL = GATEWAY_URL || import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8001';
const POI_BASE_URL = GATEWAY_URL || import.meta.env.VITE_POI_API_URL || 'http://localhost:8002';

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

export const DEFAULT_POI_IMAGE = "https://images.unsplash.com/photo-1599818816752-60453c072c41?auto=format&fit=crop&w=800&q=80";

export const getMediaUrl = (path: string | null | undefined): string => {
  if (!path || !path.trim()) return DEFAULT_POI_IMAGE;
  const trimmed = path.trim();
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed;
  }
  const base = (GATEWAY_URL || POI_BASE_URL).replace(/\/+$/, '');
  const cleanPath = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  return `${base}${cleanPath}`;
};

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
        const isLoginRequest = error.config?.url?.includes('/api/auth/login');
        if (!isLoginRequest) {
          sessionStorage.removeItem('access_token');
          sessionStorage.removeItem('user_info');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
      }
      return Promise.reject(error);
    }
  );
};

attachAuthInterceptor(apiClient);
attachAuthInterceptor(poiClient);
