from .config import LANE1_PIN, LANE2_PIN

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    GPIO = None


class GPIOLapSensor:
    def __init__(self, lane1_pin=LANE1_PIN, lane2_pin=LANE2_PIN):
        self.lane1_pin = lane1_pin
        self.lane2_pin = lane2_pin
        self.enabled = False

    def setup(self, lap_timer):
        if GPIO is None:
            self.enabled = False
            return False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.lane1_pin, GPIO.IN)
        GPIO.setup(self.lane2_pin, GPIO.IN)
        GPIO.add_event_detect(self.lane1_pin, GPIO.BOTH, callback=lap_timer.lap_callback1)
        GPIO.add_event_detect(self.lane2_pin, GPIO.BOTH, callback=lap_timer.lap_callback2)
        self.enabled = True
        return True

    def cleanup(self):
        if GPIO is None or not self.enabled:
            return
        GPIO.cleanup()
