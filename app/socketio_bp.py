from flask_socketio import SocketIO
from flask import Blueprint, render_template, request, current_app
from pymongo import MongoClient
import threading
import time
from datetime import datetime
import requests

socketio_bp = Blueprint('socketio_bp', __name__)
socket_io = SocketIO()

client = MongoClient('mongodb+srv://CloudProjectGroup01:dbhEGgjTGz2WjSGk@cluster0.ejz2u2z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['HoustonTaxiDB']
taxis_collection = db['taxis']
rides_collection = db['rides']

if taxis_collection.count_documents({}) == 0:
    initial_data = {
        'taxi_id': 'Taxi001',
        'type': 'Luxury',
        'location': {
            'type': 'Point',
            'coordinates': [-95.3698, 29.7604]
        }
    }
    taxis_collection.insert_one(initial_data)
    print("Initial taxi data inserted.")

def get_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        route = data['routes'][0]['geometry']['coordinates']
        return [(lat, lon) for lon, lat in route]
    else:
        print("Error fetching route from OSM")
        return []
def move_taxi(app, taxi_id, route, ride_id='Ride001'):
    print(f"Route: {route}")  # Debug print to see the contents of route
    covered_path = []
    with app.app_context():
        for current_position in route:
            if not isinstance(current_position, (list, tuple)) or len(current_position) != 2:
                print(f"Invalid current_position: {current_position}")
                continue

            timestamp = datetime.utcnow()
            try:
                taxis_collection.update_one(
                    {'taxi_id': taxi_id},
                    {'$set': {'location': {'type': 'Point', 'coordinates': [current_position[1], current_position[0]]}}}
                )
                rides_collection.update_one(
                    {'ride_id': ride_id},
                    {'$push': {'path': {'location': current_position, 'timestamp': timestamp}}}
                )
                covered_path.append(current_position)
                current_app.extensions['socketio'].emit('taxi_update', {
                    'lat': current_position[0],
                    'lng': current_position[1],
                    'taxi_id': taxi_id,
                    'covered_path': covered_path,
                    'full_route': route
                })
                time.sleep(1)
            except Exception as e:
                print(f"Error updating taxi location: {e}")


@socketio_bp.route('/')
def index():
    return render_template('map.html')
@socketio_bp.route('/show_map', methods=['GET'])
def show_map():
    start_lat = request.args.get('start_lat')
    start_lng = request.args.get('start_lng')
    end_lat = request.args.get('end_lat')
    end_lng = request.args.get('end_lng')

    if not start_lat or not start_lng or not end_lat or not end_lng:
        # Log missing parameters
        print(f"Missing parameters: start_lat={start_lat}, start_lng={start_lng}, end_lat={end_lat}, end_lng={end_lng}")
        # Provide default values
        start_lat = 29.7604
        start_lng = -95.3698 
        end_lat = 29.7644
        end_lng = -95.3585 # Default to another point in Houston

    ride_id = 'Ride001'
    user_id = 'User001'
    taxi_id = 'Taxi001'
    start_location = [start_lat, start_lng]
    end_location = [end_lat, end_lng]
    start_time = datetime.now()

    ride_data = {
        'ride_id': ride_id,
        'user_id': user_id,
        'taxi_id': taxi_id,
        'start_location': start_location,
        'end_location': end_location,
        'start_time': start_time,
        'path': []
    }
    db.rides.insert_one(ride_data)

    route = get_route(start_location, end_location)
    if route:
        socket_io.emit('route_init', {'full_route': route})
        taxi_thread = threading.Thread(target=move_taxi, args=(current_app._get_current_object(), taxi_id, route, ride_id))
        taxi_thread.start()

    return render_template('map.html')

@socket_io.on('connect')
def test_connect():
    print('Client connected')

@socket_io.on('disconnect')
def test_disconnect():
    print('Client disconnected')