import requests

headers = {
    'Authorization': 'Bearer test_token', # replace later if real test
    'Content-Type': 'application/json'
}

data = {
    "fcm_token": "test_fcm",
    "platform": "ios",
    "apns_token": "cd9d43f3ffd3afa4c7242ca653f2f1f19248139f8c0fd0c008bea5c8083b08f9"
}

# Just using the local script on remote to push via FCM 
