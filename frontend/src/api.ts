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

export const hospitalApi = {
  getAll: () => api.get<Hospital[]>('/hospitals'),
  getById: (id: string) => api.get<Hospital>(`/hospitals/${id}`),
  create: (data: Partial<Hospital>) => api.post<Hospital>('/hospitals', data),
};

export const inventoryApi = {
  getAll: (params?: {
    blood_type?: BloodType;
    rh_type?: RhType;
    component?: BloodComponent;
    only_in_stock?: boolean;
  }) => api.get<BloodBag[]>('/inventory', { params }),
  getById: (id: string) => api.get<BloodBag>(`/inventory/${id}`),
  create: (data: Partial<BloodBag>) => api.post<BloodBag>('/inventory', data),
  getExpiringSoon: () => api.get('/inventory/alerts/expiring-soon'),
  getExpired: () => api.get('/inventory/alerts/expired'),
  scrap: (id: string, reason: string) =>
    api.post(`/inventory/${id}/scrap`, null, { params: { reason } }),
};

export const requestApi = {
  getAll: (params?: { status?: any; urgency?: UrgencyLevel }) =>
    api.get<BloodRequest[]>('/requests', { params }),
  getById: (id: string) => api.get<BloodRequest>(`/requests/${id}`),
  create: (data: Partial<BloodRequest>) =>
    api.post<BloodRequest>('/requests', data),
  match: (requestId: string) =>
    api.post<MatchResult>('/requests/match', { request_id: requestId } as MatchRequest),
  cancel: (id: string) => api.post(`/requests/${id}/cancel`),
};

export const dispatchApi = {
  getAll: (params?: { status?: any }) =>
    api.get<Dispatch[]>('/dispatches', { params }),
  getById: (id: string) => api.get<Dispatch>(`/dispatches/${id}`),
  confirm: (
    requestId: string,
    matchedItems: MatchResultItem[],
    courier?: string,
    notes?: string
  ) =>
    api.post<Dispatch>('/dispatches/confirm', matchedItems, {
      params: { request_id: requestId, courier, notes },
    }),
  startTransit: (id: string, courier?: string) =>
    api.post(`/dispatches/${id}/start-transit`, null, { params: { courier } }),
  confirmDelivery: (id: string) =>
    api.post(`/dispatches/${id}/confirm-delivery`),
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
  }) => api.get('/compatibility/check', { params }),
  getCompatibleDonors: (params: {
    recipient_blood_type: BloodType;
    recipient_rh_type: RhType;
    component: BloodComponent;
    is_emergency?: boolean;
  }) => api.get('/compatibility/compatible-donors', { params }),
};

export default api;
