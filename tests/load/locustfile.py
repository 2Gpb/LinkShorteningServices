from uuid import uuid4
from locust import HttpUser, between, task


class LinkShortenerUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.short_code = None

        alias = f"load-{uuid4().hex[:8]}"

        with self.client.post(
            "/links/shorten",
            json={
                "original_url": "https://example.com",
                "custom_alias": alias,
            },
            catch_response=True,
            name="POST /links/shorten (setup)",
        ) as response:

            if response.status_code == 201:
                self.short_code = response.json()["short_code"]
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(3)
    def create_short_link(self):
        alias = f"alias-{uuid4().hex[:10]}"

        with self.client.post(
            "/links/shorten",
            json={
                "original_url": f"https://example.com/{uuid4().hex}",
                "custom_alias": alias,
            },
            catch_response=True,
            name="POST /links/shorten",
        ) as response:

            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(5)
    def redirect_cached_link(self):
        if not self.short_code:
            return

        with self.client.get(
            f"/{self.short_code}",
            allow_redirects=False,
            catch_response=True,
            name="GET /{short_code}",
        ) as response:

            if response.status_code == 307:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def get_top_links(self):
        with self.client.get(
            "/links/top?num=10",
            catch_response=True,
            name="GET /links/top",
        ) as response:

            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                