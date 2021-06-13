import pyttsx3
import time
from pygame import mixer
from threading import Thread


# Functia aceasta initializeaza engine-ul text to speech
def init_tts():
    global engine, beep, careful
    engine = pyttsx3.init()
    engine.setProperty('voice', 'english_rp')
    engine.setProperty('rate', 175)
    engine.setProperty('volume', 1)

    mixer.init()
    beep = mixer.Sound("/home/pi/Desktop/Bionicane/files/ding.wav")
    careful = mixer.Sound("/home/pi/Desktop/Bionicane/files/becareful.wav")


# Functia primeste un string si il reda pe cale audio utilizatorului
def speak_function(s):
    global engine
    engine.say(s)
    try:
        engine.runAndWait()
    except RuntimeError as e:
        print("[ WARNING ] TTS engine is already saying something!")


# Functia porneste un Thread in paralel cu firul principal de executie, care va reda mesajul audio
def speak(s):
    th = Thread(target=speak_function, args=(s,))
    th.start()
    return th


# Functia reda o atentionare audio "Be careful!" pentru ca utilizatorul sa stie ca un obiect este in fata lui
def becareful():
    global careful
    careful.play()
    time.sleep(1)


# Functia reda un semnal audio, pentru ca utilizatorul sa stie cand poate spune o comanda
def ding():
    global beep
    beep.play()
    time.sleep(0.75)


if __name__ == '__main__':
    init_tts()
    ding()
    th = speak("I don't see anything")
    th.join()
    becareful()

