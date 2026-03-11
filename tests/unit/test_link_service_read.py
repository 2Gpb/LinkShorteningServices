import pytest

from links.exception import InvalidLimitError, LinkNotFoundError


@pytest.mark.asyncio
async def test_search_by_original_url_returns_link(link_service, mock_repository):
    mock_repository.get_by_original_url.return_value = {"original_url": "https://example.com/"}

    result = await link_service.search_by_original_url("https://example.com/")

    assert result["original_url"] == "https://example.com/"


@pytest.mark.asyncio
async def test_search_by_original_url_raises_if_not_found(link_service, mock_repository):
    mock_repository.get_by_original_url.return_value = None

    with pytest.raises(LinkNotFoundError, match="Link not found"):
        await link_service.search_by_original_url("https://missing.com/")


@pytest.mark.asyncio
async def test_get_stats_returns_link(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = {"short_code": "abc123", "click_count": 5}

    result = await link_service.get_stats("abc123")

    assert result["click_count"] == 5


@pytest.mark.asyncio
async def test_get_stats_raises_if_not_found(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = None

    with pytest.raises(LinkNotFoundError, match="Link not found"):
        await link_service.get_stats("missing")


@pytest.mark.asyncio
async def test_get_user_links_returns_repository_result(link_service, mock_repository):
    mock_repository.get_by_user_id.return_value = [{"id": 1}, {"id": 2}]

    result = await link_service.get_user_links(1)

    assert result == [{"id": 1}, {"id": 2}]


@pytest.mark.asyncio
async def test_get_top_links_returns_repository_result(link_service, mock_repository):
    mock_repository.get_top_links.return_value = [{"short_code": "a"}, {"short_code": "b"}]

    result = await link_service.get_top_links(2)

    assert result == [{"short_code": "a"}, {"short_code": "b"}]
    mock_repository.get_top_links.assert_awaited_once_with(2)


@pytest.mark.asyncio
async def test_get_top_links_raises_if_limit_less_than_one(link_service):
    with pytest.raises(InvalidLimitError, match="Limit must be between 1 and 100"):
        await link_service.get_top_links(0)


@pytest.mark.asyncio
async def test_get_top_links_raises_if_limit_greater_than_100(link_service):
    with pytest.raises(InvalidLimitError, match="Limit must be between 1 and 100"):
        await link_service.get_top_links(101)


@pytest.mark.asyncio
async def test_get_expired_links_returns_repository_result(link_service, mock_repository):
    mock_repository.get_expired_links.return_value = [{"short_code": "expired1"}]

    result = await link_service.get_expired_links(1)

    assert result == [{"short_code": "expired1"}]
    mock_repository.get_expired_links.assert_awaited_once_with(1)