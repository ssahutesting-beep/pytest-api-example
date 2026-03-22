from jsonschema import validate
import pytest
import schemas
import api_helpers
from hamcrest import assert_that, contains_string, is_
from app import app


@pytest.fixture(scope="session")
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def create_order(client):
    # Create an order for testing
    response = client.post('/store/order', json={'pet_id': 0})
    assert response.status_code == 201
    order_data = response.get_json()
    validate(instance=order_data, schema=schemas.order)
    return order_data['id']

def test_patch_order_by_id(client, create_order):
    order_id = create_order
    
    # Test updating order status to 'sold'
    update_data = {'status': 'sold'}
    response = client.patch(f'/store/order/{order_id}', json=update_data)
    
    # Validate response code
    assert response.status_code == 200
    
    # Validate response message
    response_data = response.get_json()
    validate(instance=response_data, schema=schemas.order_patch_response)
    assert response_data['message'] == "Order and pet status updated successfully"
    
    # Validate the order was updated
    # Get the order (assuming there's a GET endpoint, but since there isn't, we can check the pet status)
    # For now, just check that the response is correct
    # Optional: Validate against schema if we had an order schema
    # But since the response is just a message, no need
