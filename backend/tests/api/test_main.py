from httpx import AsyncClient


async def test_root_returns_welcome_message(async_client: AsyncClient):
    response = await async_client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Ai Assistant Showcase API"}
