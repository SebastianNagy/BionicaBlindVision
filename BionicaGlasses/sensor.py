import RPi.GPIO as GPIO
import time

# Functie pentru initializarea senzorului
def setup_sensor():  
    global TRIG, ECHO
    #GPIO.setmode(GPIO.BCM)

    TRIG = 18  # Numarul pinului la care este conectat TRIG
    ECHO = 24  # Numarul pinului la care este conectat ECHO
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)  # Setam pinul TRIG in modul output
    GPIO.setup(ECHO, GPIO.IN)  # Setam pinul ECHO in modul input

    GPIO.output(TRIG, False)  # Initial, TRIG va da 0V
    print("[ INFO ] Waiting for sensor to settle")
    time.sleep(2)  # Asteptam 2 secunde pentru a se stabiliza
    
    
# Functia pentru calcularea distantei detectate de senzor
def get_sensor_distance():  

    global TRIG, ECHO
    
    
    GPIO.output(TRIG, True)  # Punem TRIG pe "1" logic
    time.sleep(0.00001)  # Asteptam 10 us
    GPIO.output(TRIG, False)  # Punem TRIG pe "0" logic

    while GPIO.input(ECHO) == 0:
      pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
      pulse_end = time.time()
    
    try:
        pulse_duration = pulse_end - pulse_start  # Calculam durata semnalului
    except UnboundLocalError as e:
        pulse_duration = 100
        print(f"[ WARNING ] Caught error in sensor: {e}")

    distance = pulse_duration * 17150
    distance = round(distance, 2)  # Obtinem distanta la care se afla obiectul

    time.sleep(0.05)
    return distance

    
if __name__ == "__main__":
    setup_sensor()
    while True:
        distance = get_sensor_distance()
        print(distance)
        keyboard_button = input("Press q to quit, enter to continue!")
        if keyboard_button == "q":
            break
    GPIO.cleanup()    