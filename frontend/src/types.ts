export enum BloodType {
  A = 'A',
  B = 'B',
  AB = 'AB',
  O = 'O',
}

export enum RhType {
  POSITIVE = 'POSITIVE',
  NEGATIVE = 'NEGATIVE',
}

export enum BloodComponent {
  RBC = 'RBC',
  PLASMA = 'PLASMA',
  PLATELET = 'PLATELET',
  CRYOPRECIPITATE = 'CRYOPRECIPITATE',
}

export enum BagStatus {
  PENDING_TEST = 'PENDING_TEST',
  IN_STOCK = 'IN_STOCK',
  DISPATCHED = 'DISPATCHED',
  SCRAPPED = 'SCRAPPED',
}

export enum UrgencyLevel {
  ROUTINE = 'ROUTINE',
  URGENT = 'URGENT',
  EMERGENCY = 'EMERGENCY',
}

export enum RequestStatus {
  PENDING = 'PENDING',
  PARTIAL_MATCHED = 'PARTIAL_MATCHED',
  FULLY_MATCHED = 'FULLY_MATCHED',
  DISPATCHED = 'DISPATCHED',
  CANCELLED = 'CANCELLED',
}

export enum DispatchStatus {
  PREPARING = 'PREPARING',
  IN_TRANSIT = 'IN_TRANSIT',
  DELIVERED = 'DELIVERED',
}

export interface Hospital {
  id: string;
  name: string;
  address?: string;
  contact_person?: string;
  contact_phone?: string;
  is_blood_center: boolean;
  created_at: string;
  updated_at: string;
}

export interface BloodBag {
  id: string;
  bag_number: string;
  blood_type: BloodType;
  rh_type: RhType;
  component: BloodComponent;
  collection_date: string;
  expiry_date: string;
  volume_ml: number;
  status: BagStatus;
  location?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  days_to_expiry?: number;
}

export interface BloodRequest {
  id: string;
  request_number: string;
  hospital_id: string;
  patient_blood_type: BloodType;
  patient_rh_type: RhType;
  component: BloodComponent;
  quantity_units: number;
  urgency: UrgencyLevel;
  patient_name?: string;
  patient_age?: number;
  diagnosis?: string;
  status: RequestStatus;
  requested_at: string;
  matched_units: number;
  notes?: string;
  created_at: string;
  updated_at: string;
  hospital?: Hospital;
}

export interface MatchResultItem {
  blood_bag_id: string;
  bag_number: string;
  blood_type: BloodType;
  rh_type: RhType;
  component: BloodComponent;
  expiry_date: string;
  days_to_expiry: number;
  is_emergency_compatibility: boolean;
}

export interface MatchResult {
  request_id: string;
  request_number: string;
  matched_items: MatchResultItem[];
  total_matched: number;
  quantity_needed: number;
  is_fully_matched: boolean;
}

export interface InventoryStats {
  blood_type: BloodType;
  rh_type: RhType;
  component: BloodComponent;
  total_units: number;
  expiring_soon: number;
  expired: number;
}

export interface DashboardStats {
  total_inventory: number;
  total_requests_pending: number;
  total_dispatches_in_transit: number;
  expiring_soon_count: number;
  expired_count: number;
  inventory_by_type: InventoryStats[];
  urgent_requests: BloodRequest[];
}

export interface Dispatch {
  id: string;
  dispatch_number: string;
  hospital_id: string;
  status: DispatchStatus;
  total_units: number;
  dispatched_at?: string;
  delivered_at?: string;
  courier?: string;
  temperature_requirement?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  hospital?: Hospital;
  items?: DispatchItem[];
}

export interface DispatchItem {
  id: string;
  dispatch_id: string;
  request_id: string;
  blood_bag_id: string;
  is_emergency_compatibility: boolean;
  created_at: string;
  blood_bag?: BloodBag;
}
