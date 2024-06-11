from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import folium
import threading
import time
from datetime import datetime
from app.socketio_bp import get_route, move_taxi  # Importing the functions

main = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('main.login_user'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def landing_page():
    return render_template('landing_page.html')

@main.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        data = {
            "username": request.form['username'],
            "password": generate_password_hash(request.form['password'])
        }
        current_app.config['db'].users.insert_one(data)
        return jsonify({"message": "User registered successfully!"}), 201
    return render_template('register_user.html')

@main.route('/login_user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = current_app.config['db'].users.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('main.user_dashboard'))
        else:
            return jsonify({"message": "Invalid username or password!"}), 401
    return render_template('login_user.html')

@main.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('main.login_user'))

@main.route('/register_driver', methods=['GET', 'POST'])
def register_driver():
    if request.method == 'POST':
        data = {
            "username": request.form['username'],
            "password": generate_password_hash(request.form['password']),
            "taxi_id": request.form['taxi_id'],
            "driver_name": request.form['driver_name'],
            "location": {
                "type": "Point",
                "coordinates": [float(request.form['longitude']), float(request.form['latitude'])]
            }
        }
        current_app.config['db'].drivers.insert_one(data)
        return jsonify({"message": "Driver registered successfully!"}), 201
    return render_template('register_driver.html')

@main.route('/login_driver', methods=['GET', 'POST'])
def login_driver():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        driver = current_app.config['db'].drivers.find_one({"username": username})
        if driver and check_password_hash(driver['password'], password):
            session['username'] = username
            return redirect(url_for('main.driver_dashboard'))
        else:
            return jsonify({"message": "Invalid username or password!"}), 401
    return render_template('login_driver.html')

@main.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')

@main.route('/driver_dashboard')
@login_required
def driver_dashboard():
    return render_template('driver_dashboard.html')

@main.route('/register_taxi', methods=['GET', 'POST'])
@login_required
def register_taxi():
    if request.method == 'POST':
        data = {
            "taxi_id": request.form['taxi_id'],
            "driver_name": request.form['driver_name'],
            "location": {
                "type": "Point",
                "coordinates": [float(request.form['longitude']), float(request.form['latitude'])]
            }
        }
        current_app.config['db'].taxis.insert_one(data)
        return jsonify({"message": "Taxi registered successfully!"}), 201
    return render_template('register_taxi.html')

@main.route('/update_taxi_location', methods=['POST'])
@login_required
def update_taxi_location():
    data = request.json
    current_app.config['db'].taxis.update_one(
        {"taxi_id": data["taxi_id"]},
        {"$set": {"location": data["location"]}}
    )
    return jsonify({"message": "Taxi location updated successfully!"}), 200

@main.route('/request_taxi', methods=['POST'])
@login_required
def request_taxi():
    data = request.json
    user_location = data['location']
    taxi_preference = data['taxi_preference']

    query = {
        "location": {
            "$near": {
                "$geometry": user_location,
                "$maxDistance": 5000  # within 5 km radius
            }
        }
    }

    if taxi_preference != 'Any':
        query["type"] = taxi_preference

    available_taxis = list(current_app.config['db'].taxis.find(query).limit(5))

    for taxi in available_taxis:
        taxi['_id'] = str(taxi['_id'])

    return jsonify(available_taxis), 200

@main.route('/map')
def sample():
    return render_template('map.html')

@main.route('/show_map', methods=['GET'])
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
    current_app.config['db'].rides.insert_one(ride_data)

    route = get_route(start_location, end_location)
    if route:
        current_app.extensions['socketio'].emit('route_init', {'full_route': route})
        taxi_thread = threading.Thread(target=move_taxi, args=(taxi_id, route, ride_id))
        taxi_thread.start()

    return render_template('map.html')

@main.route('/visualize_taxis', methods=['GET'])
def visualize_taxis():
    taxis = list(current_app.config['db'].taxis.find())
    m = folium.Map(location=[29.7604, -95.3698], zoom_start=13)

    icons = {
        'Utility': '/static/utility.png',
        'Deluxe': '/static/deluxe.png',
        'Luxury': '/static/luxury.png',
        'default': '/static/default.png'
    }

    for taxi in taxis:
        icon_url = icons.get(taxi['type'], icons['default'])
        icon = folium.CustomIcon(
            icon_image=icon_url,
            icon_size=(30, 30),
            icon_anchor=(15, 15)
        )

        folium.Marker(
            location=[taxi['location']['coordinates'][1], taxi['            location'][0]],
            icon=icon,
            popup=f"Taxi ID: {taxi['taxi_id']}<br>Type: {taxi['type']}"
        ).add_to(m)

    map_html = m._repr_html_()
    return render_template('taxi_locations.html', map_html=map_html)

@main.route('/start_ride', methods=['POST'])
def start_ride():
    data = request.json
    ride_id = data.get('ride_id', 'Ride001')
    user_id = data.get('user_id', 'User001')
    taxi_id = data.get('taxi_id', 'Taxi001')
    start_location = data.get('start_location', [29.7604, -95.3698])
    end_location = data.get('end_location', [29.7644, -95.3585])
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
    current_app.config['db'].rides.insert_one(ride_data)

    route = get_route(start_location, end_location)
    if route:
        current_app.extensions['socketio'].emit('route_init', {'full_route': route})
        taxi_thread = threading.Thread(target=move_taxi, args=(taxi_id, route, ride_id))
        taxi_thread.start()

    return jsonify({"message": "Ride started"}), 200
