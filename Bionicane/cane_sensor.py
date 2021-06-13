import RPi.GPIO as GPIO
from threading import Thread
import time

LEFT_SENSOR_TRIG = 26
LEFT_SENSOR_ECHO = 19
RIGHT_SENSOR_TRIG = 21
RIGHT_SENSOR_ECHO = 20
FRONTAL_SENSOR_TRIG = 24
FRONTAL_SENSOR_ECHO = 23


# Functie pentru initializarea senzorului
def setup_sensor(TRIG, ECHO):

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)  # Setam pinul TRIG in modul output
    GPIO.setup(ECHO, GPIO.IN)  # Setam pinul ECHO in modul input

    GPIO.output(TRIG, False)  # Initial, TRIG va da 0V
    print("[ INFO ] Waiting for sensor to settle")
    time.sleep(2)  # Asteptam 2 secunde pentru a se stabiliza


# Functia pentru calcularea distantei detectate de senzor
def get_sensor_distance(TRIG, ECHO):

    GPIO.output(TRIG, True)  # Punem TRIG pe "1" logic
    time.sleep(0.00001)  # Asteptam 10 us
    GPIO.output(TRIG, False)  # Punem TRIG pe "0" logic
    
    try:
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
    except RuntimeError as e:
        print(f"[ WARNING ] RuntimeError while obtaining sensor distance.")
        return 5000

    try:
        pulse_duration = pulse_end - pulse_start  # Calculam durata semnalului
    except UnboundLocalError as e:
        pulse_duration = 100
        print(f"[ WARNING ] Caught error in sensor: {e}")

    distance = pulse_duration * 17150
    distance = round(distance, 2)  # Obtinem distanta la care se afla obiectul

    time.sleep(0.05)
    return distance


def test_sensor(id, TRIG, ECHO):
    while True:
        dist = get_sensor_distance(TRIG, ECHO)
        print(f"Sensor {id} distance {dist}")
        time.sleep(1)


if __name__ == "__main__":
    setup_sensor(LEFT_SENSOR_TRIG, LEFT_SENSOR_ECHO)  # Left sensor
    sensor0_thread = Thread(target=test_sensor, args=(0, LEFT_SENSOR_TRIG, LEFT_SENSOR_ECHO))  # Left sensor
    setup_sensor(RIGHT_SENSOR_TRIG, RIGHT_SENSOR_ECHO)  # Right sensor
    sensor1_thread = Thread(target=test_sensor, args=(1, RIGHT_SENSOR_TRIG, RIGHT_SENSOR_ECHO))  # Right sensor
    setup_sensor(FRONTAL_SENSOR_TRIG, FRONTAL_SENSOR_ECHO)  # Frontal sensor
    sensor2_thread = Thread(target=test_sensor, args=(2, FRONTAL_SENSOR_TRIG, FRONTAL_SENSOR_ECHO))  # Frontal sensor

    sensor0_thread.start()
    sensor1_thread.start()
    sensor2_thread.start()
    while True:
        keyboard_button = input("Press q to quit, enter to continue!")
        if keyboard_button == "q":
            break
    sensor0_thread.join(1)
    sensor1_thread.join(1)
    sensor2_thread.join(1)
    GPIO.cleanup()
