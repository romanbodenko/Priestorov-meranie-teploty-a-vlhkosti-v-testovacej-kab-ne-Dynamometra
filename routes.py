from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime


def create_routes(sensor_manager):  # prijíma dva argumenty
    routes = Blueprint('routes', __name__)

    @routes.route('/api/data', methods=['GET'])
    def get_api_data():
        data = sensor_manager.get_sensor_data()  # alebo z iného zdroja
        return jsonify(data)

    @routes.route('/')
    def home():
        # Generovanie údajov pre senzory
        data = sensor_manager.generate_sensor_data()
        return render_template('index.html', data=data)

    @routes.route('/get_sensor_data')
    def get_sensor_data():
        # Získanie údajov pre senzory vo formáte JSON
        data = sensor_manager.generate_sensor_data()
        return jsonify(data)

    @routes.route('/historical_data')
    def historical_data():
        # Získanie historických údajov podľa dátumu
        date_str = request.args.get('date')
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date = datetime.now()
        readings = sensor_manager.get_readings_by_date(date)
        return jsonify(readings)

    @routes.route('/download_log')
    def download_log():
        # Získame parameter dátumu
        date_str = request.args.get('date')
        if not date_str:
            return "Date parameter is missing", 400

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return "Invalid date format. Use YYYY-MM-DD.", 400

        # Získame cestu k logu pre zadaný dátum
        log_path = sensor_manager.logger._get_log_file_path(date)

        # Kontrola existencie súboru
        if not log_path.exists():
            return "Log file not found", 404

        # Ak súbor existuje, pošleme ho na stiahnutie
        return send_file(log_path, as_attachment=True, cache_timeout=0)

    return routes