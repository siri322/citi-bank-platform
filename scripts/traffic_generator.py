import requests
import time
import random
import threading

PAYMENT_SERVICE_URL = "http://localhost:8000/pay"

# We know these accounts are hardcoded in the account-service
ACCOUNTS = ["acc_123", "acc_456", "acc_789", "invalid_acc"]

def generate_traffic():
    while True:
        account_id = random.choice(ACCOUNTS)
        amount = round(random.uniform(10.0, 1000.0), 2)
        
        payload = {
            "account_id": account_id,
            "amount": amount
        }
        
        try:
            response = requests.post(PAYMENT_SERVICE_URL, json=payload)
            print(f"[{response.status_code}] Payment for {account_id}: ${amount}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            
        # Simulate traffic volume (1 to 5 requests per second per thread)
        time.sleep(random.uniform(0.2, 1.0))

if __name__ == "__main__":
    print("Starting traffic generator...")
    # Run 5 threads to simulate multiple concurrent users
    threads = []
    for i in range(5):
        t = threading.Thread(target=generate_traffic)
        t.daemon = True
        t.start()
        threads.append(t)
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping traffic generator.")
