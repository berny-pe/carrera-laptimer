from flask import Flask, jsonify, render_template
from lap_timer.core import LapTimer
from lap_timer.gpio_adapter import GPIOLapSensor

app = Flask(__name__)

lap_timer = LapTimer()
gpio_sensor = GPIOLapSensor()
gpio_sensor.setup(lap_timer)

@app.route('/')
def index():
    template_data = lap_timer.get_template_data()
    return render_template('index.html', **template_data)

@app.route('/api/start_timer', methods=['POST'])
def start_timer():
    lap_timer.start_timer()
    return jsonify(status='ok')

@app.route('/api/continue_timer', methods=['POST'])
def continue_timer():
    lap_timer.continue_timer()
    return jsonify(status='ok')

@app.route('/api/check_finished')
def check_finished():
    finished = lap_timer.check_finished()
    return jsonify(finished=finished)

@app.route('/api/stop_timer', methods=['POST'])
def stop_timer():
    lap_timer.stop_timer()
    return jsonify(status='ok')

@app.route('/api/reset', methods=['POST'])
def reset():
    lap_timer.reset()
    return jsonify(status='ok')

@app.route('/elapsed')
def elapsed():
    template_data = lap_timer.time()
    return render_template('elapsed.html', **template_data)

@app.route('/lap_times')
def lap_times():
    template_data = lap_timer.get_template_data()
    return render_template('lap_times.html', **template_data)

@app.route('/api/lap1', methods=['POST'])
def lap1():
    lap_timer.lap1()
    return jsonify(status='ok')

@app.route('/api/lap2', methods=['POST'])
def lap2():
    lap_timer.lap2()
    return jsonify(status='ok')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')