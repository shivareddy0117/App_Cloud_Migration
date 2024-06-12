import sys
import os
import threading
from app import create_app, create_socketio
from app.simulators.taxi_simulator import run_taxi_simulator
from app.simulators.user_simulator import run_user_simulator

# Add the app directory to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

app, socket_io = create_app()
create_socketio(socket_io)  # Initialize the Socket.IO handlers

if __name__ == '__main__':
    print("Starting Flask app with SocketIO...")

    # Start simulators in background threads
    taxi_simulator_thread = threading.Thread(target=run_taxi_simulator)
    user_simulator_thread = threading.Thread(target=run_user_simulator)
    
    taxi_simulator_thread.start()
    user_simulator_thread.start()

    socket_io.run(app, host='0.0.0.0', port=5000, debug=True)

 

