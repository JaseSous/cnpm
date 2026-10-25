// API Client giao tiếp với API Gateway qua đường dẫn /api
import { POI, TourRoute } from '../types';

const getApiBase = (): string => {
  let base = (import.meta as any).env?.VITE_API_BASE;
  if (!base || typeof base !== 'string' || base.trim() === '') {
    return '/api';
  }
  base = base.trim();
  if (base.endsWith('/')) {
    base = base.slice(0, -1);
  }
  return base;
};

const API_BASE = getApiBase();

export function getStoredToken(): string | null {
  return localStorage.getItem('access_token');
}

export function setStoredToken(token: string) {
  localStorage.setItem('access_token', token);
}

export function clearStoredToken() {
  localStorage.removeItem('access_token');
}

export function getAdminToken(): string | null {
  return localStorage.getItem('admin_access_token');
}

export function setAdminToken(token: string) {
  localStorage.setItem('admin_access_token', token);
}

export function clearAdminToken() {
  localStorage.removeItem('admin_access_token');
}

export function parseJwt(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

async function request(endpoint: string, options: RequestInit = {}) {
  // Ưu tiên token admin nếu là route /admin, hoặc khi không có token du khách nhưng có token admin
  let token = endpoint.startsWith('/admin')
    ? (getAdminToken() || getStoredToken())
    : (getStoredToken() || getAdminToken());

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token && !endpoint.startsWith('/auth/')) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    if (endpoint.startsWith('/admin')) {
      clearAdminToken();
    } else {
      clearStoredToken();
    }
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Mã xác thực không hợp lệ hoặc đã hết hạn');
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `Lỗi HTTP: ${res.status}`);
  }

  return res.json();
}

// --- UC01: Xác thực ---

export async function verifyCode(code: string) {
  return request('/auth/verify', {
    method: 'POST',
    body: JSON.stringify({ code })
  });
}

export async function createPayooSession(amount: number = 50000) {
  return request('/auth/payoo/create-session', {
    method: 'POST',
    body: JSON.stringify({ amount, payment_method: 'online' })
  });
}

export async function triggerPayooWebhook(authCode: string, status: 'Success' | 'Pending' | 'Failed') {
  return request('/auth/payoo/webhook-mock', {
    method: 'POST',
    body: JSON.stringify({ auth_code: authCode, status })
  });
}

// --- UC02: Tải dữ liệu POIs (1 lần) ---

export async function fetchAllPOIs(): Promise<{ pois: POI[]; tour_routes: TourRoute[]; message?: string }> {
  return request('/pois/all');
}

// --- UC03: Chatbot RAG ---

export async function askChatbot(question: string) {
  return request('/chat/ask', {
    method: 'POST',
    body: JSON.stringify({ question })
  });
}

// --- UC04: Admin Endpoints ---

export async function adminLogin(username: string, password: string) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
}

export async function adminCreateCashCode() {
  return request('/admin/cash-code', {
    method: 'POST'
  });
}

export async function adminGetPOIs(): Promise<POI[]> {
  const res = await request('/admin/pois');
  if (Array.isArray(res)) return res;
  if (res && Array.isArray(res.pois)) return res.pois;
  return [];
}

export async function adminCreatePOI(poiData: {
  name: string;
  latitude: number;
  longitude: number;
  trigger_radius: number;
  thumbnail_url?: string;
  original_description: string;
}) {
  return request('/admin/pois', {
    method: 'POST',
    body: JSON.stringify(poiData)
  });
}

export async function adminUpdatePOI(poiId: string, poiData: {
  name?: string;
  latitude?: number;
  longitude?: number;
  trigger_radius?: number;
  thumbnail_url?: string;
  original_description?: string;
}) {
  return request(`/admin/pois/${poiId}`, {
    method: 'PUT',
    body: JSON.stringify(poiData)
  });
}

export async function adminDeletePOI(poiId: string) {
  return request(`/admin/pois/${poiId}`, {
    method: 'DELETE'
  });
}

export async function adminGetPOIStatus(poiId: string) {
  return request(`/admin/pois/${poiId}/pipeline-status`);
}

export async function adminGetMonitoring() {
  return request('/admin/monitoring');
}

export async function sendHeartbeat(clientId: string) {
  return request('/auth/heartbeat', {
    method: 'POST',
    body: JSON.stringify({ client_id: clientId })
  });
}

export async function getActiveVisitorsCount(): Promise<{ active_visitors: number }> {
  return request('/auth/active-visitors');
}

