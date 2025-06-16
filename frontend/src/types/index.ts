// ツアー関連の型定義
export interface Tour {
  id: string;
  tour_date: string;
  activity_type: ActivityType;
  destination_name: string;
  destination_lat: number;
  destination_lng: number;
  departure_time: string;
  status: TourStatus;
  optimization_strategy: string;
  weather_data?: any;
  created_at?: string;
  updated_at?: string;
  participants: TourParticipant[];
  optimized_routes: OptimizedRoute[];
  total_participants: number;
  total_vehicles_used: number;
}

export type ActivityType = 'snorkeling' | 'diving' | 'sightseeing' | 'kayaking' | 'fishing';

export type TourStatus = 'planning' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled';

export interface TourParticipant {
  guest_id: string;
  guest_name: string;
  hotel_name?: string;
  pickup_order?: number;
  actual_pickup_time?: string;
}

export interface OptimizedRoute {
  vehicle_id: string;
  vehicle_name: string;
  route_order: number;
  total_distance_km: number;
  total_time_minutes: number;
  efficiency_score: number;
  route_data: any;
}

// ゲスト関連の型定義
export interface Guest {
  id: string;
  name: string;
  hotel_name?: string;
  pickup_lat?: number;
  pickup_lng?: number;
  num_adults: number;
  num_children: number;
  preferred_pickup_start?: string;
  preferred_pickup_end?: string;
  phone?: string;
  email?: string;
  special_requirements: string[];
}

// 車両関連の型定義
export interface Vehicle {
  id: string;
  name: string;
  capacity_adults: number;
  capacity_children: number;
  driver_name?: string;
  driver_phone?: string;
  current_lat?: number;
  current_lng?: number;
  vehicle_type?: 'sedan' | 'van' | 'minibus';
  fuel_type?: string;
  license_plate?: string;
  status?: 'available' | 'in_use' | 'maintenance';
  equipment: string[];
}

// API レスポンスの型定義
export interface TourListResponse {
  tours: Tour[];
  total: number;
  skip: number;
  limit: number;
}

export interface OptimizationJobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  estimated_completion_seconds?: number;
  progress_percentage: number;
  result?: any;
  error_message?: string;
}