import random
import time
from pymongo import MongoClient

def generate_random_coordinates(bounds):
    lat = random.uniform(bounds['southwest']['lat'], bounds['northeast']['lat'])
    lng = random.uniform(bounds['southwest']['lng'], bounds['northeast']['lng'])
    return [lng, lat]

def generate_random_users(num_users, bounds):
    users = []
    for i in range(1, num_users + 1):
        user = {
            "user_id": f"User{i:03}",
            "location": {
                "type": "Point",
                "coordinates": generate_random_coordinates(bounds)
            },
            "taxi_preference": random.choice(['Utility', 'Deluxe', 'Luxury', 'Any'])
        }
        users.append(user)
    return users

def simulate_user_requests(users, bounds, db):
    while True:
        user = random.choice(users)
        print(f"User {user['user_id']} at {user['location']['coordinates']} requests a {user['taxi_preference']} taxi.")
        
        # Insert user request into MongoDB
        db.requests.insert_one({
            "user_id": user['user_id'],
            "location": user['location'],
            "taxi_preference": user['taxi_preference'],
            "timestamp": time.time()
        })
        
        time.sleep(random.randint(30, 90))  # Random interval between requests

def run_user_simulator():
    bounds = {
        "southwest": {"lat": 29.677188413138673, "lng": -95.47487010411909},
        "northeast": {"lat": 29.82116771080327, "lng": -95.25459367187106}
    }
    
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://CloudProjectGroup01:dbhEGgjTGz2WjSGk@cluster0.ejz2u2z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['HoustonTaxiDB']

    # Generate initial user data
    users = generate_random_users(5, bounds)
    
    simulate_user_requests(users, bounds, db)

if __name__ == "__main__":
    run_user_simulator()
