import RPi.GPIO as GPIO
import time
from cane_sounds import *

WATER_SENSOR_DIGITAL = 27
WATER_SENSOR_ANALOG = 22

def water_sensor_callback(PIN):
    
    if GPIO.input(PIN):
        print("[ WATER SENSOR ] Water detected.")
        speak_thread = speak("Wet floor!")
        speak_thread.join()
    else:
        print("[ WATER SENSOR ] No water detected.")
        
def init_water_sensor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(WATER_SENSOR_DIGITAL, GPIO.IN)
    GPIO.setup(WATER_SENSOR_ANALOG, GPIO.IN)
    
    GPIO.add_event_detect(WATER_SENSOR_DIGITAL, GPIO.BOTH, bouncetime=300)
    GPIO.add_event_callback(WATER_SENSOR_DIGITAL, water_sensor_callback)
    time.sleep(0.1)

if __name__ == "__main__":
    init_tts()
    init_water_sensor()

    for i in range(20):
        time.sleep(1)


    GPIO.cleanup()