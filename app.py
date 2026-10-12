"""
Vehicle Maintenance Prediction System
Flask Application Entry Point
"""
import os
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, redirect, url_for, session
from flask_cors import CORS
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from config import Config
from models.vehicle_model import db, User, Vehicle, Prediction, Alert
from routes.auth import auth
from routes.api import api

load_dotenv()


def create_app(config_object=None):
    app = Flask(__name__)
    if config_object:
        app.config.from_object(config_object)
        if hasattr(config_object, 'init_app'):
            config_object.init_app(app)
        else:
            app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
            app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    else:
        # Apply validated configuration exactly once before initializing extensions
        Config.init_app(app)

    CORS(app, supports_credentials=True)

    # Prevent SQLite from being initialized on Vercel.
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if os.environ.get('VERCEL') == '1' and database_uri.startswith('sqlite'):
        raise RuntimeError(
            "Vercel is configured to use SQLite. "
            "Set DATABASE_URL to your Supabase PostgreSQL connection string "
            "in Vercel Project Settings > Environment Variables, then redeploy."
        )

    db.init_app(app)

    app.register_blueprint(auth)
    app.register_blueprint(api)

    @app.route('/')
    def index():
        if not session.get('user_id'):
            return redirect(url_for('login_page'))
        return render_template('index.html', username=session.get('username', 'User'))

    @app.route('/login')
    def login_page():
        if session.get('user_id'):
            return redirect(url_for('index'))
        return render_template('login.html')

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint for Vercel deployment and monitoring."""
        db_connected = False
        dialect = 'unknown'
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            db_connected = True
            dialect = db.engine.dialect.name
        except Exception:
            db_connected = False
            if hasattr(db, 'engine') and db.engine:
                try:
                    dialect = db.engine.dialect.name
                except Exception:
                    dialect = 'uninitialized'

        return {
            'status': 'healthy' if db_connected else 'degraded',
            'database': 'connected' if db_connected else 'disconnected',
            'dialect': dialect
        }, (200 if db_connected else 503)

    @app.cli.command("init-db")
    def init_db_cmd():
        """Create database tables idempotently."""
        init_db(app)
        print("[OK] Database tables created successfully.")

    @app.cli.command("seed-demo")
    def seed_demo_cmd():
        """Seed demo user and vehicle data."""
        _seed_demo_data(app)
        print("[OK] Demo data seeding completed.")

    return app


def init_db(app_instance=None):
    """Safely and idempotently create database tables."""
    target_app = app_instance or app
    with target_app.app_context():
        db.create_all()


def _seed_demo_data(app):
    """Seed realistic demo vehicles for demonstration."""
    
    # pyrefly: ignore [missing-import]
    from werkzeug.security import generate_password_hash
    from models.ml_engine import ml_engine
    import json, random

    with app.app_context():
        if User.query.count() > 0:
            return

        # Create demo user
        demo_user = User(
            username='admin',
            email='admin@vmps.ai',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(demo_user)
        db.session.commit()

        # Demo vehicles
        demo_vehicles = [
            {
                'vehicle_number': 'MH-01-AB-1234',
                'vehicle_model': 'Model S',
                'manufacturer': 'Tesla',
                'mileage': 45000,
                'engine_temp': 88,
                'oil_quality': 82,
                'tire_pressure': 33,
                'brake_condition': 79,
                'battery_health': 91,
                'fuel_efficiency': 35,
                'service_history': 4,
                'last_service_date': '2024-11-15'
            },
            {
                'vehicle_number': 'DL-02-CD-5678',
                'vehicle_model': '5 Series',
                'manufacturer': 'BMW',
                'mileage': 110000,
                'engine_temp': 105,
                'oil_quality': 28,
                'tire_pressure': 28,
                'brake_condition': 35,
                'battery_health': 52,
                'fuel_efficiency': 18,
                'service_history': 8,
                'last_service_date': '2024-05-20'
            },
            {
                'vehicle_number': 'KA-03-EF-9012',
                'vehicle_model': 'F-150',
                'manufacturer': 'Ford',
                'mileage': 180000,
                'engine_temp': 118,
                'oil_quality': 12,
                'tire_pressure': 25,
                'brake_condition': 18,
                'battery_health': 21,
                'fuel_efficiency': 10,
                'service_history': 12,
                'last_service_date': '2023-09-01'
            },
            {
                'vehicle_number': 'TN-04-GH-3456',
                'vehicle_model': 'Civic',
                'manufacturer': 'Honda',
                'mileage': 62000,
                'engine_temp': 91,
                'oil_quality': 67,
                'tire_pressure': 31,
                'brake_condition': 68,
                'battery_health': 74,
                'fuel_efficiency': 28,
                'service_history': 6,
                'last_service_date': '2024-09-10'
            },
        ]

        for vdata in demo_vehicles:
            vehicle = Vehicle(user_id=demo_user.id, **vdata)
            db.session.add(vehicle)
            db.session.commit()

            result = ml_engine.predict(vdata)
            pred = Prediction(
                vehicle_id=vehicle.id,
                health_score=result['health_score'],
                maintenance_required=result['maintenance_required'],
                risk_level=result['risk_level'],
                urgency=result['urgency'],
                failure_components=json.dumps([result['failure_component']]),
                recommendations=json.dumps(result['recommendations']),
                estimated_cost=result['estimated_cost'],
                accuracy=result['accuracy']
            )
            db.session.add(pred)

            if result['urgency'] in ('CRITICAL', 'HIGH'):
                alert = Alert(
                    vehicle_id=vehicle.id,
                    message=f"Vehicle {vehicle.vehicle_number}: {result['failure_component']} — {result['urgency']}",
                    severity='CRITICAL' if result['urgency'] == 'CRITICAL' else 'WARNING'
                )
                db.session.add(alert)

        db.session.commit()
        print("[OK] Demo data seeded: 1 user, 4 vehicles, predictions and alerts created.")
        print("[INFO] Login: admin@vmps.ai / admin123")


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            init_db(app)
            _seed_demo_data(app)
        except Exception as e:
            print(f"[WARN] Local startup database check: {e}")

    print("[VMPS] Vehicle Maintenance Prediction System starting...")
    print("[VMPS] Open browser at: http://localhost:5000")
    print("[VMPS] Demo login: admin@vmps.ai / admin123")
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=5000)
