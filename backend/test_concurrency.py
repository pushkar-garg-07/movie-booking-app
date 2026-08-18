import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from database import AsyncSessionLocal, engine
from models import Base
from seed import seed


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    # Fresh seed for test runs
    await seed()
    yield


@pytest.mark.asyncio
async def test_auth_and_seat_locking_concurrency():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register User 1 & User 2
        await client.post(
            "/auth/register",
            json={"name": "User One", "email": "user1@example.com", "password": "password123"},
        )
        await client.post(
            "/auth/register",
            json={"name": "User Two", "email": "user2@example.com", "password": "password123"},
        )

        # 2. Login to retrieve access tokens
        login1 = await client.post(
            "/auth/login",
            data={"username": "user1@example.com", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        login2 = await client.post(
            "/auth/login",
            data={"username": "user2@example.com", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert login1.status_code == 200, f"Login 1 failed: {login1.text}"
        assert login2.status_code == 200, f"Login 2 failed: {login2.text}"

        token1 = login1.json()["access_token"]
        token2 = login2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # 3. Get Layout to pick a target Seat ID
        layout_res = await client.get("/showtimes/1/seats")
        assert layout_res.status_code == 200
        first_seat = layout_res.json()["grid"][0][0]
        seat_id = first_seat["seat_id"]

        # 4. User 1 locks the seat (Must Succeed)
        lock_res = await client.post(
            "/bookings/lock-seats",
            json={"showtime_id": 1, "seat_ids": [seat_id]},
            headers=headers1,
        )
        assert lock_res.status_code == 200
        assert seat_id in lock_res.json()["locked_seat_ids"]

        # 5. User 2 attempts to lock the exact same seat (Must Fail due to lock conflict)
        conflict_res = await client.post(
            "/bookings/lock-seats",
            json={"showtime_id": 1, "seat_ids": [seat_id]},
            headers=headers2,
        )
        assert conflict_res.status_code in (400, 409)
     # 6. User 1 confirms the booking
        confirm_res = await client.post(
         "/bookings/confirm",
         json={"showtime_id": 1, "seat_ids": [seat_id]},
         headers=headers1,
     )
        assert confirm_res.status_code in (200, 201)
        
        # 7. Verify seat status is permanently updated to BOOKED
        final_layout = await client.get("/showtimes/1/seats")
        updated_seat = final_layout.json()["grid"][0][0]
        assert updated_seat["status"] == "BOOKED"