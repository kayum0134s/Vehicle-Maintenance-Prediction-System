"""
Tests for API routes, authentication, predictions, and dashboard.
"""
import unittest
import json
from app import create_app, init_db
from models.vehicle_model import db, User, Vehicle, Prediction, Alert


class TestAppConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key-12345'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False


class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_object=TestAppConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _register_and_login(self):
        # Register
        res = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'testuser@vmps.ai',
            'password': 'password123'
        })
        self.assertEqual(res.status_code, 201)
        return res.get_json()['user']

    def test_health_check_endpoint(self):
        """Verify the health check endpoint returns status."""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'connected')

    def test_auth_flow(self):
        """Test registration, login, me, and logout."""
        # 1. Register
        user = self._register_and_login()
        self.assertEqual(user['username'], 'testuser')

        # 2. Check /api/auth/me
        res_me = self.client.get('/api/auth/me')
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.get_json()['user']['email'], 'testuser@vmps.ai')

        # 3. Logout
        res_out = self.client.post('/api/auth/logout')
        self.assertEqual(res_out.status_code, 200)

        # 4. Check /api/auth/me is now unauthorized
        res_me_after = self.client.get('/api/auth/me')
        self.assertEqual(res_me_after.status_code, 401)

        # 5. Login again
        res_login = self.client.post('/api/auth/login', json={
            'email': 'testuser@vmps.ai',
            'password': 'password123'
        })
        self.assertEqual(res_login.status_code, 200)

    def test_vehicle_crud_and_prediction(self):
        """Test vehicle creation, listing, prediction, updating, and deletion."""
        self._register_and_login()

        # 1. Add vehicle
        vehicle_payload = {
            'vehicle_number': 'MH-12-PQ-9999',
            'vehicle_model': 'Model S',
            'manufacturer': 'Tesla',
            'mileage': 45000,
            'engine_temp': 90,
            'oil_quality': 85,
            'tire_pressure': 33,
            'brake_condition': 82,
            'battery_health': 90,
            'fuel_efficiency': 34,
            'service_history': 3,
            'last_service_date': '2024-10-01'
        }
        res = self.client.post('/api/vehicles', json=vehicle_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        vid = data['vehicle']['id']

        # 2. Get vehicles list
        res_list = self.client.get('/api/vehicles')
        self.assertEqual(res_list.status_code, 200)
        vehicles = res_list.get_json()['vehicles']
        self.assertEqual(len(vehicles), 1)

        # 3. Get single vehicle
        res_get = self.client.get(f'/api/vehicles/{vid}')
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.get_json()['vehicle']['vehicle_number'], 'MH-12-PQ-9999')

        # 4. Run prediction on vehicle
        res_pred = self.client.post(f'/api/vehicles/{vid}/predict', json={})
        self.assertEqual(res_pred.status_code, 200)
        pred_res = res_pred.get_json()['prediction']
        self.assertIn('health_score', pred_res)
        self.assertIn('urgency', pred_res)

        # 5. Fetch prediction history
        res_history = self.client.get(f'/api/vehicles/{vid}/predictions')
        self.assertEqual(res_history.status_code, 200)
        preds = res_history.get_json()['predictions']
        self.assertGreaterEqual(len(preds), 1)

        # 6. Update vehicle
        res_update = self.client.put(f'/api/vehicles/{vid}', json={'mileage': 46000})
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.get_json()['vehicle']['mileage'], 46000)

        # 7. Dashboard analytics
        res_dash = self.client.get('/api/dashboard')
        self.assertEqual(res_dash.status_code, 200)
        dash_data = res_dash.get_json()
        self.assertEqual(dash_data['total_vehicles'], 1)
        self.assertIn('avg_health', dash_data)

        # 8. Delete vehicle
        res_del = self.client.post(f'/api/vehicles/{vid}', method='DELETE') if False else self.client.delete(f'/api/vehicles/{vid}')
        self.assertEqual(res_del.status_code, 200)

        # Confirm deleted
        res_after = self.client.get(f'/api/vehicles/{vid}')
        self.assertEqual(res_after.status_code, 404)

    def test_quick_predict(self):
        """Test quick prediction endpoint."""
        self._register_and_login()
        res = self.client.post('/api/predict/quick', json={
            'vehicle_number': 'TEMP-TEST-01',
            'vehicle_model': 'Civic',
            'manufacturer': 'Honda',
            'mileage': 60000,
            'engine_temp': 95,
            'oil_quality': 70,
            'tire_pressure': 32,
            'brake_condition': 75,
            'battery_health': 80,
            'fuel_efficiency': 28
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('prediction', data)
        self.assertIn('health_score', data['prediction'])

    def test_chatbot_endpoint(self):
        """Test chatbot response."""
        res = self.client.post('/api/chatbot', json={'message': 'how often should I change my oil?'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('reply', res.get_json())


if __name__ == '__main__':
    unittest.main()
