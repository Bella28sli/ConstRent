# -*- coding: utf-8 -*-
import os
import random

from faker import Faker
from locust import HttpUser, TaskSet, between, task

fake = Faker("ru_RU")

USERNAME = os.environ.get("LOCUST_USER", "admin")
PASSWORD = os.environ.get("LOCUST_PASS", "admin123")
CLIENT_ID = int(os.environ.get("LOCUST_CLIENT_ID", "1"))
ADDRESS_ID = int(os.environ.get("LOCUST_ADDRESS_ID", "1"))
MODEL_ID = int(os.environ.get("LOCUST_MODEL_ID", "1"))
BRAND_ID = int(os.environ.get("LOCUST_BRAND_ID", "1"))
COUNTRY_ID = int(os.environ.get("LOCUST_COUNTRY_ID", "1"))


class ClientsTasks(TaskSet):
    @task(5)
    def list_clients(self):
        self.client.get("/api/clients/")

    @task(5)
    def list_individual_clients(self):
        self.client.get("/api/indclients/")

    @task(1)
    def create_individual_client(self):
        email = fake.unique.email()
        phone = fake.unique.msisdn()
        client_payload = {"email": email, "phone_number": phone, "type": "individual"}
        resp = self.client.post(
            "/api/clients/",
            json=client_payload,
            headers=self.user.csrf_headers(),
        )

        client_id = None
        if getattr(resp, "ok", False):
            try:
                client_id = resp.json().get("id")
            except ValueError:
                client_id = None
        if not client_id:
            client_id = CLIENT_ID

        ind_payload = {
            "client": client_id,
            "last_name": fake.last_name(),
            "first_name": fake.first_name(),
            "patronymic": fake.middle_name(),
            "passport_number": fake.unique.numerify("##########"),
            "passport_issued_by": fake.company(),
            "passport_issued_date": fake.date_between(start_date="-10y", end_date="-1y").isoformat(),
            "passport_code": fake.numerify("######"),
            "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=65).isoformat(),
            "registration_address": ADDRESS_ID,
            "actual_address": ADDRESS_ID,
            "inn": fake.numerify("##########"),
        }
        self.client.post(
            "/api/indclients/",
            json=ind_payload,
            headers=self.user.csrf_headers(),
        )


class EquipmentTasks(TaskSet):
    @task(5)
    def list_equipment(self):
        self.client.get("/api/equipment/")

    @task(1)
    def create_equipment(self):
        equipment_payload = {
            "equipment_name": fake.sentence(nb_words=3).rstrip("."),
            "equipment_code": f"LC-{fake.unique.bothify('??##??##')}",
            "description": fake.sentence(nb_words=8),
            "model": MODEL_ID,
            "country": COUNTRY_ID,
            "brand": BRAND_ID,
            "power": round(random.uniform(5.0, 300.0), 2),
            "weight": round(random.uniform(50.0, 5000.0), 2),
            "fuel_type": random.choice(["petrol", "diesel", "electric", "hybrid", "gas", "other"]),
            "rental_price_day": round(random.uniform(500.0, 20000.0), 2),
            "status": random.choice(["available", "rented", "maintenance"]),
        }
        resp = self.client.post(
            "/api/equipment/",
            json=equipment_payload,
            headers=self.user.csrf_headers(),
            catch_response=True,
        )
        if resp.status_code == 403:
            print("403 body:", resp.text)



class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    tasks = [ClientsTasks, EquipmentTasks]

    def on_start(self):
        self._csrf_token = ""
        resp = self.client.get("/accounts/login/")
        self._csrf_token = resp.cookies.get("csrftoken", "")
        print("login:", resp.status_code, resp.cookies.get("csrftoken"))
        self.client.post(
            "/accounts/login/",
            {
                "username": USERNAME,
                "password": PASSWORD,
                "csrfmiddlewaretoken": self._csrf_token,
            },
            headers={"X-CSRFToken": self._csrf_token, "Referer": "/accounts/login/"},
        )
        self._csrf_token = self.client.cookies.get("csrftoken", "") or self._csrf_token
        print("sessionid:", self.client.cookies.get("sessionid"))


    def csrf_headers(self):
        token = self.client.cookies.get("csrftoken", "") or self._csrf_token
        if not token:
            return {}
        return {"X-CSRFToken": token, "Referer": "/"}
