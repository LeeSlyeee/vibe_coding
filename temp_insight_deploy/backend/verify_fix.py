import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_fix():
    print("🚀 Starting Verification...")
    
    # 1. Login (Magic Login)
    # accounts/views.py CustomTokenObtainPairView allows "app_slyeee" without password check if configured
    # Or just use "slyeee" with standard magic login if implemented.
    # Code says: if username and (username.startswith('app_') or username == 'slyeee'): ...
    
    login_url = f"{BASE_URL}/v1/auth/login/"
    # Password can be anything for magic login
    resp = requests.post(login_url, json={"username": "app_slyeee", "password": "any"})
    
    if resp.status_code != 200:
        print(f"❌ Login Failed: {resp.status_code} {resp.text}")
        return

    data = resp.json()
    token = data.get("access")
    print(f"✅ Login Success. Token: {token[:10]}...")
    
    # Debug: Check logic in login response itself (it returns user data too)
    user_data = data.get("user", {})
    print(f"   [Login Response] center_code: {user_data.get('center_code')}")
    print(f"   [Login Response] linked_center_code: {user_data.get('linked_center_code')}")

    # 2. Call Me
    headers = {"Authorization": f"Bearer {token}"}
    me_url = f"{BASE_URL}/user/me"
    me_resp = requests.get(me_url, headers=headers)
    
    if me_resp.status_code != 200:
        print(f"❌ Me API Failed: {me_resp.status_code} {me_resp.text}")
        return
        
    me_data = me_resp.json()
    print(f"✅ Me API Response: {json.dumps(me_data, indent=2, ensure_ascii=False)}")
    
    cc = me_data.get("center_code")
    lcc = me_data.get("linked_center_code")
    
    if cc == "IV7L90SYBT" or lcc == "IV7L90SYBT":
        print("\n🎉 VERIFICATION PASSED: Center Code is present.")
    else:
        print("\n🔥 VERIFICATION FAILED: Center Code is missing or wrong.")

if __name__ == "__main__":
    test_fix()
