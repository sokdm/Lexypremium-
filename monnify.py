import requests
import base64
import json
from datetime import datetime, timedelta
from flask import current_app
from models import Order, db, Notification, MonnifyTransactionLog, Product

class MonnifyAPI:
    def __init__(self):
        self.api_key = current_app.config['MONNIFY_API_KEY']
        self.secret_key = current_app.config['MONNIFY_SECRET_KEY']
        self.base_url = current_app.config['MONNIFY_BASE_URL']
        self.contract_code = current_app.config.get('MONNIFY_CONTRACT_CODE', '')
        self.access_token = None
        
    def _get_auth_token(self):
        """Get Monnify access token"""
        auth_string = f"{self.api_key}:{self.secret_key}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {'Authorization': f'Basic {auth_b64}'}
        
        try:
            response = requests.post(
                f'{self.base_url}/api/v1/auth/login',
                headers=headers,
                timeout=10
            )
            data = response.json()
            
            if data.get('requestSuccessful'):
                self.access_token = data['responseBody']['accessToken']
                return self.access_token
            else:
                print(f"❌ Monnify auth error: {data}")
                return None
        except Exception as e:
            print(f"❌ Monnify auth exception: {e}")
            return None
    
    def _get_headers(self):
        """Get headers with authentication"""
        if not self.access_token:
            self._get_auth_token()
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def reserve_account(self, order, customer_email, customer_name):
        """
        Reserve a virtual account for customer payment
        """
        if not self.contract_code or self.contract_code == 'TEST_CONTRACT_CODE':
            print("⚠️ WARNING: Using test contract code. Get real code from Monnify dashboard.")
            # Return mock data for testing
            return self._create_mock_account(order, customer_name)
        
        headers = self._get_headers()
        
        payment_reference = f"WIG_{order.order_number}_{int(datetime.utcnow().timestamp())}"
        
        payload = {
            "accountReference": payment_reference,
            "accountName": f"LuxeWigs-{order.order_number[:8]}",
            "currencyCode": "NGN",
            "contractCode": self.contract_code,
            "customerEmail": customer_email,
            "customerName": customer_name[:50],  # Max 50 chars
            "getAllAvailableBanks": False,
            "preferredBanks": ["035"],  # Wema Bank (most reliable)
            "incomeSplitConfig": []
        }
        
        try:
            print(f"🔵 Creating reserved account with payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f'{self.base_url}/api/v2/bank-transfer/reserved-accounts',
                headers=headers,
                json=payload,
                timeout=30
            )
            data = response.json()
            
            print(f"🟢 Monnify response: {json.dumps(data, indent=2)}")
            
            if data.get('requestSuccessful') and data.get('responseBody'):
                response_body = data['responseBody']
                
                order.monnify_transaction_reference = response_body.get('accountReference')
                order.monnify_payment_reference = response_body.get('accountReference')
                
                accounts = response_body.get('accounts', [])
                if accounts:
                    account = accounts[0]
                    order.monnify_account_number = account.get('accountNumber')
                    order.monnify_account_name = account.get('accountName')
                    order.monnify_bank_name = account.get('bankName')
                    order.monnify_bank_code = account.get('bankCode')
                
                db.session.commit()
                
                return {
                    'success': True,
                    'account_number': order.monnify_account_number,
                    'account_name': order.monnify_account_name,
                    'bank_name': order.monnify_bank_name,
                    'payment_reference': payment_reference,
                    'accounts': accounts
                }
            else:
                error_msg = data.get('responseMessage', 'Unknown error')
                print(f"❌ Monnify reserve account failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            print(f"❌ Monnify reserve account exception: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_mock_account(self, order, customer_name):
        """Create mock account for testing without real Monnify contract"""
        print("🧪 Creating MOCK account for testing")
        
        mock_ref = f"MOCK_{order.order_number}_{int(datetime.utcnow().timestamp())}"
        
        order.monnify_transaction_reference = mock_ref
        order.monnify_payment_reference = mock_ref
        order.monnify_account_number = "1234567890"  # Fake account
        order.monnify_account_name = f"LuxeWigs-{order.order_number[:8]}"
        order.monnify_bank_name = "Test Bank (Mock)"
        order.monnify_bank_code = "999"
        
        db.session.commit()
        
        return {
            'success': True,
            'account_number': order.monnify_account_number,
            'account_name': order.monnify_account_name,
            'bank_name': order.monnify_bank_name,
            'payment_reference': mock_ref,
            'accounts': [{
                'accountNumber': order.monnify_account_number,
                'accountName': order.monnify_account_name,
                'bankName': order.monnify_bank_name,
                'bankCode': order.monnify_bank_code
            }],
            'mock': True  # Flag indicating this is test data
        }
    
    def get_transaction_status(self, transaction_reference):
        """Get transaction status"""
        if transaction_reference.startswith('MOCK_'):
            # Mock transaction always returns not paid (for testing manual verification)
            return {
                'success': True,
                'paid': False,
                'mock': True,
                'data': {
                    'paymentStatus': 'PENDING',
                    'amount': 0,
                    'message': 'This is a mock transaction. Use admin panel to mark as paid.'
                }
            }
        
        headers = self._get_headers()
        
        try:
            response = requests.get(
                f'{self.base_url}/api/v2/transactions/{transaction_reference}',
                headers=headers,
                timeout=10
            )
            data = response.json()
            
            print(f"Transaction status: {json.dumps(data, indent=2)}")
            
            if data.get('requestSuccessful') and data.get('responseBody'):
                tx_data = data['responseBody']
                return {
                    'success': True,
                    'paid': tx_data.get('paymentStatus') == 'PAID',
                    'amount': tx_data.get('amount'),
                    'data': tx_data
                }
            else:
                return {
                    'success': False,
                    'error': data.get('responseMessage', 'Failed to get status')
                }
                
        except Exception as e:
            print(f"Error checking transaction: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def process_webhook_event(event_data):
    """
    Process Monnify webhook event
    """
    try:
        event_type = event_data.get('eventType')
        event_body = event_data.get('eventData', {})
        
        print(f"📨 Processing webhook: {event_type}")
        
        # Log the webhook
        log = MonnifyTransactionLog(
            event_type=event_type,
            payload=json.dumps(event_data),
            processed=False
        )
        db.session.add(log)
        db.session.commit()
        
        # Handle successful payment
        if event_type == 'SUCCESSFUL_TRANSACTION':
            transaction_reference = event_body.get('transactionReference')
            payment_reference = event_body.get('paymentReference')
            payment_status = event_body.get('paymentStatus')
            amount_paid = event_body.get('amount', 0)
            
            # Find order
            order = Order.query.filter(
                db.or_(
                    Order.monnify_payment_reference == payment_reference,
                    Order.monnify_transaction_reference == transaction_reference
                )
            ).first()
            
            if order and payment_status == 'PAID':
                # Verify amount matches
                if float(amount_paid) >= float(order.total_amount) * 0.99:  # Allow small variance
                    
                    # Update order
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.paid_at = datetime.utcnow()
                    
                    # Update stock
                    for item in order.items:
                        product = Product.query.get(item.product_id)
                        if product:
                            product.stock -= item.quantity
                            product.sold_count += item.quantity
                    
                    # Notifications
                    create_notification(
                        type='email',
                        recipient=order.email,
                        subject=f'Payment Confirmed - Order {order.order_number}',
                        message=f'Your payment of ₦{amount_paid} has been confirmed.'
                    )
                    
                    admin_msg = f"💰 NEW PAYMENT!\n\nOrder: #{order.order_number}\nAmount: ₦{amount_paid}\nCustomer: {order.full_name}"
                    create_notification(
                        type='whatsapp',
                        recipient=current_app.config['WHATSAPP_PHONE_NUMBER'],
                        message=admin_msg
                    )
                    
                    log.processed = True
                    db.session.commit()
                    
                    print(f"✅ Order {order.order_number} auto-processed!")
                    return {
                        'success': True,
                        'message': 'Payment processed',
                        'order_number': order.order_number
                    }
        
        # Handle failed transaction
        elif event_type == 'FAILED_TRANSACTION':
            payment_reference = event_body.get('paymentReference')
            order = Order.query.filter_by(monnify_payment_reference=payment_reference).first()
            
            if order:
                order.payment_status = 'failed'
                order.notes = f"Payment failed: {event_body.get('message', 'Unknown')}"
                db.session.commit()
        
        log.processed = True
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Event logged'
        }
        
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }


def create_notification(type, recipient, message, subject=None):
    """Create notification record"""
    notification = Notification(
        type=type,
        recipient=recipient,
        subject=subject,
        message=message,
        status='pending'
    )
    db.session.add(notification)
    db.session.commit()
    return notification
