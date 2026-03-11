from datetime import datetime, timedelta, timezone

import pytest

from links.exception import LinkExpiredError, LinkNotFoundError


@pytest.mark.asyncio
async def test_redirect_returns_cached_url_on_cache_hit(link_service, mock_repository, mock_cache_service):
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    mock_cache_service.get_redirect_data.return_value = {
        "original_url": "https://example.com/",
        "expires_at": future_time,
    }

    result = await link_service.get_original_url_for_redirect("abc123")

    assert result == "https://example.com/"
    mock_repository.increment_click_stats.assert_awaited_once()
    mock_repository.get_by_short_code.assert_not_awaited()


@pytest.mark.asyncio
async def test_redirect_cache_hit_with_expired_link_moves_to_history_and_raises(
    link_service, mock_repository, mock_cache_service
):
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    mock_cache_service.get_redirect_data.return_value = {
        "original_url": "https://example.com/",
        "expires_at": past_time,
    }
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "original_url": "https://example.com/",
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=10),
        "owner_id": 1,
        "click_count": 5,
        "last_used_at": None,
    }

    with pytest.raises(LinkExpiredError, match="Link has expired"):
        await link_service.get_original_url_for_redirect("abc123")

    mock_repository.save_expired_link.assert_awaited_once()
    mock_repository.delete_by_short_code.assert_awaited_once_with("abc123")
    mock_cache_service.delete_redirect_url.assert_awaited_once_with("abc123")


@pytest.mark.asyncio
async def test_redirect_cache_miss_returns_link_and_sets_cache(link_service, mock_repository, mock_cache_service):
    mock_cache_service.get_redirect_data.return_value = None
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "original_url": "https://example.com/",
        "created_at": datetime.now(timezone.utc),
        "expires_at": None,
        "owner_id": 1,
        "click_count": 5,
        "last_used_at": None,
    }

    result = await link_service.get_original_url_for_redirect("abc123")

    assert result == "https://example.com/"
    mock_repository.increment_click_stats.assert_awaited_once()
    mock_cache_service.set_redirect_data.assert_awaited_once_with(
        short_code="abc123",
        original_url="https://example.com/",
        expires_at=None,
    )


@pytest.mark.asyncio
async def test_redirect_cache_miss_raises_if_link_not_found(link_service, mock_repository, mock_cache_service):
    mock_cache_service.get_redirect_data.return_value = None
    mock_repository.get_by_short_code.return_value = None

    with pytest.raises(LinkNotFoundError, match="Link not found"):
        await link_service.get_original_url_for_redirect("missing")


@pytest.mark.asyncio
async def test_redirect_cache_miss_with_expired_link_moves_to_history_and_raises(
    link_service, mock_repository, mock_cache_service
):
    mock_cache_service.get_redirect_data.return_value = None
    mock_repository.get_by_short_code.return_value = {
        "short_code": "abc123",
        "original_url": "https://example.com/",
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=5),
        "owner_id": 1,
        "click_count": 5,
        "last_used_at": None,
    }

    with pytest.raises(LinkExpiredError, match="Link has expired"):
        await link_service.get_original_url_for_redirect("abc123")

    mock_repository.save_expired_link.assert_awaited_once()
    mock_repository.delete_by_short_code.assert_awaited_once_with("abc123")
    mock_cache_service.delete_redirect_url.assert_awaited_once_with("abc123")