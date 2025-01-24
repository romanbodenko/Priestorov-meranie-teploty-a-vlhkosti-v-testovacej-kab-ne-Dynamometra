import smbus
from flask import Flask
from sensor_manager import SensorDataManager, Config
from routes import create_routes

def create_app():
    app = Flask(__name__)
    # Inicializácia konfigurácie
    config = Config()
    # Inicializácia I2C zbernice
    i2c_bus = smbus.SMBus(1)  # Použite správnu zbernicu pre váš hardvér
    # Inicializácia správcu senzorov
    sensor_manager = SensorDataManager(config, i2c_bus, address=[8, 9])
    # Registrácia ciest
    routes = create_routes(sensor_manager)
    app.register_blueprint(routes)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
