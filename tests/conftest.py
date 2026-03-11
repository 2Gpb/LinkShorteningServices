from unittest.mock import AsyncMock, Mock

import pytest

from links.service import LinkService

@pytest.fixture
def mock_repository():
    return Mock(
        get_by_short_code=AsyncMock(),
        get_by_original_url=AsyncMock(),
        get_by_user_id=AsyncMock(),
        get_top_links=AsyncMock(),
        create=AsyncMock(),
        update_original_url=AsyncMock(),
        increment_click_stats=AsyncMock(),
        delete_by_short_code=AsyncMock(),
        save_expired_link=AsyncMock(),
        get_expired_links=AsyncMock(),
    )


@pytest.fixture
def mock_cache_service():
    return Mock(
        get_redirect_data=AsyncMock(),
        set_redirect_data=AsyncMock(),
        delete_redirect_url=AsyncMock(),
    )


@pytest.fixture
def link_service(mock_repository, mock_cache_service):
    return LinkService(mock_repository, mock_cache_service)
