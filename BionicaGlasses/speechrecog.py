import speech_recognition as sr
from sounds import ding, init_tts, speak
import os
import subprocess as sp

# O lista cu obiectele recunoscute de catre modelul de detectie a obiectelor
COCO_NAMES = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'plant', 'bed', 'N/A', 'dining table',
    'N/A', 'N/A', 'toilet', 'N/A', 'TV', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
    'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]

# Se initializeaza engine-ul pentru recunoasterea vocala
def init_srecog():
    global r_engine
    r_engine = sr.Recognizer()

# Functia porneste o inregistrare audio de 4 secunde ce urmeaza sa fie procesata
def record():
    sp.run(['arecord', '-D', 'hw:2,0', '-d', '4', '-f', 'cd', '/home/pi/Desktop/BionicaV2/files/temp.wav', '-c', '1'], stdout=sp.DEVNULL, stderr=sp.STDOUT)

# Functia asteapta ca utilizatorul sa rosteasca o comanda si o transforma in text
def speech_to_text(filename="", ding_enable=False, name=""):
    global r_engine
    if ding_enable == True:
        ding()
        
    print(f"[ SPEECH {name}] Speak now")
    record()
    print(f"[ SPEECH {name}] Processing recording")
    
    with sr.AudioFile(filename) as source:
    #with sr.Microphone(device_index=2) as source:
        #r_engine.adjust_for_ambient_noise(source)
        
        audio = r_engine.listen(source)
        try:
            text = r_engine.recognize_google(audio)
            print(f"[ SPEECH {name}] Recognized: {text}")
        except sr.UnknownValueError:
            text = ""
            print(f"[ SPEECH {name}] Could not recognize. Please try again!")
        return text

# Aceasta functie asteapta ca utilizatorul sa inceapa dialogul spunand o variatie a comenzii "Hello Bionica"
def wait_hello_bionica():
    global r_engine
    obtained_hello = False
    accepted_bionicas = ["hello", "bionic", "hello bionic", "buy a new car", "hello bionica", "hello bionicle", "hello by Anika", "bionica", "bionicle", "by Anika"]
    while obtained_hello == False:
        text = speech_to_text("/home/pi/Desktop/BionicaV2/files/temp.wav", ding_enable=False, name="HELLO ")
        if text in accepted_bionicas:
            obtained_hello = True
        if text == "exit":
            break
    return not obtained_hello

# Aceasta functie asteapta a doua comanda de la utilizator, dupa ce a spus "Hello Bionica"
# El poate cere detectia obiectelor intr-o imagine, descrierea unei imaginii sau cautarea unei anumite persoane
def wait_object():
    fails = 0
    text_type = None
    while True:
        text = get_speech(ding=True)
        
        if "describe" in text:
            text_type = "labels"
            break
        elif "can you find" in text:
            text = text[13:]
            text_type = "face"
            break
        elif text in ["what do I see", "what to do IC", "what boycie"]:
            text = "what do I see"
            text_type = "obj"
            break
        elif text in ["exit"] or text in COCO_NAMES:
            text_type = "obj"
            break
        #elif "Where is" in text:
        
        fails +=1
        if fails == 3:
            th = speak("Please try again!")
            text = "fail"
            break
        
        th = speak("Please Repeat!")
        th.join()
        
    return text, text_type

# Functia asteapta comanda "Guide me" in urma gasirii unui anume obiect
def wait_guide_me():
    fails = 0
    while True:
        text = get_speech(ding=False)
        if text in ["Guide Me", "guide"]:
            break
        fails +=1
        if fails == 3:
            text = "fail"
            break
    return text

# Functia transforma un fisier audio in text, folosita pentru testare
def get_speech(ding=False): 
    print("[ SPEECH ] Waiting for speech")
    text = speech_to_text("/home/pi/Desktop/BionicaV2/files/temp.wav", ding_enable=ding)  
    return text

if __name__ == '__main__':
    init_tts()
    init_srecog()
    #speech_to_text(filename="/home/pi/Desktop/BionicaV2/files/whatdoisee.wav", ding_enable=True)
    #speech_to_text(filename="", ding_enable=True)
    wait_hello_bionica()
    