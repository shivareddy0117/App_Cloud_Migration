import random
import time
from pymongo import MongoClient

def generate_random_coordinates(bounds):
    lat = random.uniform(bounds['southwest']['lat'], bounds['northeast']['lat'])
    lng = random.uniform(bounds['southwest']['lng'], bounds['northeast']['lng'])
    return [lng, lat]

def generate_random_taxis(num_taxis, bounds):
    taxi_types = ['Utility', 'Deluxe', 'Luxury']
    taxis = []
    for i in range(1, num_taxis + 1):
        taxi = {
            "taxi_id": f"Taxi{i:03}",
            "type": random.choice(taxi_types),
            "location": {
                "type": "Point",
                "coordinates": generate_random_coordinates(bounds)
            }
        }
        taxis.append(taxi)
    return taxis

def update_taxi_locations(taxis, bounds):
    for taxi in taxis:
        # Update taxi location with small random movement
        taxi['location']['coordinates'] = generate_random_coordinates(bounds)
    return taxis

def run_taxi_simulator():
    bounds = {
        "southwest": {"lat": 29.677188413138673, "lng": -95.47487010411909},
        "northeast": {"lat": 29.82116771080327, "lng": -95.25459367187106}
    }
    
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://CloudProjectGroup01:dbhEGgjTGz2WjSGk@cluster0.ejz2u2z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['HoustonTaxiDB']
    taxis_collection = db['taxis']

    # Create geospatial index on location field
    taxis_collection.create_index([("location", "2dsphere")])
    
    # Generate initial taxi data
    taxis = generate_random_taxis(50, bounds)
    taxis_collection.insert_many(taxis)
    print("Initial taxi data generated and inserted into MongoDB.")

    try:
        while True:
            # Update taxi locations every minute
            taxis = update_taxi_locations(taxis, bounds)
            for taxi in taxis:
                taxis_collection.update_one(
                    {"taxi_id": taxi["taxi_id"]},
                    {"$set": {"location": taxi["location"]}}
                )
            print("Taxi locations updated.")
            time.sleep(60)
    except KeyboardInterrupt:
        print("Stopping the simulator.")
