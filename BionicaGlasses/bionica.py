from picamera.array import PiRGBArray
from picamera import PiCamera
from object_detection_base import init_myriad, draw_detections, ColorPalette
from speechrecog import *
from sounds import *
from filter_speakstring import *
from sensor import *
from filters import get_brightness, alpha_beta_increase_brightness
from detect_labels import *
from PIL import Image, ImageStat
import cv2
import datetime
import traceback
import os

vid_enable = False  # Variabila de control pentru activarea si dezactivarea modului video
bionica_running = True  # Variabila de control pentru loop-ul principal al programului
username = "Dora"

# Aceasta functie se foloseste de camera pentru a face o poza 
def take_picture():
    global camera, rawCapture
    camera.capture(rawCapture, format="bgr")
    image = rawCapture.array
    image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    rawCapture.truncate(0)
    
    
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  # Imaginea se converteste in grayscale
    bright = get_brightness(gray_image)  # Pentru a obtine nivelul luminozitatii
    alpha_beta_frame = alpha_beta_increase_brightness(image, bright)  # Daca luminozitatea este scazuta, se aplica un filtru de crestere a acesteia
    
    return alpha_beta_frame  

# Functia proceseaza o imagine aplicand modelul de detectie a obiectelor asupra ei, si returneaza obiectele recunoscute
def obj_det_process_image(input_image, display=True):
    global obj_det_next_frame_id, obj_det_next_frame_id_to_show, obj_det_detector_pipeline, obj_det_model
    # obj_det_start = datetime.datetime.now()  # Metrics
    
    while True:
        # Daca pipeline-ul datelor a intalnit o eroare, se semnaleaza acest lucru
        if obj_det_detector_pipeline.callback_exceptions:
            raise obj_det_detector_pipeline.callback_exceptions[0]
        
        # Se obtin rezultatele in urma procesarii
        results = obj_det_detector_pipeline.get_result(obj_det_next_frame_id_to_show)
        if results:
            print(f"[ INFO ] Image with ID {obj_det_next_frame_id_to_show} received")
            objects, frame_meta = results
            frame = frame_meta['frame']
            
            # Se deseneaza conturul obiectelor detectate in poza
            frame, detected_objects, detected_boxes = draw_detections(frame, objects, palette, obj_det_model.labels, 0.6, False)
            
            if display:  # Afisam imaginea pentru debugging
                left_x = int(frame.shape[1]/3)
                right_x = int(frame.shape[1]/3)*2
                cv2.line(frame, (int(left_x), 0), (int(left_x), frame.shape[0]), (0, 0, 0), 2)
                cv2.line(frame, (int(right_x), 0), (int(right_x), frame.shape[0]), (0, 0, 0), 2)
                
                cv2.imwrite(f"results/obj_{obj_det_next_frame_id_to_show}.jpg", frame)
            
                #cv2.imshow(f"Result {obj_det_next_frame_id_to_show}", frame)
                #key = cv2.waitKey(5000)
                #cv2.destroyAllWindows()
            
            obj_det_next_frame_id_to_show += 1
            break
        
        # Daca pipeline-ul este liber pentru a primi o imagine noua spre procesare, aceasta imagine se trimite in pipeline
        if obj_det_detector_pipeline.is_ready():
            print(f"[ INFO ] Image with ID {obj_det_next_frame_id} sent to pipeline")
            obj_det_detector_pipeline.submit_data(input_image, obj_det_next_frame_id, {'frame': input_image, 'start_time': 0})
            obj_det_next_frame_id += 1
        else:  # Daca nu, se asteapta ca pipeline-ul sa se elibereze 
            print("[ INFO ] Pipeline await any")
            obj_det_detector_pipeline.await_any()
            
    # Metrics  
    # obj_det_stop = datetime.datetime.now()
    # a = obj_det_stop - obj_det_start
    # print(f"[ METRICS ] Face detection took {a.seconds}s and {a.microseconds / 1000}ms.")
    
    return frame, detected_objects, detected_boxes

# Functia asteapta ca utilizatorul sa spuna ca doreste oprirea modului video
# Adica, nu mai doreste sa fie ghidat catre un obiect
def wait_vid_disable():
    global vid_enable
    print("[ SPEECH ] Waiting for video disable")
    while vid_enable == True:
        text = speech_to_text("/home/pi/Desktop/BionicaV2/files/temp.wav", ding_enable=False, name="VIDEO ")
        if text in ["thank you", "disable", "ok", "okay", "ok bionica", "okay bionica", "thanks"]:
            vid_enable = False

# Aceasta functie este folosita pentru a ghida utilizatorul catre un anumit obiect
def obj_det_process_video(text):
    global vid_enable, camera, rawCapture, obj_det_next_frame_id_to_show
    correct = 0
    wrong = 0
    print("[ INFO ] Starting video recording")
    # Se incepe o inregistrare video folosindu-ne de camera conectata la raspberry
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port="True"):
        image = frame.array
        rawCapture.truncate(0)
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        bright = get_brightness(gray_image)
        alpha_beta_frame = alpha_beta_increase_brightness(image, bright)
        # Imaginea este procesata precum in modul in care se lucreaza cu o singura imagine        
        image, detected_objects, detected_boxes = obj_det_process_image(alpha_beta_frame, display=False)
        cv2.imwrite(f"results/obj_{obj_det_next_frame_id_to_show}.jpg", image)
        
        #cv2.imshow("Video", image)
        #key = cv2.waitKey(25)
        #if key in {ord('q'), ord('Q')}:
        #    vid_enable = False
        #    break
            
        # Utilizatorul este incurajat daca merge in directia buna, sau atentionat daca nu
        if text in detected_objects:
            if wrong > 0 and correct == 0:
                speak_thread = speak("You're okay now!")
            correct += 1
            wrong = 0
            if correct % 4 == 0 and correct > 0:
                speak_thread = speak("Keep going!")
        else:
            if correct > 0 and wrong == 0:
                speak_thread = speak("Wrong direction!")
            wrong +=1
            correct = 0
            if wrong % 4 == 0 and wrong > 0:
                speak_thread = speak("Wrong direction!")
            if wrong == 10:
                speak("Please try again!")
                vid_enable = False
        if vid_enable == False:
            break
            
    cv2.destroyAllWindows()

# Aceasta functie are scopul de a atentiona utilizatorul pe cale audio daca este prea aproape de un obiect
# Si deci, se poate lovi
def sensor():
    global bionica_running
    while bionica_running == True:
        distance = get_sensor_distance()
        if distance < 30.0:
            print(f"[ INFO ] Distance: {distance}cm\n")
            try:
                becareful()
            except RuntimeError:
                print("[ WARNING ] Be careful while speaking")


# Functia de mai jos se ocupa cu procesarea imaginii atunci cand utilizatorul cauta o anumita persoana
def face_det_process_image(input_image, source_person, person_name, display=True):
    global face_det_next_frame_id, face_det_next_frame_id_to_show, face_det_detector_pipeline, face_det_model
    # face_det_start = datetime.datetime.now()  # Metrics
    
    while True:
        # Daca pipeline-ul datelor a intalnit o eroare, se semnaleaza acest lucru
        if face_det_detector_pipeline.callback_exceptions:
            raise face_det_detector_pipeline.callback_exceptions[0]
        
        # Se obtin rezultatele in urma procesarii
        results = face_det_detector_pipeline.get_result(face_det_next_frame_id_to_show)
        if results:
            print(f"[ INFO ] Image with ID {face_det_next_frame_id_to_show} received")
            objects, frame_meta = results
            frame = frame_meta['frame']
            
            # Daca persoana cautata se gaseste in poza, fata acesteia este conturata
            frame, detected_objects, detected_boxes = draw_detections(frame, objects, palette, face_det_model.labels, 0.6, False, True, source_person, person_name)
            
            if display:  # Se afiseaza imaginea pentru debugging
                left_x = int(frame.shape[1]/3)
                right_x = int(frame.shape[1]/3)*2
                cv2.line(frame, (int(left_x), 0), (int(left_x), frame.shape[0]), (0, 0, 0), 2)
                cv2.line(frame, (int(right_x), 0), (int(right_x), frame.shape[0]), (0, 0, 0), 2)
                
                cv2.imwrite(f"results/face_{face_det_next_frame_id_to_show}.jpg", frame)
                #cv2.imshow(f"Result {face_det_next_frame_id_to_show}", frame)
                #key = cv2.waitKey(5000)
                #cv2.destroyAllWindows()
            face_det_next_frame_id_to_show += 1
            break
        
        # Daca pipeline-ul este liber pentru a primi o imagine noua spre procesare, aceasta imagine se trimite in pipeline
        if face_det_detector_pipeline.is_ready():
            print(f"[ INFO ] Image with ID {face_det_next_frame_id} sent to pipeline")
            face_det_detector_pipeline.submit_data(input_image, face_det_next_frame_id, {'frame': input_image, 'start_time': 0})
            face_det_next_frame_id += 1
        else:  # Daca nu, se asteapta ca pipeline-ul sa se elibereze
            print("[ INFO ] Pipeline await any")
            face_det_detector_pipeline.await_any()
            
    # Metrics     
    # face_det_stop = datetime.datetime.now()
    # a = face_det_stop - face_det_start
    # print(f"[ METRICS ] Face detection took {a.seconds}s and {a.microseconds / 1000}ms.")
    
    return frame, detected_objects, detected_boxes

# Firul principal al evenimentelor
def main():
    global camera, rawCapture, obj_det_model, obj_det_detector_pipeline, face_det_model, face_det_detector_pipeline, palette, face_det_next_frame_id, face_det_next_frame_id_to_show, obj_det_next_frame_id, obj_det_next_frame_id_to_show, vid_enable, bionica_running
    print("[ INFO ] Initializing text to speech engine" )
    init_tts()  # Se initializeaza modulul text to speech
    print("[ INFO ] Initializing speech to text engine" )
    init_srecog()  # Se initializeaza modulul de recunoastere vocala
    print("[ INFO ] Initializing sensor" )
    setup_sensor()  # Se initializeaza senzorul
    
    # Se initializeaza camera
    camera = PiCamera()
    camera.resolution = (800, 608)
    camera.framerate = 30
    rawCapture = PiRGBArray(camera)
    # Se incarca retelele de recunoastere faciala si a obiectelor pe NCS2
    obj_det_model, obj_det_detector_pipeline, face_det_model, face_det_detector_pipeline = init_myriad()
    palette = ColorPalette(len(obj_det_model.labels) if obj_det_model.labels else 100)
    obj_det_next_frame_id = 0
    obj_det_next_frame_id_to_show = 0
    face_det_next_frame_id = 0
    face_det_next_frame_id_to_show = 0
    
    print("[ INFO ] Ready to go!")
    speak_thread = speak(f"Hello {username}!")
    speak_thread.join()
    
    # Se porneste senzorul
    sensor_thread = Thread(target=sensor)
    sensor_thread.start()
    
    while True:
        # Daca utilizatorul a cerut acest lucru, bionica se opreste
        is_exit = wait_hello_bionica()
        if is_exit:
            bionica_running = False
            break
        speak_thread = speak(f"Yes, {username}?")
        speak_thread.join()
        
        # Se asteapta o comanda
        text, text_type = wait_object()
        
        if text == "fail":
            continue
        
        # Utilizatorul poate alege descrierea unei imagini
        if text_type == "labels":
            img = take_picture()
            cv2.imwrite("results/label_img.jpg", img)
            
            #labels_string = mimic_detect_labels()
            labels_string = detect_labels("results/label_img.jpg")
            speak_thread = speak(labels_string)
            speak_thread.join()
        
        # Sau recunoasterea unei anumite persoane
        elif text_type == "face":
            
            if not os.path.isfile(f"faces/{text}.jpg"):
                speak_thread = speak(f"I don't know who {text} is!")
                speak_thread.join()
                continue  # Restart loop
            imlooking()   
            print(f"[ INFO ] Loading face of {text}")
            source_person = cv2.imread(f"faces/{text}.jpg")
            frame, det_objs, det_boxes = face_det_process_image(take_picture(), source_person, text, display=True)
            if det_boxes != []:
                np_det_boxes = np.array(det_boxes)
                distance = np_det_boxes[:,2]
            else:
                distance = 0
                
            final_str = face_build_speakstring(det_objs, det_boxes, frame.shape, text, distance)
            
            print(f"[ SPEECH ] {final_str}")
            speak_thread = speak(final_str)
            speak_thread.join()
         
        # Recunoasterea obiectelor
        elif text_type == "obj":
            imlooking()   
            frame, det_objs, det_boxes = obj_det_process_image(take_picture(), display=True)   
            if det_boxes != []:
                np_det_boxes = np.array(det_boxes)
                distance = np_det_boxes[:,2]
            else:
                distance = 0
            speakstring = build_speakstring(det_objs, det_boxes, frame.shape)
            filtered_str = filter_speakstring(speakstring, text)
            if "I can't see any" not in filtered_str:
                final_str = remove_duplicates(filtered_str, distance, text)
            else:
                final_str = filtered_str
                
            print(f"[ SPEECH ] {final_str}")
            speak_thread = speak(final_str)
            speak_thread.join()
        
            if text != "what do I see" and "I can't see any" not in final_str:
                obj = text
                
                #text = wait_guide_me()
                #if text == "fail":
                #    continue
        
                vid_enable = True
                vid_listen_thread = Thread(target=wait_vid_disable, args=())
                vid_listen_thread.start()
                obj_det_process_video(obj)
                
                time.sleep(1)
                speak_thread = speak("Congratulations!")
                speak_thread.join()
    sensor_thread.join(2)
    speak_thread = speak("Bye bye!")
    speak_thread.join()


if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    try:
        main()
    except BaseException as e:
        print(f"[ WARNING ] Caught exception {e}!")
        traceback.print_exc()
    GPIO.cleanup()
