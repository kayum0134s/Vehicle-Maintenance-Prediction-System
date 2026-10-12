"""
Tests for SQLAlchemy models: User, Vehicle, Prediction, Alert.
"""
import unittest
import json
from datetime import datetime
from flask import Flask

from models.vehicle_model import db, User, Vehicle, Prediction, Alert


class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_creation_and_to_dict(self):
        with self.app.app_context():
            user = User(
                username="testdriver",
                email="testdriver@example.com",
                password_hash="hashed_pw_123"
            )
            db.session.add(user)
            db.session.commit()

            fetched = User.query.filter_by(username="testdriver").first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.email, "testdriver@example.com")

            data = fetched.to_dict()
            self.assertEqual(data["username"], "testdriver")
            self.assertIn("created_at", data)

    def test_vehicle_creation_and_relationship(self):
        with self.app.app_context():
            user = User(
                username="owner1",
                email="owner1@example.com",
                password_hash="hashed"
            )
            db.session.add(user)
            db.session.commit()

            vehicle = Vehicle(
                user_id=user.id,
                vehicle_number="CA-99-ZZ-0001",
                vehicle_model="Model 3",
                manufacturer="Tesla",
                mileage=15000,
                engine_temp=89.5,
                oil_quality=92.0,
                tire_pressure=34.0,
                brake_condition=88.0,
                battery_health=95.0,
                fuel_efficiency=40.0
            )
            db.session.add(vehicle)
            db.session.commit()

            self.assertEqual(len(user.vehicles), 1)
            self.assertEqual(user.vehicles[0].vehicle_number, "CA-99-ZZ-0001")

            v_dict = vehicle.to_dict()
            self.assertEqual(v_dict["vehicle_number"], "CA-99-ZZ-0001")
            self.assertEqual(v_dict["mileage"], 15000)

    def test_prediction_and_alert_lifecycle(self):
        with self.app.app_context():
            user = User(username="u2", email="u2@example.com", password_hash="h")
            db.session.add(user)
            db.session.commit()

            vehicle = Vehicle(
                user_id=user.id,
                vehicle_number="NY-10-AA-1111",
                vehicle_model="Accord",
                manufacturer="Honda"
            )
            db.session.add(vehicle)
            db.session.commit()

            pred = Prediction(
                vehicle_id=vehicle.id,
                health_score=45.0,
                maintenance_required=True,
                risk_level="HIGH",
                urgency="HIGH",
                failure_components=json.dumps(["Brake System"]),
                recommendations=json.dumps([{"action": "Replace Brake Pads", "priority": "HIGH"}]),
                estimated_cost=250.0,
                accuracy=95.0
            )
            db.session.add(pred)

            alert = Alert(
                vehicle_id=vehicle.id,
                message="Brake pads severely worn",
                severity="WARNING"
            )
            db.session.add(alert)
            db.session.commit()

            # Verify predictions and alerts loaded
            self.assertEqual(len(vehicle.predictions), 1)
            self.assertEqual(len(vehicle.alerts), 1)

            pred_data = pred.to_dict()
            self.assertEqual(pred_data["failure_components"], ["Brake System"])
            self.assertEqual(len(pred_data["recommendations"]), 1)

            alert_data = alert.to_dict()
            self.assertEqual(alert_data["severity"], "WARNING")
            self.assertFalse(alert_data["is_read"])


if __name__ == '__main__':
    unittest.main()
