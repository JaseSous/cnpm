import axios from 'axios';

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL;

const AUTH_BASE_URL = GATEWAY_URL || import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8001';
const POI_BASE_URL = GATEWAY_URL || import.meta.env.VITE_POI_API_URL || 'http://localhost:8002';
const CHATBOT_BASE_URL = GATEWAY_URL || import.meta.env.VITE_CHATBOT_API_URL || 'http://localhost:8003';

export const authClient = axios.create({
  baseURL: AUTH_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const poiClient = axios.create({
  baseURL: POI_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const chatbotClient = axios.create({
  baseURL: CHATBOT_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
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

const attachCustomerAuth = (instance: any) => {
  instance.interceptors.request.use((config: any) => {
    const token = localStorage.getItem('customer_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  instance.interceptors.response.use(
    (response: any) => response,
    (error: any) => {
      if (error.response && error.response.status === 401) {
        localStorage.removeItem('customer_token');
        localStorage.removeItem('customer_expires_at');
        if (window.location.pathname !== '/auth' && window.location.pathname !== '/') {
          window.location.href = '/auth';
        }
      }
      return Promise.reject(error);
    }
  );
};

attachCustomerAuth(authClient);
attachCustomerAuth(poiClient);
attachCustomerAuth(chatbotClient);
