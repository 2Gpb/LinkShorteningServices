import time
from datetime import datetime, timedelta, timezone


def test_redirect_success(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://redirect-example.com",
            "custom_alias": "redir1",
        },
    )

    response = client.get("/redir1", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://redirect-example.com/"


def test_redirect_returns_404_for_missing_link(client):
    response = client.get("/missing-link", follow_redirects=False)

    assert response.status_code == 404


def test_redirect_increments_click_count(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://clicks-example.com",
            "custom_alias": "clicks1",
        },
    )

    redirect_response = client.get("/clicks1", follow_redirects=False)
    assert redirect_response.status_code == 307

    stats_response = client.get("/links/clicks1/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["click_count"] == 1
