from datetime import datetime, timedelta, timezone


def test_create_short_link_anonymous_success(client):
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "custom_alias": "example1",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "example1"
    assert data["owner_id"] is None


def test_create_short_link_authenticated_success(client, auth_helpers):
    auth_helpers.register()
    auth_helpers.login()

    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "custom_alias": "example2",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "example2"
    assert data["owner_id"] is not None


def test_create_short_link_with_duplicate_alias_returns_400(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "custom_alias": "dup-alias",
        },
    )

    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.org",
            "custom_alias": "dup-alias",
        },
    )

    assert response.status_code == 400


def test_create_short_link_with_invalid_url_returns_422(client):
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "not-a-url",
            "custom_alias": "badurl",
        },
    )

    assert response.status_code == 422


def test_create_short_link_with_past_expires_at_returns_400(client):
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://expired.com",
            "custom_alias": "expired-alias",
            "expires_at": past_time,
        },
    )

    assert response.status_code == 400


def test_search_link_by_original_url_success(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://search-example.com",
            "custom_alias": "search1",
        },
    )

    response = client.get("/links/search", params={"original_url": "https://search-example.com/"})

    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "search1"


def test_search_link_by_original_url_returns_404_if_missing(client):
    response = client.get("/links/search", params={"original_url": "https://missing.com"})

    assert response.status_code == 404


def test_get_link_stats_success(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://stats-example.com",
            "custom_alias": "stats1",
        },
    )

    response = client.get("/links/stats1/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://stats-example.com/"
    assert data["click_count"] == 0


def test_get_link_stats_returns_404_if_missing(client):
    response = client.get("/links/missing/stats")

    assert response.status_code == 404


def test_get_my_links_requires_auth(client):
    response = client.get("/links/my")

    assert response.status_code == 401


def test_get_my_links_success(client, auth_helpers):
    auth_helpers.register()
    auth_helpers.login()

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://my-links-example.com",
            "custom_alias": "mylink1",
        },
    )

    response = client.get("/links/my")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["short_code"] == "mylink1"


def test_get_top_links_success(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://top-example.com",
            "custom_alias": "top1",
        },
    )

    response = client.get("/links/top", params={"num": 10})

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_top_links_invalid_limit_returns_400(client):
    response = client.get("/links/top", params={"num": 0})

    assert response.status_code == 400


def test_check_alias_returns_true_for_free_alias(client):
    response = client.get("/links/check-alias/freealias")

    assert response.status_code == 200
    assert response.json()["available"] is True


def test_check_alias_returns_false_for_taken_alias(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://alias-example.com",
            "custom_alias": "takenalias",
        },
    )

    response = client.get("/links/check-alias/takenalias")

    assert response.status_code == 200
    assert response.json()["available"] is False


def test_get_expired_links_requires_auth(client):
    response = client.get("/links/expired")

    assert response.status_code == 401


def test_get_expired_links_returns_empty_list_for_new_user(client, auth_helpers):
    auth_helpers.register()
    auth_helpers.login()

    response = client.get("/links/expired")

    assert response.status_code == 200
    assert response.json() == []


def test_update_link_requires_auth(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://update-example.com",
            "custom_alias": "upd1",
        },
    )

    response = client.put(
        "/links/upd1",
        json={"original_url": "https://updated-example.com"},
    )

    assert response.status_code == 401


def test_update_link_success_for_owner(client, auth_helpers):
    auth_helpers.register()
    auth_helpers.login()

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://update-owner.com",
            "custom_alias": "upd2",
        },
    )

    response = client.put(
        "/links/upd2",
        json={"original_url": "https://updated-owner.com"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://updated-owner.com/"


def test_update_link_forbidden_for_non_owner(client, auth_helpers):
    auth_helpers.register(email="owner@example.com", username="owner")
    auth_helpers.login(email="owner@example.com")

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://owner-link.com",
            "custom_alias": "ownerlink",
        },
    )

    auth_helpers.logout()
    auth_helpers.register(email="other@example.com", username="other")
    auth_helpers.login(email="other@example.com")

    response = client.put(
        "/links/ownerlink",
        json={"original_url": "https://other-update.com"},
    )

    assert response.status_code == 403


def test_update_link_returns_404_if_missing(client, auth_helpers):
    auth_helpers.register()
    auth_helpers.login()

    response = client.put(
        "/links/missinglink",
        json={"original_url": "https://updated.com"},
    )

    assert response.status_code == 404


def test_delete_link_requires_auth(client):
    client.post(
        "/links/shorten",
        json={
            "original_url": "https://delete-example.com",
            "custom_alias": "del1",
        },
    )

    response = client.delete("/links/del1")

    assert response.status_code == 401


def test_delete_link_success_for_owner(client, auth_helpers):
    auth_helpers.register()
    auth_helpers.login()

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://delete-owner.com",
            "custom_alias": "del2",
        },
    )

    response = client.delete("/links/del2")

    assert response.status_code == 204


def test_delete_link_forbidden_for_non_owner(client, auth_helpers):
    auth_helpers.register(email="owner2@example.com", username="owner2")
    auth_helpers.login(email="owner2@example.com")

    client.post(
        "/links/shorten",
        json={
            "original_url": "https://owner-delete.com",
            "custom_alias": "delowner",
        },
    )

    auth_helpers.logout()
    auth_helpers.register(email="other2@example.com", username="other2")
    auth_helpers.login(email="other2@example.com")

    response = client.delete("/links/delowner")

    assert response.status_code == 403


def test_delete_link_returns_404_if_missing(client, auth_helpers):
    auth_helpers.register()
    auth_helpers.login()

    response = client.delete("/links/missinglink")

    assert response.status_code == 404