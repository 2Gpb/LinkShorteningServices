from datetime import datetime, timedelta, timezone

import pytest

from links.exception import (
    InvalidExpiresAtError,
    ShortCodeAlreadyExistsError,
    ShortCodeGenerationError,
)
from links.schemas import LinkCreate


def make_link_create(
    original_url: str = "https://example.com",
    custom_alias: str | None = None,
    expires_at: datetime | None = None,
) -> LinkCreate:
    return LinkCreate(
        original_url=original_url,
        custom_alias=custom_alias,
        expires_at=expires_at,
    )


def test_generate_short_code_returns_string_of_default_length(link_service):
    short_code = link_service._generate_short_code()

    assert isinstance(short_code, str)
    assert len(short_code) == 6
    assert short_code.isalnum()


@pytest.mark.asyncio
async def test_generate_unique_short_code_returns_first_unique_value(link_service, mock_repository, mocker):
    mocker.patch.object(link_service, "_generate_short_code", side_effect=["abc123"])
    mock_repository.get_by_short_code.return_value = None

    result = await link_service._generate_unique_short_code()

    assert result == "abc123"
    mock_repository.get_by_short_code.assert_awaited_once_with("abc123")


@pytest.mark.asyncio
async def test_generate_unique_short_code_retries_until_unique(link_service, mock_repository, mocker):
    mocker.patch.object(
        link_service,
        "_generate_short_code",
        side_effect=["taken1", "taken2", "free01"],
    )
    mock_repository.get_by_short_code.side_effect = [
        {"short_code": "taken1"},
        {"short_code": "taken2"},
        None,
    ]

    result = await link_service._generate_unique_short_code()

    assert result == "free01"
    assert mock_repository.get_by_short_code.await_count == 3


@pytest.mark.asyncio
async def test_generate_unique_short_code_raises_after_10_attempts(link_service, mock_repository, mocker):
    mocker.patch.object(link_service, "_generate_short_code", return_value="takenxx")
    mock_repository.get_by_short_code.return_value = {"short_code": "takenxx"}

    with pytest.raises(ShortCodeGenerationError, match="Failed to generate unique short code"):
        await link_service._generate_unique_short_code()


@pytest.mark.asyncio
async def test_create_link_with_generated_short_code(link_service, mock_repository, mocker):
    data = make_link_create()
    mocker.patch.object(link_service, "_generate_unique_short_code", return_value="abc123")
    mock_repository.get_by_short_code.return_value = None
    mock_repository.create.return_value = {
        "id": 1,
        "original_url": "https://example.com",
        "short_code": "abc123",
        "owner_id": 1,
    }

    result = await link_service.create_link(data, owner_id=1)

    assert result["short_code"] == "abc123"
    mock_repository.create.assert_awaited_once()
    kwargs = mock_repository.create.await_args.kwargs
    assert kwargs["original_url"] == "https://example.com/"
    assert kwargs["short_code"] == "abc123"
    assert kwargs["owner_id"] == 1
    assert kwargs["expires_at"] is None


@pytest.mark.asyncio
async def test_create_link_with_custom_alias(link_service, mock_repository):
    data = make_link_create(custom_alias="myalias")
    mock_repository.get_by_short_code.return_value = None
    mock_repository.create.return_value = {
        "id": 1,
        "original_url": "https://example.com",
        "short_code": "myalias",
        "owner_id": None,
    }

    result = await link_service.create_link(data)

    assert result["short_code"] == "myalias"
    kwargs = mock_repository.create.await_args.kwargs
    assert kwargs["short_code"] == "myalias"


@pytest.mark.asyncio
async def test_create_link_raises_if_short_code_already_exists(link_service, mock_repository):
    data = make_link_create(custom_alias="busyalias")
    mock_repository.get_by_short_code.return_value = {"short_code": "busyalias"}

    with pytest.raises(ShortCodeAlreadyExistsError, match="Short code already exists"):
        await link_service.create_link(data)


@pytest.mark.asyncio
async def test_create_link_raises_if_expires_at_in_past(link_service, mock_repository):
    past_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    data = make_link_create(expires_at=past_time)
    mock_repository.get_by_short_code.return_value = None

    with pytest.raises(InvalidExpiresAtError, match="expires_at must be in the future"):
        await link_service.create_link(data)


@pytest.mark.asyncio
async def test_check_alias_returns_true_when_alias_is_free(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = None

    result = await link_service.check_alias("freealias")

    assert result is True


@pytest.mark.asyncio
async def test_check_alias_returns_false_when_alias_is_taken(link_service, mock_repository):
    mock_repository.get_by_short_code.return_value = {"short_code": "taken"}

    result = await link_service.check_alias("taken")

    assert result is False