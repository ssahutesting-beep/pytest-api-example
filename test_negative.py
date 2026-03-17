import uuid
from copy import deepcopy

import pytest

from app import app, orders, pets


INITIAL_PETS = deepcopy(pets)


def assert_error_response(response, expected_status, expected_message):
    assert response.status_code == expected_status
    assert expected_message in response.get_json()["message"]


@pytest.fixture(scope="session")
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_app_state():
    orders.clear()
    pets[:] = deepcopy(INITIAL_PETS)


@pytest.fixture
def create_order(client):
    def _create_order(pet_id=2):
        response = client.post("/store/order", json={"pet_id": pet_id})
        assert response.status_code == 201
        return response.get_json()["id"]

    return _create_order


@pytest.mark.parametrize(
    ("query_string", "expected_status", "expected_message"),
    [
        ({"status": "unknown"}, 400, "Invalid pet status"),
        ({}, 400, "Invalid pet status"),
    ],
)
def test_find_by_status_negative_cases(client, query_string, expected_status, expected_message):
    response = client.get("/pets/findByStatus", query_string=query_string)

    assert_error_response(response, expected_status, expected_message)


@pytest.mark.parametrize(
    ("payload", "expected_status", "expected_message"),
    [
        ({"pet_id": 9999}, 404, "No pet found"),
        ({}, 400, "must include pet_id"),
        ({"pet_id": "abc"}, 400, "pet_id must be an integer"),
        ({"pet_id": 1}, 400, "is not available for order"),
    ],
)
def test_create_order_negative_cases(client, payload, expected_status, expected_message):
    response = client.post("/store/order", json=payload)

    assert_error_response(response, expected_status, expected_message)


def test_patch_unknown_order_404(client):
    missing_order_id = str(uuid.uuid4())

    response = client.patch(f"/store/order/{missing_order_id}", json={"status": "sold"})

    assert_error_response(response, 404, "Order not found")


@pytest.mark.parametrize(
    ("payload", "use_json", "expected_status", "expected_message"),
    [
        ({"status": "archived"}, True, 400, "Invalid status"),
        ({}, True, 400, "must include status"),
        (None, False, 400, "must include status"),
    ],
)
def test_patch_order_negative_cases(
    client, create_order, payload, use_json, expected_status, expected_message
):
    order_id = create_order()
    request_kwargs = {"json": payload} if use_json else {}

    response = client.patch(f"/store/order/{order_id}", **request_kwargs)

    assert_error_response(response, expected_status, expected_message)


def test_create_pet_duplicate_id_409(client):
    duplicate_pet = {
        "id": 0,
        "name": "copycat",
        "type": "cat",
        "status": "available",
    }

    response = client.post("/pets/", json=duplicate_pet)

    assert_error_response(response, 409, "already exists")


@pytest.mark.parametrize(
    ("payload", "expected_status", "expected_message"),
    [
        ({"id": 10, "type": "cat", "status": "available"}, 400, "include name and type"),
        ({"id": 11, "name": "copycat", "status": "available"}, 400, "include name and type"),
        ({"id": 12, "name": "copycat", "type": "bird", "status": "available"}, 400, "Invalid pet type"),
    ],
)
def test_create_pet_invalid_payloads(client, payload, expected_status, expected_message):
    response = client.post("/pets/", json=payload)

    assert_error_response(response, expected_status, expected_message)
