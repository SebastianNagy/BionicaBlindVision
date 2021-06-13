import traceback
from maps import *
from cane_sounds import *
from cane_sensor import *
from cane_speech_recog import *
from vibration import *
from gps_module import get_gps_coord
from water_sensor import *
import smtplib
import ssl
import datetime
import serial
import pynmea2


cancel_process_direction_results = False
bionicane_running = True
emergency_emails = ["nagyseby98@gmail.com", "teogodea@yahoo.com"]
port="/dev/ttyS0"
ser=serial.Serial(port, baudrate=9600, timeout=0.01, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
dataout = pynmea2.NMEAStreamReader()
close_serial_thread = False
last_coords = None


def gps_thread_f():
    global ser, dataout, close_serial_thread, last_coords
    
    while close_serial_thread == False:
        last_coords = get_gps_coord(ser,dataout)
        # print("Thread: ", last_coords)
        

def wait_directions_disable():
    global cancel_process_direction_results
    print("[ SPEECH ] Waiting for directions disable")
    while cancel_process_direction_results is False:
        text = speech_to_text("/home/pi/Desktop/Bionicane/files/temp.wav", ding_enable=False, name="Directions")
        if text in ["exit", "thank you", "disable", "ok", "okay", "ok cane", "okay cane", "thanks", "ok bionic cane", "okay bionic cane"]:
            cancel_process_direction_results = True
            speak_thread = speak(f"Exiting directions")
            speak_thread.join()

def process_direction_results(directions_result):
    global cancel_process_direction_results, last_coords
    step_size = 0.6
    last_speak = 4
    print(f"[ INFO ] All directions are: {directions_result}")
    
    while len(directions_result) > 1 and cancel_process_direction_results is False:
        current_position = last_coords   
        print(f"[ INFO GPS ] Coordinates are {current_position}")
        
        speak_string, speak_enable = get_next_step(current_position, directions_result, last_speak, step_size)
        if speak_enable == 1 or speak_enable == 2:
            last_speak = 0
            speak_thread = speak(speak_string)
            speak_thread.join()
        elif speak_enable == 0:
            last_speak += 1
        if speak_enable == 1:
            directions_result = directions_result[1:]  # go to next dirs

        time.sleep(5)

    final_step = directions_result[0]
    end_location = (final_step['end_location']['lat'], final_step['end_location']['lng'])

    # Final waypoint
    last_speak = 4
    current_position = last_coords
    distance = round(mpu.haversine_distance(current_position, end_location) * (1000))
    while distance >= 25 and cancel_process_direction_results is False:
        current_position = last_coords
        print(f"[ INFO GPS ] Coordinates are {current_position}")
        
        distance = round(mpu.haversine_distance(current_position, end_location) * (1000 / step_size)) #/ step_size))
        
        if last_speak == 4:
            last_speak = 0
            speak_thread = speak(f"You will arive at your destination in {distance} steps.")
            speak_thread.join()
        else:
            last_speak +=1
        time.sleep(5)

    if cancel_process_direction_results is False:
        speak_thread = speak("You have arrived at your destination!")
        speak_thread.join()
        cancel_process_direction_results = True


def sensor(id, TRIG, ECHO):
    global bionicane_running
    
    while bionicane_running == True:
        # print(f"[ SENSOR ] Sensor {id} has bionicane_running {bionicane_running}")
        try:
            sensor_distance = get_sensor_distance(TRIG, ECHO)
        except RuntimeError as e:
            #print(f"[ WARNING ] RuntimeError while obtaining sensor distance.")
            sensor_distance = 5000
            
        if sensor_distance < 30.0:  # To change back to 30
            print(f"[ SENSOR ] Sensor {id} distance: {sensor_distance}cm")
            if id == 2:
                try:
                    becareful()
                except RuntimeError:
                    print("[ WARNING ] Be careful while speaking")
            else:
                vibrate(id, True)
        else:
            if id != 2:
                vibrate(id, False)


def send_email(lat, long):
    global emergency_emails
    port = 465
    account_password = "bionica1234"
    email_context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=email_context) as email_server:
        try:
            email_server.login("bionica.blind.vision@gmail.com", account_password)
        except BaseException as e:
            print(f"[ WARNING EMAIL ] Authentication into email account failed!")
            
        email_return = email_server.sendmail("bionica.blind.vision@gmail.com", emergency_emails, f"Subject: I need your help!\n\nHello!\n\nI need help, please reach out to me ASAP! I am here: ({lat}, {long}).\n\nThank you!")
        print(f"[ INFO EMAIL ] Sent emails to emergency contacts with return {email_return}")
            

def main():
    global cancel_process_direction_results, bionicane_running, close_serial_thread, last_coords
    print("[ INFO ] Initializing text to speech engine")
    init_tts()  # Se initializeaza modulul text to speech
    print("[ INFO ] Initializing speech to text engine")
    init_srecog()  # Se initializeaza modulul de recunoastere vocala
    print("[ INFO ] Initializing water sensor")
    init_water_sensor()
    print("[ INFO ] Initializing sensors")
    setup_sensor(LEFT_SENSOR_TRIG, LEFT_SENSOR_ECHO)  # Left sensor
    sensor0_thread = Thread(target=sensor, args=(0, LEFT_SENSOR_TRIG, LEFT_SENSOR_ECHO))  # Left sensor
    setup_sensor(RIGHT_SENSOR_TRIG, RIGHT_SENSOR_ECHO)  # Right sensor
    sensor1_thread = Thread(target=sensor, args=(1, RIGHT_SENSOR_TRIG, RIGHT_SENSOR_ECHO))  # Right sensor
    setup_sensor(FRONTAL_SENSOR_TRIG, FRONTAL_SENSOR_ECHO)  # Frontal sensor
    sensor2_thread = Thread(target=sensor, args=(2, FRONTAL_SENSOR_TRIG, FRONTAL_SENSOR_ECHO))  # Frontal sensor
    print("[ INFO ] Initializing vibration motors")
    setup_vibration_motor(LEFT_MOTOR)
    setup_vibration_motor(RIGHT_MOTOR)

    mapskey_file = open("mapskey.txt", "r")
    mapskey = mapskey_file.readline()
    gmaps = googlemaps.Client(key=mapskey)

    known_locations_dict = {"home 2": "Camin 11C, Str. Aleea Studentilor, Timisoara",
                            "corner": "46.42882280607239, 21.84298146187208",
                            "Pizza": "Pizzeria La Roscatu, Calea Traian, Ineu",
                            "home": "46.42782866666667, 21.843100166666666",
                            "the gas station": "Petrom Gas Station Ineu"}
    
    print("[ INFO ] Ready to go!")
    speak_thread = speak("Hello Sebastian!")
    speak_thread.join()
    
    gps_thread = Thread(target=gps_thread_f)
    gps_thread.start()
    
    sensor0_thread.start()
    sensor1_thread.start()
    sensor2_thread.start()

    while bionicane_running == True:
        is_exit = wait_hello_cane()
        if is_exit:
            bionicane_running = False
            break
        speak_thread = speak("Yes, Sebastian?")
        speak_thread.join()

        addr, addr_type = wait_address(known_locations_dict)
        if addr_type == "fail":
            continue
        elif addr_type == "email":
            lat, long = last_coords
            send_email(lat, long)
            speak_thread = speak("Emails sent successfully!")
            speak_thread.join()
            continue
        print(f"[ INFO ] Address is {addr}.")
        
        lat, long = last_coords
        now = datetime.datetime.now()
        
        if lat != 0 and long != 0:
            print(f"[ POS ] Current position is: {lat} lat, {long} long")
            try:
                directions_result = gmaps.directions(origin=(lat, long), destination=addr, mode="walking",departure_time=now)
                # directions_result = [{'bounds': {'northeast': {'lat': 46.4289353, 'lng': 21.8429955}, 'southwest': {'lat': 46.4257779, 'lng': 21.8399752}}, 'copyrights': 'Map data ©2021', 'legs': [{'distance': {'text': '0.8 km', 'value': 802}, 'duration': {'text': '10 mins', 'value': 599}, 'end_address': 'Calea Republicii 64, Ineu 315300, Romania', 'end_location': {'lat': 46.4257779, 'lng': 21.8419213}, 'start_address': 'Calea Traian 2, Ineu 315300, Romania', 'start_location': {'lat': 46.4279246, 'lng': 21.8428049}, 'steps': [{'distance': {'text': '0.1 km', 'value': 113}, 'duration': {'text': '1 min', 'value': 81}, 'end_location': {'lat': 46.4289353, 'lng': 21.8429955}, 'html_instructions': 'Head <b>north</b> toward <b>Str. Ioan Slavici</b>', 'polyline': {'points': 'o}jzGodidCc@GkBUg@ESC'}, 'start_location': {'lat': 46.4279246, 'lng': 21.8428049}, 'travel_mode': 'WALKING'}, {'distance': {'text': '0.2 km', 'value': 225}, 'duration': {'text': '3 mins', 'value': 166}, 'end_location': {'lat': 46.4287555, 'lng': 21.8400729}, 'html_instructions': 'Turn <b>left</b> onto <b>Str. Ioan Slavici</b>', 'maneuver': 'turn-left', 'polyline': {'points': '{ckzGweidCBF@JPtGHtE@l@?Z'}, 'start_location': {'lat': 46.4289353, 'lng': 21.8429955}, 'travel_mode': 'WALKING'}, {'distance': {'text': '0.3 km', 'value': 314}, 'duration': {'text': '4 mins', 'value': 240}, 'end_location': {'lat': 46.4259289, 'lng': 21.8399752}, 'html_instructions': 'Turn <b>left</b> onto <b>Calea Traian</b>', 'maneuver': 'turn-left', 'polyline': {'points': 'wbkzGmshdCzFHlA@rDBv@@'}, 'start_location': {'lat': 46.4287555, 'lng': 21.8400729}, 'travel_mode': 'WALKING'}, {'distance': {'text': '0.2 km', 'value': 150}, 'duration': {'text': '2 mins', 'value': 112}, 'end_location': {'lat': 46.4257779, 'lng': 21.8419213}, 'html_instructions': 'Turn <b>left</b> onto <b>Calea Republicii</b>/<wbr/><b>DJ792</b><div style="font-size:0.9em">Destination will be on the left</div>', 'maneuver': 'turn-left', 'polyline': {'points': 'aqjzG{rhdC@m@ZuI'}, 'start_location': {'lat': 46.4259289, 'lng': 21.8399752}, 'travel_mode': 'WALKING'}], 'traffic_speed_entry': [], 'via_waypoint': []}], 'overview_polyline': {'points': 'o}jzGodidCkEg@DRZjN@hAhIJjFD\\cK'}, 'summary': 'Str. Ioan Slavici and Calea Traian', 'warnings': ['Walking directions are in beta. Use caution – This route may be missing sidewalks or pedestrian paths.'], 'waypoint_order': []}]
            except BaseException as e:
                print(f"[ WARNING MAPS ] Error is: {e}")
            print(directions_result)
            
            cancel_process_direction_results = False
            wait_cancel_directions = Thread(target=wait_directions_disable, args=())
            wait_cancel_directions.start()
            process_direction_results(directions_result[0]['legs'][0]['steps'])
            wait_cancel_directions.join(1)
        else:
            speak_thread = speak("I'm sorry, I can't obtain your position!")
            speak_thread.join()
        
    bionicane_running = False
    close_serial_thread = True
    speak_thread = speak("Bye bye!")
    speak_thread.join()
    gps_thread.join(2)
    sensor0_thread.join(2)
    sensor1_thread.join(2)
    sensor2_thread.join(2)


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    try:
        main()
    except BaseException as e:
        bionicane_running = False
        print(f"[ MAIN WARNING ] Caught exception {e}!")
        traceback.print_exc()
    ser.close()
    GPIO.cleanup()
