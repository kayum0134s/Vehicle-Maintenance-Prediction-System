"""
Vehicle Maintenance Prediction System (VMPS)
Database Management & Migration CLI Utility

Commands:
  python manage_db.py check-db
  python manage_db.py init-db
  python manage_db.py seed-demo
  python manage_db.py migrate-from-sqlite [path_to_sqlite.db]
"""
import os
import sys
import argparse
import sqlite3
import json
from datetime import datetime
import urllib.parse

from app import create_app, init_db, _seed_demo_data
from models.vehicle_model import db, User, Vehicle, Prediction, Alert


def mask_connection_uri(uri: str) -> str:
    """Mask password and sensitive credentials for safe logging."""
    if not uri:
        return "<not set>"
    try:
        parsed = urllib.parse.urlsplit(uri)
        if parsed.password:
            netloc = f"{parsed.username}:******@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return parsed._replace(netloc=netloc).geturl()
        return uri
    except Exception:
        return "<configured>"


def check_db():
    """Verify database connection and display current row counts."""
    app = create_app()
    with app.app_context():
        raw_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        masked_uri = mask_connection_uri(raw_uri)
        print("=" * 60)
        print(" VMPS Database Diagnostics")
        print("=" * 60)
        print(f"[*] Target URI: {masked_uri}")
        try:
            with db.engine.connect() as conn:
                res = conn.execute(db.text('SELECT 1')).scalar()
                dialect = db.engine.dialect.name
                driver = db.engine.dialect.driver
                print(f"[OK] Connection test successful (SELECT 1 returned {res})")
                print(f"[*] Dialect: {dialect} | Driver: {driver}")

                # Check table counts
                try:
                    users_count = User.query.count()
                    vehicles_count = Vehicle.query.count()
                    pred_count = Prediction.query.count()
                    alert_count = Alert.query.count()

                    print(f"[*] Current records in database:")
                    print(f"    - users:       {users_count}")
                    print(f"    - vehicles:    {vehicles_count}")
                    print(f"    - predictions: {pred_count}")
                    print(f"    - alerts:      {alert_count}")
                except Exception as table_err:
                    print(f"[!] Tables may not be initialized yet: {table_err}")
                    print("    Run: python manage_db.py init-db")
        except Exception as conn_err:
            print(f"[FAIL] Could not connect to database: {conn_err}")
            sys.exit(1)


def initialize_tables():
    """Create all schema tables idempotently."""
    app = create_app()
    with app.app_context():
        print("[*] Initializing database schema...")
        init_db(app)
        print("[OK] All tables (users, vehicles, predictions, alerts) created successfully.")


def seed_demo():
    """Seed demo user and vehicle data if the database has no users."""
    app = create_app()
    with app.app_context():
        print("[*] Seeding demo data...")
        _seed_demo_data(app)


def migrate_from_sqlite(sqlite_path: str = None, force: bool = False):
    """
    Migrate existing records from local SQLite to PostgreSQL/Supabase.
    Preserves primary keys, foreign keys, relationships, and data types.
    Non-destructive: will not overwrite existing rows unless --force is specified.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    if not sqlite_path:
        sqlite_path = os.path.join(base_dir, 'instance', 'vehicle_maintenance.db')

    if not os.path.exists(sqlite_path):
        print(f"[!] SQLite source file not found at: {sqlite_path}")
        return

    print("=" * 60)
    print(" VMPS SQLite to PostgreSQL Data Migration")
    print("=" * 60)
    print(f"[*] SQLite source: {sqlite_path}")

    app = create_app()
    with app.app_context():
        # 1. Ensure target schema exists
        init_db(app)

        # 2. Check if target database already has data
        existing_users = User.query.count()
        if existing_users > 0 and not force:
            print(f"[!] Target database already contains {existing_users} user(s).")
            print("    To prevent duplicate key collisions, migration was skipped.")
            print("    Pass --force if you want to proceed.")
            return

        # 3. Read SQLite data
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        cur = sqlite_conn.cursor()

        try:
            # Users
            users_rows = cur.execute("SELECT * FROM users").fetchall()
            print(f"[*] Found {len(users_rows)} users in SQLite.")
            for row in users_rows:
                row_dict = dict(row)
                created_at = None
                if row_dict.get('created_at'):
                    try:
                        created_at = datetime.fromisoformat(row_dict['created_at'])
                    except Exception:
                        created_at = datetime.utcnow()

                user = User(
                    id=row_dict['id'],
                    username=row_dict['username'],
                    email=row_dict['email'],
                    password_hash=row_dict['password_hash'],
                    created_at=created_at or datetime.utcnow()
                )
                db.session.merge(user)
            db.session.commit()

            # Vehicles
            vehicles_rows = cur.execute("SELECT * FROM vehicles").fetchall()
            print(f"[*] Found {len(vehicles_rows)} vehicles in SQLite.")
            for row in vehicles_rows:
                row_dict = dict(row)
                created_at = None
                updated_at = None
                if row_dict.get('created_at'):
                    try:
                        created_at = datetime.fromisoformat(row_dict['created_at'])
                    except Exception:
                        created_at = datetime.utcnow()
                if row_dict.get('updated_at'):
                    try:
                        updated_at = datetime.fromisoformat(row_dict['updated_at'])
                    except Exception:
                        updated_at = datetime.utcnow()

                vehicle = Vehicle(
                    id=row_dict['id'],
                    user_id=row_dict['user_id'],
                    vehicle_number=row_dict['vehicle_number'],
                    vehicle_model=row_dict['vehicle_model'],
                    manufacturer=row_dict['manufacturer'],
                    mileage=float(row_dict.get('mileage', 0)),
                    engine_temp=float(row_dict.get('engine_temp', 90)),
                    oil_quality=float(row_dict.get('oil_quality', 80)),
                    tire_pressure=float(row_dict.get('tire_pressure', 32)),
                    brake_condition=float(row_dict.get('brake_condition', 80)),
                    battery_health=float(row_dict.get('battery_health', 85)),
                    fuel_efficiency=float(row_dict.get('fuel_efficiency', 30)),
                    service_history=int(row_dict.get('service_history', 1)),
                    last_service_date=row_dict.get('last_service_date'),
                    created_at=created_at or datetime.utcnow(),
                    updated_at=updated_at or datetime.utcnow()
                )
                db.session.merge(vehicle)
            db.session.commit()

            # Predictions
            pred_rows = cur.execute("SELECT * FROM predictions").fetchall()
            print(f"[*] Found {len(pred_rows)} predictions in SQLite.")
            for row in pred_rows:
                row_dict = dict(row)
                created_at = None
                if row_dict.get('created_at'):
                    try:
                        created_at = datetime.fromisoformat(row_dict['created_at'])
                    except Exception:
                        created_at = datetime.utcnow()

                pred = Prediction(
                    id=row_dict['id'],
                    vehicle_id=row_dict['vehicle_id'],
                    health_score=float(row_dict.get('health_score', 80)),
                    maintenance_required=bool(row_dict.get('maintenance_required', False)),
                    risk_level=row_dict.get('risk_level', 'LOW'),
                    urgency=row_dict.get('urgency', 'ROUTINE'),
                    failure_components=row_dict.get('failure_components', '[]'),
                    recommendations=row_dict.get('recommendations', '[]'),
                    estimated_cost=float(row_dict.get('estimated_cost', 0)),
                    accuracy=float(row_dict.get('accuracy', 94.5)),
                    created_at=created_at or datetime.utcnow()
                )
                db.session.merge(pred)
            db.session.commit()

            # Alerts
            alert_rows = cur.execute("SELECT * FROM alerts").fetchall()
            print(f"[*] Found {len(alert_rows)} alerts in SQLite.")
            for row in alert_rows:
                row_dict = dict(row)
                created_at = None
                if row_dict.get('created_at'):
                    try:
                        created_at = datetime.fromisoformat(row_dict['created_at'])
                    except Exception:
                        created_at = datetime.utcnow()

                alert = Alert(
                    id=row_dict['id'],
                    vehicle_id=row_dict['vehicle_id'],
                    message=row_dict.get('message', ''),
                    severity=row_dict.get('severity', 'INFO'),
                    is_read=bool(row_dict.get('is_read', False)),
                    created_at=created_at or datetime.utcnow()
                )
                db.session.merge(alert)
            db.session.commit()

            # 4. Synchronize PostgreSQL sequence values so subsequent INSERTs do not collide
            if db.engine.dialect.name == 'postgresql':
                print("[*] Synchronizing PostgreSQL sequence counters...")
                with db.engine.connect() as conn:
                    for table in ['users', 'vehicles', 'predictions', 'alerts']:
                        try:
                            seq = conn.execute(db.text(f"SELECT pg_get_serial_sequence('{table}', 'id')")).scalar()
                            if seq:
                                conn.execute(db.text(f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM {table}), 1))"))
                                conn.commit()
                        except Exception as seq_err:
                            print(f"[!] Notice: sequence synchronization for {table}: {seq_err}")

            print("[OK] Migration finished successfully!")
            print(f"     Transferred {len(users_rows)} users, {len(vehicles_rows)} vehicles, {len(pred_rows)} predictions, {len(alert_rows)} alerts.")

        except Exception as e:
            db.session.rollback()
            print(f"[FAIL] Migration error: {e}")
            raise
        finally:
            sqlite_conn.close()


def main():
    parser = argparse.ArgumentParser(description="VMPS Database Management Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("check-db", help="Test database connection and show row counts")
    subparsers.add_parser("init-db", help="Create all database tables idempotently")
    subparsers.add_parser("seed-demo", help="Seed initial demo vehicles and user")

    migrate_p = subparsers.add_parser("migrate-from-sqlite", help="Transfer records from SQLite to PostgreSQL")
    migrate_p.add_argument("--sqlite-path", type=str, default=None, help="Path to SQLite database file")
    migrate_p.add_argument("--force", action="store_true", help="Migrate even if target database contains records")

    args = parser.parse_args()

    if args.command == "check-db":
        check_db()
    elif args.command == "init-db":
        initialize_tables()
    elif args.command == "seed-demo":
        seed_demo()
    elif args.command == "migrate-from-sqlite":
        migrate_from_sqlite(sqlite_path=args.sqlite_path, force=args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
