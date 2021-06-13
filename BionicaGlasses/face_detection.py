import cv2
import dlib
import datetime
import numpy as np
import face_recognition


# Functie cu scop utilitar de a extrage fata unei persoane si de a o salva pentru folosiri viitoare
def save_face(input_image_path, filename):
    input_image = cv2.imread(input_image_path)
    global dlib_face_detector, source_img
    #resized_image = cv2.resize(input_image, (800, 600))
    resized_image = input_image
    gray_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    rectangles = dlib_face_detector(gray_image, 1)

    for rec in rectangles:
        x, y, w, h = get_face(rec)
        face = resized_image[y:y + h, x:x + w]
        face = cv2.resize(face, (128, 128))
        cv2.rectangle(resized_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imshow("face", face)
        cv2.waitKey(0)
        cv2.imwrite(f"faces/{filename}.jpg", face)

# O versiune primitiva a algoritmului de comparare a doua fete
'''
def euclidian_compare(img1, img2):  # unused
    global n_samples, s_score
    #score = cosine(img1, img2)
    #score = np.sum((img1-img2)**2)
    score = compare_ssim(img1, img2)
    n_samples += 1
    s_score += score

    if score >= 0.275:
        print(f"[ INFO ] Match with score {score} --- average is {s_score/n_samples}")
        return True
    print(f"[ INFO ] No match with score {score} --- average is {s_score/n_samples}")
    return False
'''

# Functie utilitara pentru a obtine coordonatele fetei dintr-o poza, in final nefolosita
def get_face(rect):
    x = rect.left()
    y = rect.top()
    w = rect.right() - x
    h = rect.bottom() - y
    return x, y, w, h

# Functie pentru a procesa o imagine si a extrage fetele dintr-o poza
# Se foloseste de prima versiune de face detector, in final nefolosita
def process_image(input_image):
    global dlib_face_detector, source_img, name
    # resized_image = cv2.resize(input_image, (800, 600))  # works better if it's not resized
    # gray_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)  # works better if it's RGB
    
    rectangles = dlib_face_detector(input_image, 1)
    
    for rec in rectangles:
        x, y, w, h = get_face(rec)
        face = input_image[y:y+h, x:x+w]
        face = cv2.resize(face, (128, 128))
        #face = cv2.cvtColor(face, cv2.COLOR_RGB2GRAY)
        cv2.rectangle(input_image, (x, y), (x + w, y + h), (0, 0, 0), 2)

        time_start = datetime.datetime.now()
        #euclidian_value = euclidian_compare(Image.fromarray(source_img), Image.fromarray(face))#.flatten())
        result = face_recog_compare(source_img, face)[0]
        
        time_stop = datetime.datetime.now()
        cv2.putText(input_image, f"{name} - {result}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        a = time_stop - time_start
        
        print(f"[ INFO ] Comparison took {a.microseconds / 1000}ms.")

    return input_image

# Aceasta functie primeste doua imagini (cu fete) si returneaza daca ele sunt aceeasi persoana sau nu
def face_recog_compare(img1, img2):
    img1_enconding = face_recognition.face_encodings(img1, known_face_locations=[[0, 128, 128, 0]])[0]
    img2_enconding = face_recognition.face_encodings(img2, known_face_locations=[[0, 128, 128, 0]])[0]
    result = face_recognition.compare_faces([img1_enconding], img2_enconding)
    return result

# Functie pentru debugging a primei versiuni de face detector
def test_video():
    cap = cv2.VideoCapture("FacesVids/videoteo.mp4")
    if not cap:
        print("[ ERROR ] Video camera can't be opened")
    while True:
        ret, current_frame = cap.read()

        start_process_img = datetime.datetime.now()
        current_frame = process_image(current_frame)
        end_process_img = datetime.datetime.now()
        time = end_process_img - start_process_img
        fps = 1 / (time.microseconds / 10**6)
        cv2.putText(current_frame, f"FPS: {fps}", (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        cv2.imshow('frame', current_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# O prima versiune a face detector-ului, in final nefolosit
def init_face_detector():
    global dlib_face_detector
    print(f"[ INFO ] Loading face detection model")
    start_load_face_det = datetime.datetime.now()
    dlib_face_detector = dlib.get_frontal_face_detector()
    end_load_face_det = datetime.datetime.now()
    a = end_load_face_det - start_load_face_det
    print(f"[ INFO ] Face detection model loaded in {a.seconds}s -- {a.microseconds/1000}ms.")


if __name__ == "__main__":
    name = "teo"
    source_img = cv2.imread(f"faces/{name}.jpg")#.flatten()

    init_face_detector()

    #save_face("teo.jpeg", "teo2")
    #exit()
    n_samples = 0
    s_score = 0
    
    test_video()
