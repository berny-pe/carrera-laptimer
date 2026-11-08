from functools import partial

from .lanes import lane_pins

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    GPIO = None


class GPIOLapSensor:
    def __init__(self, pins=None):
        self.lane_pins = list(lane_pins() if pins is None else pins)
        self.enabled = False

    def setup(self, lap_timer):
        if GPIO is None:
            self.enabled = False
            return False

        GPIO.setmode(GPIO.BCM)
        for lane_number, pin in enumerate(self.lane_pins, start=1):
            GPIO.setup(pin, GPIO.IN)
            GPIO.add_event_detect(pin, GPIO.BOTH, callback=partial(lap_timer.lap_callback, lane_number))
        self.enabled = True
        return True

    def cleanup(self):
        if GPIO is None or not self.enabled:
            return
        GPIO.cleanup()
