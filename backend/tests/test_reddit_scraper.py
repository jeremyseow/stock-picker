import pytest
from unittest.mock import AsyncMock, MagicMock
from app.reddit_scraper import (
    RedditOAuthClient,
    RedditAuthError,
    get_target_subreddits,
)


@pytest.mark.asyncio
async def test_missing_credentials_raises_auth_error(monkeypatch):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)

    with pytest.raises(RedditAuthError, match="credentials missing"):
        RedditOAuthClient(client_id=None, client_secret=None)


@pytest.mark.asyncio
async def test_invalid_credentials_rejected_by_reddit():
    client = RedditOAuthClient(client_id="fake_id", client_secret="fake_secret")
    
    mock_http_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 401
    mock_res.text = "Unauthorized"
    mock_http_client.post.return_value = mock_res

    with pytest.raises(RedditAuthError, match="authentication rejected"):
        await client.get_access_token(mock_http_client)


@pytest.mark.asyncio
async def test_token_caching_and_reuse():
    client = RedditOAuthClient(client_id="valid_id", client_secret="valid_secret")
    
    mock_http_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "access_token": "mock_token_123",
        "expires_in": 3600,
        "token_type": "bearer",
    }
    mock_http_client.post.return_value = mock_res

    # First call: makes HTTP POST
    token1 = await client.get_access_token(mock_http_client)
    assert token1 == "mock_token_123"
    assert mock_http_client.post.call_count == 1

    # Second call: returns cached token without HTTP POST
    token2 = await client.get_access_token(mock_http_client)
    assert token2 == "mock_token_123"
    assert mock_http_client.post.call_count == 1


@pytest.mark.asyncio
async def test_fetch_subreddit_posts_preserves_score_and_metadata():
    client = RedditOAuthClient(client_id="valid_id", client_secret="valid_secret")
    client._access_token = "mock_token"
    client._token_expires_at = 9999999999.0

    mock_http_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers = {"x-ratelimit-remaining": "99", "x-ratelimit-reset": "60"}
    mock_res.json.return_value = {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "post_1",
                        "title": "NVDA Earnings Discussion",
                        "selftext": "Long calls on NVDA",
                        "score": 523,
                        "num_comments": 84,
                        "upvote_ratio": 0.94,
                        "subreddit": "wallstreetbets",
                        "stickied": False,
                    }
                },
                {
                    "data": {
                        "id": "stickied_mod_post",
                        "title": "Rules of the subreddit",
                        "selftext": "Don't break rules",
                        "score": 10,
                        "stickied": True,
                    }
                }
            ]
        }
    }
    mock_http_client.get.return_value = mock_res

    posts = await client.fetch_subreddit_posts("wallstreetbets", mock_http_client)

    # Stickied post must be filtered out
    assert len(posts) == 1
    post = posts[0]
    assert post["id"] == "post_1"
    assert post["title"] == "NVDA Earnings Discussion"
    assert post["score"] == 523
    assert post["num_comments"] == 84
    assert post["upvote_ratio"] == 0.94
    assert post["subreddit"] == "wallstreetbets"


@pytest.mark.asyncio
async def test_fetch_comments_preserves_score():
    client = RedditOAuthClient(client_id="valid_id", client_secret="valid_secret")
    client._access_token = "mock_token"
    client._token_expires_at = 9999999999.0

    mock_http_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers = {}
    mock_res.json.return_value = [
        {"data": {"children": []}},  # Post listing
        {
            "data": {
                "children": [
                    {
                        "kind": "t1",
                        "data": {
                            "id": "c1",
                            "body": "AAPL looks undervalued here",
                            "score": 42,
                            "author": "trader1",
                        }
                    },
                    {
                        "kind": "t1",
                        "data": {
                            "id": "c2",
                            "body": "[deleted]",
                            "score": 1,
                            "author": "[deleted]",
                        }
                    }
                ]
            }
        }
    ]
    mock_http_client.get.return_value = mock_res

    comments = await client.fetch_post_comments("post_1", "wallstreetbets", mock_http_client)
    assert len(comments) == 1
    assert comments[0]["id"] == "c1"
    assert comments[0]["score"] == 42
    assert comments[0]["body"] == "AAPL looks undervalued here"


def test_target_subreddits_default_and_custom(monkeypatch):
    monkeypatch.delenv("REDDIT_SUBREDDITS", raising=False)
    assert get_target_subreddits() == ["wallstreetbets", "stocks", "ValueInvesting"]

    monkeypatch.setenv("REDDIT_SUBREDDITS", "r/stocks, options, r/investing")
    assert get_target_subreddits() == ["stocks", "options", "investing"]


@pytest.mark.asyncio
async def test_save_retail_social_raw():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.future import select
    from app.database import Base
    from app.models import RetailSocialRaw
    from app.crud import save_retail_social_raw

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    candidate_items = [
        {
            "ticker": "NVDA",
            "engagement_score": 1250.0,
            "mention_count": 14,
            "context_text": "[POST | Score: 200]: NVIDIA Blackwell ramp continues.",
        }
    ]

    async with async_session() as db:
        await save_retail_social_raw(db, candidate_items)

        result = await db.execute(select(RetailSocialRaw).where(RetailSocialRaw.ticker == "NVDA"))
        row = result.scalar_one()
        assert row.ticker == "NVDA"
        assert row.title == "Reddit discussions for NVDA"
        assert row.score == 1250
        assert row.comment_count == 14
        assert "Blackwell ramp" in row.post_body

    await engine.dispose()


