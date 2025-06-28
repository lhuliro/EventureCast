import requests
import json
import os

def authenticate(client_id: str = os.environ.get('PAYPAL_CLIENT_ID'), client_secret: str = os.environ.get('PAYPAL_CLIENT_SECRET'), sandbox: bool = True) -> str:
    auth_response = requests.post(
        'https://api-m.sandbox.paypal.com/v1/oauth2/token',
        headers={'Accept': 'application/json', 'Accept-Language': 'en_US'},
        data={'grant_type': 'client_credentials'},
        auth=(client_id, client_secret)
    )
    if auth_response.status_code != 200:
        print(f"Auth Response: {json.dumps(auth_response.json(), indent=2)}")
        return None
    return auth_response.json()['access_token']


def create_order(amount: float, message: str = None, access_token: str = None, server_root: str = "http://localhost:5000/") -> dict:
    if not access_token:
        return {"error": "Missing access token"}

    order_payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "EUR",
                "value": str(amount)
            },
            "description": str(message) if message else "Donation"
        }],
        "application_context": {
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
            "return_url": server_root.rstrip('/') + '/capture',
            "cancel_url": server_root.rstrip('/') + '/error.html'
        }
    }

    order_response = requests.post(
        'https://api-m.sandbox.paypal.com/v2/checkout/orders',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        },
        json=order_payload
    )

    if order_response.status_code != 201:
        print(f"Order Response: {json.dumps(order_response.json(), indent=2)}")
        return None

    return order_response.json()    


def capture_payment(order_id: str, access_token: str = None) -> dict:
    if not access_token:
        return {"error": "Missing access token"}
    if not order_id:
        return {"error": "Missing order ID"}
    capture_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture'
    response = requests.post(
        capture_url,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
    )
    if response.status_code != 201:
        print(f"Capture Response: {json.dumps(response.json(), indent=2)}")
        return None
    return response.json()