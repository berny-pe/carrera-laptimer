from flask import Flask, jsonify, redirect, render_template, request, url_for
from lap_timer.core import LapTimer
from lap_timer.gpio_adapter import GPIOLapSensor

app = Flask(__name__)

lap_timer = LapTimer()
gpio_sensor = GPIOLapSensor()
gpio_sensor.setup(lap_timer)

@app.route('/')
def setup():
    if lap_timer.configured:
        return redirect(url_for('race'))
    return render_template('setup.html', num_lanes=lap_timer.num_lanes)


@app.route('/race')
def race():
    if not lap_timer.configured:
        return redirect(url_for('setup'))
    template_data = lap_timer.get_template_data()
    return render_template('index.html', **template_data)


@app.route('/api/configure', methods=['POST'])
def configure():
    data = request.get_json(silent=True) or {}
    try:
        lap_timer.configure(data.get('mode'), laps=data.get('laps'), time_seconds=data.get('time_seconds'),
                             lanes=data.get('lanes'))
    except ValueError as err:
        return jsonify(status='error', error=str(err)), 400
    return jsonify(status='ok')

@app.route('/api/start_timer', methods=['POST'])
def start_timer():
    if not lap_timer.configured:
        return jsonify(status='error', error='configure the race first'), 409
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

@app.route('/api/lap/<int:lane>', methods=['POST'])
def lap(lane):
    try:
        lap_timer.lap(lane)
    except ValueError as err:
        return jsonify(status='error', error=str(err)), 404
    return jsonify(status='ok')


# legacy 2-lane endpoints
@app.route('/api/lap1', methods=['POST'])
def lap1():
    return lap(1)

@app.route('/api/lap2', methods=['POST'])
def lap2():
    return lap(2)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')