import json
from unittest import TestCase
import copy

from faker import Faker
from app import app


class TestUserView(TestCase):

    def setUp(self):
        self.data_factory = Faker()
        self.client = app.test_client()

    def test_signup_when_return_susses(self):
        same_password = self.data_factory.password()
        new_user = {
            "username": self.data_factory.user_name(),
            "password1": same_password,
            "password2": same_password,
            "email": self.data_factory.email()
        }

        new_user_request = self.client.post("/api/auth/signup", data=json.dumps(new_user),
                                            headers={'Content-Type': 'application/json'})

        response = json.loads(new_user_request.get_data())

        self.assertEqual(new_user_request.status_code, 200)
        self.assertEqual(response.get("mensaje"), "usuario creado exitosamente.")
        self.assertIsNotNone(response.get("token"))

    def test_signup_when_return_error(self):
        same_password = self.data_factory.password()
        new_user = {
            "username": self.data_factory.user_name(),
            "password1": same_password,
            "password2": same_password,
        }

        new_user_request = self.client.post("/api/auth/signup", data=json.dumps(new_user),
                                            headers={'Content-Type': 'application/json'})

        self.assertEqual(new_user_request.status_code, 400)

    def test_signup_when_return_error_with_different_password(self):
        new_user = {
            "username": self.data_factory.user_name(),
            "password1": self.data_factory.password(),
            "password2": self.data_factory.password(),
            "email": self.data_factory.email()
        }

        new_user_request = self.client.post("/api/auth/signup", data=json.dumps(new_user),
                                            headers={'Content-Type': 'application/json'})

        response = json.loads(new_user_request.get_data())

        self.assertEqual(new_user_request.status_code, 400)
        self.assertEqual(response.get("mensaje"), "Las contraseñas no coinciden.")

    def test_signup_when_return_error_with_same_email(self):
        same_password = self.data_factory.password()
        same_email = self.data_factory.email()
        new_user = {
            "username": self.data_factory.user_name(),
            "password1": same_password,
            "password2": same_password,
            "email": same_email
        }

        new_user_request = self.client.post("/api/auth/signup", data=json.dumps(new_user),
                                            headers={'Content-Type': 'application/json'})

        self.assertEqual(new_user_request.status_code, 200)

        new_user_2 = copy.deepcopy(new_user)
        new_user_2.update({"username": self.data_factory.user_name()})

        new_user_2_request = self.client.post("/api/auth/signup", data=json.dumps(new_user_2),
                                              headers={'Content-Type': 'application/json'})
        response_2 = json.loads(new_user_2_request.get_data())

        self.assertEqual(new_user_2_request.status_code, 400)
        self.assertEqual(response_2.get("mensaje"), "El email ya se encuentra registrado.")
