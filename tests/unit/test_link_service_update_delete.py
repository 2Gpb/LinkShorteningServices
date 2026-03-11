import pytest

from links.exception import AccessDeniedError, LinkNotFoundError
from links.schemas import LinkUpdate


def make_link_update(original_url: str = "https://new-example.com") -> LinkUpdate:
    return LinkUpdate(original_url=original_url)


@pytest.mark.asyncio
async def test_update_link_success(link_service, mock_repository, mock_cache_service):
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "owner_id": 1,
    }
    mock_repository.update_original_url.return_value = {
        "short_code": "abc123",
        "original_url": "https://new-example.com/",
    }

    result = await link_service.update_link("abc123", make_link_update(), user_id=1)

    assert result["original_url"] == "https://new-example.com/"
    mock_repository.update_original_url.assert_awaited_once_with(
        short_code="abc123",
        new_original_url="https://new-example.com/",
    )
    mock_cache_service.delete_redirect_url.assert_awaited_once_with("abc123")


@pytest.mark.asyncio
async def test_update_link_raises_if_not_found(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = None

    with pytest.raises(LinkNotFoundError, match="Link not found"):
        await link_service.update_link("missing", make_link_update(), user_id=1)


@pytest.mark.asyncio
async def test_update_link_raises_if_user_is_not_owner(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "owner_id": 2,
    }

    with pytest.raises(AccessDeniedError, match="You cannot update this link"):
        await link_service.update_link("abc123", make_link_update(), user_id=1)


@pytest.mark.asyncio
async def test_update_link_raises_if_repository_returns_none_after_update(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "owner_id": 1,
    }
    mock_repository.update_original_url.return_value = None

    with pytest.raises(LinkNotFoundError, match="Link not found"):
        await link_service.update_link("abc123", make_link_update(), user_id=1)


@pytest.mark.asyncio
async def test_delete_link_success(link_service, mock_repository, mock_cache_service):
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "owner_id": 1,
    }
    mock_repository.delete_by_short_code.return_value = True

    result = await link_service.delete_link("abc123", user_id=1)

    assert result is None
    mock_repository.delete_by_short_code.assert_awaited_once_with("abc123")
    mock_cache_service.delete_redirect_url.assert_awaited_once_with("abc123")


@pytest.mark.asyncio
async def test_delete_link_raises_if_not_found(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = None

    with pytest.raises(LinkNotFoundError, match="Link not found"):
        await link_service.delete_link("missing", user_id=1)


@pytest.mark.asyncio
async def test_delete_link_raises_if_user_is_not_owner(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "owner_id": 2,
    }

    with pytest.raises(AccessDeniedError, match="You cannot delete this link"):
        await link_service.delete_link("abc123", user_id=1)


@pytest.mark.asyncio
async def test_delete_link_raises_if_repository_delete_returns_false(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "owner_id": 1,
    }
    mock_repository.delete_by_short_code.return_value = False

    with pytest.raises(LinkNotFoundError, match="Link not found"):
        await link_service.delete_link("abc123", user_id=1)