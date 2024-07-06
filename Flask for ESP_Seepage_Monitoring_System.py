from flask import Flask, request, jsonify, render_template_string, abort
import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__)

# Update this based on your mobile hotspot's IP range
ALLOWED_NETWORK_PREFIX = '***.***.***'

def is_request_from_local_network():
    client_ip = request.remote_addr
    return client_ip.startswith(ALLOWED_NETWORK_PREFIX)

@app.before_request
def restrict_remote_access():
    if not is_request_from_local_network():
        abort(403)  # Forbidden

# MySQL database setup
DATABASE_CONFIG = {
    'user': 'root',             #Update the User
    'password': '*********',    # Update the Password
    'host': 'localhost',
    'database': 'sensor_data',
    'raise_on_warnings': True
}

def init_db():
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_values (
                id INT AUTO_INCREMENT PRIMARY KEY,
                current_value FLOAT NOT NULL,
                meter_value FLOAT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

init_db()

@app.route('/update', methods=['GET'])
def update_sensor():
    current_value = request.args.get('current')
    meter_value = request.args.get('meter')
    if current_value and meter_value:
        current_value = float(current_value)
        meter_value = float(meter_value)
        try:
            conn = mysql.connector.connect(**DATABASE_CONFIG)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sensor_values (current_value, meter_value) VALUES (%s, %s)", (current_value, meter_value))
            if current_value > 97:
                cursor.execute("INSERT INTO alerts (message) VALUES (%s)", (f"Fault value: {current_value}",))
            conn.commit()
        except mysql.connector.Error as err:
            pass  
        finally:
            cursor.close()
            conn.close()
    return jsonify({"status": "success"})

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    sensor_values = []
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT current_value, meter_value, timestamp FROM sensor_values ORDER BY timestamp DESC LIMIT 100")
        result = cursor.fetchall()
        sensor_values = [{"current_value": row[0], "meter_value": row[1], "timestamp": row[2].strftime("%Y-%m-%d %H:%M:%S")} for row in result]
    except mysql.connector.Error as err:
        pass  
    finally:
        cursor.close()
        conn.close()
    return jsonify({"sensor_values": sensor_values})

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Sensor Data</title>
        <style>
            #sensor-data {
                margin-top: 20px;
                white-space: pre-wrap;
                font-family: Arial, sans-serif;
            }
        </style>
    </head>
    <body>
        <h1>Live Sensor Data</h1>
        <div id="sensor-data"></div>
        <script>
            function fetchSensorData() {
                fetch('/sensor_data')
                    .then(response => response.json())
                    .then(data => {
                        let sensorDataDiv = document.getElementById('sensor-data');
                        sensorDataDiv.innerHTML = '';
                        data.sensor_values.forEach(sensor => {
                            sensorDataDiv.innerHTML += `Current Value: ${sensor.current_value} A, Meter: ${sensor.meter_value} m, Timestamp: ${sensor.timestamp}<br>`;
                        });
                    })
                    .catch(error => console.error('Error fetching sensor data:', error));
            }

            setInterval(fetchSensorData, 5000); // Fetch data every 5 seconds

            fetchSensorData(); // Initial fetch
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
