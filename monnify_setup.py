#!/usr/bin/env python3
"""
Monnify Setup Helper - Get your contract code
"""
import requests
import base64
import json
from config import Config

def get_monnify_details():
    """Get merchant details from Monnify API"""
    
    api_key = Config.MONNIFY_API_KEY
    secret_key = Config.MONNIFY_SECRET_KEY
    base_url = Config.MONNIFY_BASE_URL
    
    print("🔐 Authenticating with Monnify...")
    
    # Generate auth token
    auth_string = f"{api_key}:{secret_key}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {auth_b64}'
    }
    
    try:
        # Login to get access token
        response = requests.post(
            f'{base_url}/api/v1/auth/login',
            headers=headers
        )
        data = response.json()
        
        print(f"Login response: {json.dumps(data, indent=2)}")
        
        if data.get('requestSuccessful'):
            access_token = data['responseBody']['accessToken']
            print(f"✅ Login successful!")
            
            # Try to get reserved account details (shows contract info)
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            # Try the transactions endpoint to verify connection
            trans_response = requests.get(
                f'{base_url}/api/v1/transactions/search',
                headers=headers,
                params={'page': 0, 'size': 1}
            )
            trans_data = trans_response.json()
            print(f"\nTransactions test: {json.dumps(trans_data, indent=2)[:500]}...")
            
            print("\n" + "="*50)
            print("📝 MANUAL SETUP REQUIRED")
            print("="*50)
            print("\n1. Log in to your Monnify Dashboard:")
            print("   https://sandbox.monnify.com or https://app.monnify.com")
            print("\n2. Go to: Settings → API Keys & Webhooks")
            print("\n3. Find your 'Contract Code' (usually starts with numbers)")
            print("\n4. Update config.py with:")
            print(f"   MONNIFY_CONTRACT_CODE = 'YOUR_CONTRACT_CODE_HERE'")
            print("\n5. Set webhook URL to:")
            print("   https://your-domain.com/webhook/monnify")
            print("\n6. Select events: SUCCESSFUL_TRANSACTION, FAILED_TRANSACTION")
            print("="*50)
            
        else:
            print(f"❌ Login failed: {data.get('responseMessage', 'Unknown error')}")
            print(f"Full response: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    get_monnify_details()
