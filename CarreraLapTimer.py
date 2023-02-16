import time
from flask import Flask, render_template
import RPi.GPIO as GPIO

app = Flask(__name__)

class LapTimer:
    def __init__(self):
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.IN)
        GPIO.setup(23, GPIO.IN)
        GPIO.add_event_detect(18, GPIO.BOTH, callback=self.lap_callback1)
        GPIO.add_event_detect(23, GPIO.BOTH, callback=self.lap_callback2)
        self.reset()
        
    def reset(self):
        # Initialize variable for timers
        self.timer_running = False
        self.start_time = None
        self.elapsed_time = None
        self.last_total_time1 = None
        self.last_total_time2 = None
        self.lap_time1 = None
        self.lap_time2 = None
        self.last_lap_time1 = None
        self.last_lap_time2 = None
        self.fastest_lap_time1 = None
        self.fastest_lap_time2 = None
        self.num_laps1 = 0
        self.num_laps2 = 0
    
        
    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.start_time = time.time()
            self.last_total_time1 = None
            self.last_total_time2 = None
            self.lap_time1 = None
            self.lap_time2 = None
            self.last_lap_time1 = None
            self.last_lap_time2 = None
            self.fastest_lap_time1 = None
            self.fastest_lap_time2 = None
            self.num_laps1 = 0
            self.num_laps2 = 0
        
    def stop_timer(self):
        
        if self.timer_running:
            self.elapsed_timer()
            self.timer_running = False
            
    def elapsed_timer(self):
        if self.timer_running:
            self.elapsed_time = time.time() - self.start_time
        print(self.elapsed_time)
        return self.elapsed_time

    def lap_callback1(self):
        print(self.start_time)
        
        if self.last_lap_time1 is not None:
            self.last_lap_time1 = time.time() - self.last_total_time1
        else:
            self.last_lap_time1 = time.time() - self.start_time
            #self.lap_time1 = time.time() - self.start_time
        
        if self.fastest_lap_time1 is None or self.last_lap_time1 < self.fastest_lap_time1:
            self.fastest_lap_time1 = self.last_lap_time1
            
        self.num_laps1 += 1
            
        
        self.last_total_time1 = time.time()
        print(self.last_lap_time1)
        print(self.fastest_lap_time1)
            
    def lap_callback2(self):
        print('lap2')
        
        
    def get_current_lap_times(self):
        if self.start_time:
            if self.last_total_time1 is None:
                self.lap_time1 = time.time() - self.start_time
            else:
                self.lap_time1 = time.time() - self.last_total_time1
        #lap_time2 = time.time() - self.lap_time2
            
    def get_formatted_time(self, lap_time):
        minutes = int(lap_time // 60)
        seconds = int(lap_time % 60)
        thousands = int((lap_time % 1) * 1000)
        return '{:02d}:{:02d}:{:03d}'.format(minutes, seconds, thousands)
    
    def time(self):
        if self.start_time is None:
            formatted_time = '00:00:000'
        else:
            formatted_time = self.get_formatted_time(self.elapsed_timer())
        return {'formatted_time': formatted_time }
                
            
    def lap1(self):
        print('lap1 from web')
        self.lap_callback1()
        
    def lap2(self):
        print('lap2 from web')
        self.lap_callback2()
    
    def get_template_data(self):
        self.get_current_lap_times()
        
        # Get data for time 
        formatted_time = '00:00:000'
        formatted_current_lap_time1 = '00:00:000'
        
        if self.start_time is not None:
            formatted_time = self.get_formatted_time(self.elapsed_timer())
            if self.last_lap_time1 is not None:
                formatted_current_lap_time1 = self.get_formatted_time(self.lap_time1)
            else:
                formatted_current_lap_time1 = formatted_time
            
            
        # Get data for timer 1
        if self.last_lap_time1 is not None:
            formatted_last_lap_time1 = self.get_formatted_time(self.last_lap_time1)
        else:
            formatted_last_lap_time1 = '00:00:000'
        if self.fastest_lap_time1 is not None:
            formatted_fastest_lap_time1 = self.get_formatted_time(self.fastest_lap_time1)
        else:
            formatted_fastest_lap_time1 = '00:00:000'
        num_laps1 = self.num_laps1
        
        
        return {'formatted_time': formatted_time,
                
                'formatted_current_lap_time1': formatted_current_lap_time1,
                'formatted_last_lap_time1': formatted_last_lap_time1,
                'formatted_fastest_lap_time1': formatted_fastest_lap_time1,
                'num_laps1': num_laps1,
                
                #'formatted_lap_time2': formatted_lap_time2,
                #'formatted_fastest_lap_time2': formatted_fastest_lap_time2,
                #'num_laps2': num_laps2
                }
        
lap_timer = LapTimer()

@app.route('/')
def index():
    template_data = lap_timer.get_template_data()
    return render_template('index.html', **template_data)

@app.route('/start_timer')
def start_timer():
    lap_timer.start_timer()
    return 'OK'

@app.route('/stop_timer')
def stop_timer():
    lap_timer.stop_timer()
    return 'OK'

@app.route('/reset')
def reset():
    lap_timer.reset()
    return 'OK'

@app.route('/elapsed')
def elapsed():
    template_data = lap_timer.time()
    return render_template('elapsed.html', **template_data)

@app.route('/lap_times')
def lap_times():
    template_data = lap_timer.get_template_data()
    return render_template('lap_times.html', **template_data)

@app.route('/lap1')
def lap1():
    lap_timer.lap1()
    return 'OK'

@app.route('/lap2')
def lap2():
    lap_timer.lap2()
    return 'OK'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')