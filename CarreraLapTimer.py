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
        self.last_active_time = None
        self.paused = 0
        self.elapsed_time = None
        self.lane1_finished = None
        self.lane2_finished = None
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
            self.lane1_finished = None
            self.lane2_finished = None
        
    def continue_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.paused = time.time() - self.last_active_time
            self.lane1_finished = None
            self.lane2_finished = None
            
    def stop_timer(self):
        self.last_active_time = time.time()
        if self.timer_running:
            self.elapsed_timer()
            self.timer_running = False
            
    def elapsed_timer(self):
        print("-----")
        if self.timer_running:
            self.elapsed_time = time.time() - self.start_time - self.paused
        
        return self.elapsed_time

    def lap_callback1(self):
        if self.lane1_finished is None:
            if self.last_lap_time1 is not None:
                self.last_lap_time1 = time.time() - self.last_total_time1
            else:
                self.last_lap_time1 = time.time() - self.start_time
            
            if self.fastest_lap_time1 is None or self.last_lap_time1 < self.fastest_lap_time1:
                self.fastest_lap_time1 = self.last_lap_time1
                
            self.num_laps1 += 1
            
            self.last_total_time1 = time.time()
            if not self.timer_running:
                self.lane1_finished = True
        
            
    def lap_callback2(self):
        if self.lane2_finished is None:
            if self.last_lap_time2 is not None:
                self.last_lap_time2 = time.time() - self.last_total_time2
            else:
                self.last_lap_time2 = time.time() - self.start_time
            
            if self.fastest_lap_time2 is None or self.last_lap_time2 < self.fastest_lap_time2:
                self.fastest_lap_time2 = self.last_lap_time2
                
            self.num_laps2 += 1
                
            self.last_total_time2 = time.time()
            if not self.timer_running:
                self.lane2_finished = True
        
        
    def get_current_lap_times(self):
        if self.start_time:
            if self.lane1_finished is None:
                if self.last_total_time1 is None:
                    self.lap_time1 = time.time() - self.start_time
                else:
                    self.lap_time1 = time.time() - self.last_total_time1
            else:
                self.lap_time1 = None
                
            if self.lane2_finished is None:
                if self.last_total_time2 is None:
                    self.lap_time2 = time.time() - self.start_time
                else:
                    self.lap_time2 = time.time() - self.last_total_time2
            else:
                self.lap_time2 = None
      
      
    def check_finished(self):
        if self.lane1_finished and self.lane2_finished:
            return True
    
    
    def get_formatted_time(self, lap_time):
        if lap_time is None:
            return '00:00:000'
        else:
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
        formatted_current_lap_time2 = '00:00:000'
        
        if self.start_time is not None:
            formatted_time = self.get_formatted_time(self.elapsed_timer())
            if self.last_lap_time1 is not None:
                formatted_current_lap_time1 = self.get_formatted_time(self.lap_time1)
            else:
                formatted_current_lap_time1 = formatted_time
                
            if self.last_lap_time2 is not None:
                formatted_current_lap_time2 = self.get_formatted_time(self.lap_time2)
            else:
                formatted_current_lap_time2 = formatted_time
            
            
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
        
        
        # Get data for timer 2
        if self.last_lap_time2 is not None:
            formatted_last_lap_time2 = self.get_formatted_time(self.last_lap_time2)
        else:
            formatted_last_lap_time2 = '00:00:000'
            
        if self.fastest_lap_time2 is not None:
            formatted_fastest_lap_time2 = self.get_formatted_time(self.fastest_lap_time2)
        else:
            formatted_fastest_lap_time2 = '00:00:000'
        
        num_laps2 = self.num_laps2
        
        
        return {'formatted_time': formatted_time,
                
                'formatted_current_lap_time1': formatted_current_lap_time1,
                'formatted_last_lap_time1': formatted_last_lap_time1,
                'formatted_fastest_lap_time1': formatted_fastest_lap_time1,
                'num_laps1': num_laps1,
                
                'formatted_current_lap_time2': formatted_current_lap_time2,
                'formatted_last_lap_time2': formatted_last_lap_time2,
                'formatted_fastest_lap_time2': formatted_fastest_lap_time2,
                'num_laps2': num_laps2,
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

@app.route('/continue_timer')
def continue_timer():
    lap_timer.continue_timer()
    return 'OK'

@app.route('/check_finished')
def check_finished():
    finished = lap_timer.check_finished()
    if finished:
        return 'OK'
    else:
        return 'NOK'

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