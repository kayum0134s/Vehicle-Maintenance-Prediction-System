-- =============================================================================
-- Vehicle Maintenance Prediction System (VMPS)
-- Supabase PostgreSQL Database Schema
--
-- How to apply:
-- 1. Open your Supabase Dashboard: https://supabase.com/dashboard/project/<your-project-ref>
-- 2. Go to the "SQL Editor" section on the left navigation.
-- 3. Click "New query", paste the contents of this file, and click "Run".
-- =============================================================================

-- 1. Users Table
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 2. Vehicles Table
CREATE TABLE IF NOT EXISTS public.vehicles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    vehicle_number VARCHAR(50) NOT NULL,
    vehicle_model VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    mileage DOUBLE PRECISION DEFAULT 0,
    engine_temp DOUBLE PRECISION DEFAULT 90,
    oil_quality DOUBLE PRECISION DEFAULT 80,
    tire_pressure DOUBLE PRECISION DEFAULT 32,
    brake_condition DOUBLE PRECISION DEFAULT 80,
    battery_health DOUBLE PRECISION DEFAULT 85,
    fuel_efficiency DOUBLE PRECISION DEFAULT 30,
    service_history INTEGER DEFAULT 1,
    last_service_date VARCHAR(20),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 3. Predictions Table
CREATE TABLE IF NOT EXISTS public.predictions (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES public.vehicles(id) ON DELETE CASCADE,
    health_score DOUBLE PRECISION NOT NULL,
    maintenance_required BOOLEAN DEFAULT FALSE,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    urgency VARCHAR(20) DEFAULT 'ROUTINE',
    failure_components TEXT DEFAULT '[]',
    recommendations TEXT DEFAULT '[]',
    estimated_cost DOUBLE PRECISION DEFAULT 0,
    accuracy DOUBLE PRECISION DEFAULT 94.5,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 4. Alerts Table
CREATE TABLE IF NOT EXISTS public.alerts (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES public.vehicles(id) ON DELETE CASCADE,
    message VARCHAR(500) NOT NULL,
    severity VARCHAR(20) DEFAULT 'INFO',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_vehicles_user_id ON public.vehicles(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_vehicle_id ON public.predictions(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON public.predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_vehicle_id ON public.alerts(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON public.alerts(created_at DESC);

-- Permissions Note:
-- The Flask backend connects using the standard connection string (role: postgres).
-- If Row Level Security (RLS) is enabled in Supabase, ensure service-level access
-- or policies allow the connecting user to perform SELECT/INSERT/UPDATE/DELETE.
