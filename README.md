# carrera-laptimer

this is a quick implementation of an analog lap timer for slotcar racing running on a raspberry pi taking lane inputs over GPIO pins.

## architecture
the main logic is a python script that starts a timer, takes GPIO inputs and exposes a webserver with the information. additionally it contains user interface functionality for starting, stopping and resetting the timer.
