# Route to capture payment after PayPal approval
from flask import redirect, url_for
import json
from dotenv import load_dotenv
from flask import Flask, render_template
from paypal import authenticate, create_order, capture_payment
from flask import request

load_dotenv()
 
app = Flask("Beggers Website")
 
@app.route('/')
def home():
    return app.send_static_file('index.html')
 
 

# Accept both GET and POST for flexibility
@app.route('/donate', methods=['GET', 'POST'])
def donate():
    # Try to get amount from form (POST) or query string (GET)
    amount = request.form.get('amount') or request.args.get('amount')
    if not amount:
        return "Amount is required", 400
    access_token = authenticate()
    order = create_order(amount=amount, message="Cat Donation", access_token=access_token, server_root=request.url_root)
    # Extract approval_url from PayPal order response
    approval_url = None
    if order and 'links' in order:
        for link in order['links']:
            if link.get('rel') == 'approve':
                approval_url = link.get('href')
                break
    if not approval_url:
        return "Error creating PayPal order", 500
    # Render modal template with amount and approval_url
    return render_template('donate.html', amount=amount, approval_url=approval_url)
 
@app.route('/capture')
def capture():
    order_id = request.args.get('token')  # PayPal returns 'token' as order_id
    if not order_id:
        return "Order ID is required", 400
    access_token = authenticate()
    result = capture_payment(order_id, access_token=access_token)
    # If capture is successful, show thank you modal and redirect
    if result and result.get('status') == 'COMPLETED':
        # List of "Thank you" in 10 different languages (excluding Russian)
        thanks = [
            "Thank you!",           # English
            "Gracias!",            # Spanish
            "Merci!",              # French
            "Danke!",              # German
            "Grazie!",             # Italian
            "Arigatou!",           # Japanese
            "Obrigado!",           # Portuguese
            "Dhanyavaad!",         # Hindi
            "Xièxiè!",             # Chinese
            "Shukran!"             # Arabic
        ]
        return render_template('thankyou.html', thanks=thanks)
    else:
        return "Payment not completed", 400
    
if __name__ == '__main__':
    app.run(debug=True)