import sys
import os

# Add the app directory to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app import create_app, create_socketio, socket_io
from app.simulators.taxi_simulator import run_taxi_simulator
from app.simulators.user_simulator import run_user_simulator
import threading

app, socket_io = create_app()
create_socketio(socket_io)  # Initialize the Socket.IO handlers

if __name__ == '__main__':
    print("Starting Flask app with SocketIO...")

    # Start simulators in background threads
    taxi_simulator_thread = threading.Thread(target=run_taxi_simulator)
    user_simulator_thread = threading.Thread(target=run_user_simulator)
    
    taxi_simulator_thread.start()
    user_simulator_thread.start()

    socket_io.run(app, debug=True)
