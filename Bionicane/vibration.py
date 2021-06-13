import RPi.GPIO as GPIO
import time

LEFT_MOTOR = 6
RIGHT_MOTOR = 13

def setup_vibration_motor(PIN_NUMBER):
    GPIO.setup(PIN_NUMBER, GPIO.OUT)  # Setam pinul TRIG in modul output
    GPIO.output(PIN_NUMBER, False)  # Initial, TRIG va da 0V


def vibrate(id, truth_value):
    if id == 0:
        GPIO.output(LEFT_MOTOR, truth_value)
        time.sleep(0.5)
    elif id == 1:
        GPIO.output(RIGHT_MOTOR, truth_value)
        time.sleep(0.5)


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)

    setup_vibration_motor(LEFT_MOTOR)
    setup_vibration_motor(RIGHT_MOTOR)
    
    vibrate(0, True)
    time.sleep(5)
    vibrate(0, False)
    vibrate(1, True)
    time.sleep(5)
    vibrate(1, False)
    vibrate(0, True)
    vibrate(1, True)
    time.sleep(5)
    vibrate(0, False)
    vibrate(1, False)
    GPIO.cleanup()