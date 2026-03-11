def test_register_user_success(client, auth_helpers):
    response = auth_helpers.register()

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["username"] == "user1"


def test_login_user_success_sets_cookie(client, auth_helpers):
    auth_helpers.register()

    response = auth_helpers.login()

    assert response.status_code in (200, 204)
    assert "set-cookie" in response.headers


def test_logout_user_success(client, auth_helpers):
    auth_helpers.register()
    auth_helpers.login()

    response = auth_helpers.logout()

    assert response.status_code in (200, 204)