import RPi.GPIO as GPIO
import time

DOOR_LOCK_PIN = 23

class DoorLock:
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DOOR_LOCK_PIN, GPIO.OUT)
        self.lock()

    def lock(self):
        GPIO.output(DOOR_LOCK_PIN, GPIO.HIGH)

    def unlock(self, duration):
        GPIO.output(DOOR_LOCK_PIN, GPIO.LOW)
        time.sleep(duration)
        self.lock()

    def cleanup(self):
        GPIO.cleanup()