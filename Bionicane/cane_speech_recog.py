import speech_recognition as sr
from cane_sounds import ding, init_tts, speak
import os
import subprocess as sp


# Se initializeaza engine-ul pentru recunoasterea vocala
def init_srecog():
    global r_engine
    r_engine = sr.Recognizer()


# Functia porneste o inregistrare audio de 4 secunde ce urmeaza sa fie procesata
def record():
    sp.run(['arecord', '-D', 'hw:2,0', '-d', '4', '-f', 'cd', '/home/pi/Desktop/Bionicane/files/temp.wav', '-c', '1'],
           stdout=sp.DEVNULL, stderr=sp.STDOUT)


# Functia transforma un fisier audio in text, folosita pentru testare
def get_speech(ding=False):
    print("[ SPEECH ] Waiting for speech")
    text = speech_to_text("/home/pi/Desktop/Bionicane/files/temp.wav", ding_enable=ding)
    return text


# Functia asteapta ca utilizatorul sa rosteasca o comanda si o transforma in text
def speech_to_text(filename="", ding_enable=False, name=""):
    global r_engine
    if ding_enable == True:
        ding()

    print(f"[ SPEECH {name}] Speak now")
    record()
    print(f"[ SPEECH {name}] Processing recording")

    with sr.AudioFile(filename) as source:
        # with sr.Microphone(device_index=2) as source:
        # r_engine.adjust_for_ambient_noise(source)

        audio = r_engine.listen(source)
        try:
            text = r_engine.recognize_google(audio)
            print(f"[ SPEECH {name}] Recognized: {text}")
        except sr.UnknownValueError:
            text = ""
            print(f"[ SPEECH {name}] Could not recognize. Please try again!")
        return text


# Aceasta functie asteapta ca utilizatorul sa inceapa dialogul spunand o variatie a comenzii "Hello Bionica"
def wait_hello_cane():
    global r_engine
    obtained_hello = False
    accepted_bionicas = ["hello", "bionic cane", "hello bionic cane",   "hello bionicle", "bionicle", "bionic pain",
                         "hello Cain", "hello Keane", "Cain", "Keane", "hello Ken", "hello by any cane"]
    while obtained_hello == False:
        text = speech_to_text("/home/pi/Desktop/Bionicane/files/temp.wav", ding_enable=False, name="HELLO ")
        if text in accepted_bionicas:
            obtained_hello = True
        if text == "exit":
            break
    return not obtained_hello


# Aceasta functie asteapta a doua comanda de la utilizator, dupa ce a spus "Hello Bionica"
# El poate cere detectia obiectelor intr-o imagine, descrierea unei imaginii sau cautarea unei anumite persoane
def wait_address(known_locations_dict):
    fails = 0
    addr = None
    addr_type = None
    while True:
        text = get_speech(ding=True)

        if "emergency" in text:
            addr = ""
            addr_type = "email"
            break
        elif "take me to" in text:
            addr = text[11:]
            
            if addr in known_locations_dict.keys():
                addr = known_locations_dict[addr]
                addr_type = "known_location"
                break
            else:
                addr_type = "unknown_location"
            # break

        fails += 1
        if fails == 3:
            th = speak("Please try again!")
            addr_type = "fail"
            break

        th = speak("Please Repeat!")
        th.join()

    return addr, addr_type


if __name__ == '__main__':
    init_tts()
    init_srecog()
    # speech_to_text(filename="/home/pi/Desktop/BionicaV2/files/whatdoisee.wav", ding_enable=True)
    # speech_to_text(filename="", ding_enable=True)
    wait_hello_cane()
