import axios from 'axios';
import type {
  Hospital,
  BloodBag,
  BloodRequest,
  MatchResult,
  MatchRequest,
  DashboardStats,
  Dispatch,
  DispatchItem,
  MatchResultItem,
} from './types';
import { BloodComponent, BloodType, RhType, UrgencyLevel } from './types';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export interface LoginResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: string;
  real_name: string;
}

export interface UserInfo {
  id: string;
  username: string;
  real_name: string;
  role: string;
  hospital_id: string | null;
}

export const authApi = {
  login: (username: string, password: string) =>
    api.post<LoginResponse>('/auth/login/json', { username, password }),
  getMe: () => api.get<UserInfo>('/auth/me'),
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  isAuthenticated: () => !!localStorage.getItem('token'),
  getToken: () => localStorage.getItem('token'),
  getUser: (): UserInfo | null => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
  setAuth: (data: LoginResponse) => {
    localStorage.setItem('token', data.access_token);
    const userInfo: UserInfo = {
      id: '',
      username: data.username,
      real_name: data.real_name,
      role: data.role,
      hospital_id: null,
    };
    localStorage.setItem('user', JSON.stringify(userInfo));
  },
};

export const hospitalApi = {
  getAll: () => api.get<Hospital[]>('/hospitals/'),
  getById: (id: string) => api.get<Hospital>(`/hospitals/${id}/`),
  create: (data: Partial<Hospital>) => api.post<Hospital>('/hospitals/', data),
};

export const inventoryApi = {
  getAll: (params?: {
    blood_type?: BloodType;
    rh_type?: RhType;
    component?: BloodComponent;
    only_in_stock?: boolean;
  }) => api.get<BloodBag[]>('/inventory/', { params }),
  getById: (id: string) => api.get<BloodBag>(`/inventory/${id}/`),
  create: (data: Partial<BloodBag>) => api.post<BloodBag>('/inventory/', data),
  getExpiringSoon: () => api.get('/inventory/alerts/expiring-soon'),
  getExpired: () => api.get('/inventory/alerts/expired'),
  scrap: (id: string, reason: string) =>
    api.post(`/inventory/${id}/scrap/`, null, { params: { reason } }),
};

export const requestApi = {
  getAll: (params?: { status?: any; urgency?: UrgencyLevel }) =>
    api.get<BloodRequest[]>('/requests/', { params }),
  getById: (id: string) => api.get<BloodRequest>(`/requests/${id}/`),
  create: (data: Partial<BloodRequest>) =>
    api.post<BloodRequest>('/requests/', data),
  match: (requestId: string) =>
    api.post<MatchResult>('/requests/match/', { request_id: requestId } as MatchRequest),
  cancel: (id: string) => api.post(`/requests/${id}/cancel/`),
};

export const dispatchApi = {
  getAll: (params?: { status?: any }) =>
    api.get<Dispatch[]>('/dispatches/', { params }),
  getById: (id: string) => api.get<Dispatch>(`/dispatches/${id}/`),
  confirm: (
    requestId: string,
    matchedItems: MatchResultItem[],
    courier?: string,
    notes?: string
  ) =>
    api.post<Dispatch>('/dispatches/confirm/', matchedItems, {
      params: { request_id: requestId, courier, notes },
    }),
  startTransit: (id: string, courier?: string) =>
    api.post(`/dispatches/${id}/start-transit/`, null, { params: { courier } }),
  confirmDelivery: (id: string) =>
    api.post(`/dispatches/${id}/confirm-delivery/`),
};

export const dashboardApi = {
  getStats: () => api.get<DashboardStats>('/dashboard/stats'),
};

export const compatibilityApi = {
  check: (params: {
    donor_blood_type: BloodType;
    donor_rh_type: RhType;
    recipient_blood_type: BloodType;
    recipient_rh_type: RhType;
    component: BloodComponent;
    is_emergency?: boolean;
  }) => api.get('/compatibility/check/', { params }),
  getCompatibleDonors: (params: {
    recipient_blood_type: BloodType;
    recipient_rh_type: RhType;
    component: BloodComponent;
    is_emergency?: boolean;
  }) => api.get('/compatibility/compatible-donors/', { params }),
};

export default api;
