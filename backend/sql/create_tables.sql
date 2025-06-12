-- ゲスト情報
CREATE TABLE guests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    hotel_name VARCHAR(200),
    pickup_lat DECIMAL(10, 8),
    pickup_lng DECIMAL(11, 8),
    num_adults INTEGER DEFAULT 1,
    num_children INTEGER DEFAULT 0,
    preferred_pickup_start TIME,
    preferred_pickup_end TIME,
    phone VARCHAR(20),
    email VARCHAR(100),
    special_requirements TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 車両情報
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    capacity_adults INTEGER NOT NULL,
    capacity_children INTEGER NOT NULL,
    driver_name VARCHAR(100),
    driver_phone VARCHAR(20),
    current_lat DECIMAL(10, 8),
    current_lng DECIMAL(11, 8),
    vehicle_type VARCHAR(20) CHECK (vehicle_type IN ('sedan', 'van', 'minibus')),
    fuel_type VARCHAR(20),
    license_plate VARCHAR(20),
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'in_use', 'maintenance')),
    equipment TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ツアー情報
CREATE TABLE tours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tour_date DATE NOT NULL,
    activity_type VARCHAR(50) NOT NULL CHECK (activity_type IN ('snorkeling', 'diving', 'sightseeing', 'kayaking', 'fishing')),
    destination_name VARCHAR(200),
    destination_lat DECIMAL(10, 8),
    destination_lng DECIMAL(11, 8),
    departure_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'planning' CHECK (status IN ('planning', 'confirmed', 'in_progress', 'completed', 'cancelled')),
    optimization_strategy VARCHAR(20) DEFAULT 'balanced',
    weather_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ツアー参加者（多対多の中間テーブル）
CREATE TABLE tour_participants (
    tour_id UUID REFERENCES tours(id) ON DELETE CASCADE,
    guest_id UUID REFERENCES guests(id) ON DELETE CASCADE,
    pickup_order INTEGER,
    actual_pickup_time TIME,
    PRIMARY KEY (tour_id, guest_id)
);

-- 最適化結果
CREATE TABLE optimized_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tour_id UUID REFERENCES tours(id) ON DELETE CASCADE,
    vehicle_id UUID REFERENCES vehicles(id),
    route_order INTEGER,
    total_distance_km DECIMAL(10, 2),
    total_time_minutes INTEGER,
    efficiency_score DECIMAL(3, 2),
    route_data JSONB, -- 詳細なルート情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_tours_date ON tours(tour_date);
CREATE INDEX idx_tours_status ON tours(status);
CREATE INDEX idx_guests_hotel ON guests(hotel_name);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_optimized_routes_tour ON optimized_routes(tour_id);

-- 更新日時の自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_guests_updated_at BEFORE UPDATE ON guests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON vehicles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tours_updated_at BEFORE UPDATE ON tours
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();