"""
Tests for SQLite to PostgreSQL migration script and sequence handling.
"""
import unittest
import os
import sqlite3
from flask import Flask

from manage_db import migrate_from_sqlite
from models.vehicle_model import db, User, Vehicle, Prediction, Alert


class TestAppConfig:
    TESTING = True
    SECRET_KEY = 'test-secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False


class TestMigration(unittest.TestCase):

    def setUp(self):
        # Create a temporary source SQLite DB
        self.temp_sqlite = os.path.abspath('temp_test_source.db')
        conn = sqlite3.connect(self.temp_sqlite)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE vehicles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                vehicle_number TEXT NOT NULL,
                vehicle_model TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                mileage REAL DEFAULT 0,
                engine_temp REAL DEFAULT 90,
                oil_quality REAL DEFAULT 80,
                tire_pressure REAL DEFAULT 32,
                brake_condition REAL DEFAULT 80,
                battery_health REAL DEFAULT 85,
                fuel_efficiency REAL DEFAULT 30,
                service_history INTEGER DEFAULT 1,
                last_service_date TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE predictions (
                id INTEGER PRIMARY KEY,
                vehicle_id INTEGER NOT NULL,
                health_score REAL NOT NULL,
                maintenance_required BOOLEAN DEFAULT 0,
                risk_level TEXT DEFAULT 'LOW',
                urgency TEXT DEFAULT 'ROUTINE',
                failure_components TEXT DEFAULT '[]',
                recommendations TEXT DEFAULT '[]',
                estimated_cost REAL DEFAULT 0,
                accuracy REAL DEFAULT 94.5,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY,
                vehicle_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'INFO',
                is_read BOOLEAN DEFAULT 0,
                created_at TEXT
            )
        """)

        # Insert test data
        cur.execute("INSERT INTO users VALUES (1, 'migrated_user', 'migrated@vmps.ai', 'hash123', '2024-01-01T00:00:00')")
        cur.execute("INSERT INTO vehicles VALUES (10, 1, 'MH-01-MIG-1', 'Civic', 'Honda', 50000, 90, 80, 32, 80, 85, 30, 2, '2024-01-01', '2024-01-01T00:00:00', '2024-01-01T00:00:00')")
        cur.execute("INSERT INTO predictions VALUES (100, 10, 88.5, 0, 'LOW', 'ROUTINE', '[\"None\"]', '[]', 0, 95.0, '2024-01-01T00:00:00')")
        cur.execute("INSERT INTO alerts VALUES (1000, 10, 'Test Alert', 'INFO', 0, '2024-01-01T00:00:00')")
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.temp_sqlite):
            os.remove(self.temp_sqlite)

    def test_migrate_from_sqlite_execution(self):
        """Test that data transfers and IDs are preserved."""
        # Use an isolated SQLite target DB to simulate the target PostgreSQL/production DB
        target_db_path = os.path.abspath('temp_target.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{target_db_path.replace(os.sep, "/")}'

        try:
            migrate_from_sqlite(sqlite_path=self.temp_sqlite, force=True)

            # Connect to target and check records
            from app import create_app
            target_app = create_app()
            with target_app.app_context():
                user = User.query.filter_by(username='migrated_user').first()
                self.assertIsNotNone(user)
                self.assertEqual(user.id, 1)

                vehicle = Vehicle.query.filter_by(vehicle_number='MH-01-MIG-1').first()
                self.assertIsNotNone(vehicle)
                self.assertEqual(vehicle.id, 10)
                self.assertEqual(vehicle.user_id, 1)

                pred = Prediction.query.filter_by(vehicle_id=10).first()
                self.assertIsNotNone(pred)
                self.assertEqual(pred.id, 100)
                self.assertEqual(pred.health_score, 88.5)

                alert = Alert.query.filter_by(vehicle_id=10).first()
                self.assertIsNotNone(alert)
                self.assertEqual(alert.id, 1000)
        finally:
            with target_app.app_context():
                db.session.remove()
                db.engine.dispose()
            if 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']
            try:
                if os.path.exists(target_db_path):
                    os.remove(target_db_path)
            except OSError:
                pass


if __name__ == '__main__':
    unittest.main()
