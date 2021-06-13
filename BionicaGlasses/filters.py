from PIL import Image, ImageStat
import time
import cv2
import datetime
import numpy as np
from skimage.filters import threshold_yen
from skimage.exposure import rescale_intensity

# Functia face o poza folosindu-se de camera si afiseaza poza modificata
# Cu diferiti algoritmi pentru deblurring sau de crestere a luminozitatii
# Functia a fost folosita pentru testarea si obtinerea celui mai eficient algoritm
def take_picture():
    cap = cv2.VideoCapture(0)
    ret,frame = cap.read()
    frame = cv2.resize(frame, (800, 600))
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    time_start = datetime.datetime.now()
    bright = get_brightness(gray_frame)
    print(f"Image brightness is {bright}")
    time_brightness = datetime.datetime.now()

    res_img = alpha_beta_increase_brightness(frame, bright)
    time_increased_brightness = datetime.datetime.now()
    blur = get_blur(gray_frame)
    time_blur = datetime.datetime.now()
    print(f"Blur is {blur}")

    a = time_brightness - time_start
    b = time_increased_brightness - time_brightness
    c = time_blur - time_increased_brightness
    print(f"Brightness check takes {a.microseconds/1000} ms; Increasing brightness takes {b.microseconds/1000}ms; Blur takes {c.microseconds/1000}ms")

    cv2.imshow('img1',frame) #display the captured image
    cv2.imshow("increased_brightness", res_img)
    cv2.imshow("sharpened_img", sharpened_img)
    cv2.imshow("enhanced_img", enhanced_img)
    cv2.waitKey(0)

    cv2.imwrite("pic.jpg", frame)

    cap.release()
    cv2.destroyAllWindows()


# Aceasta functie este folosita pentru obtinerea unei valori ce cuantizeaza luminozitatea dintr-o imagine
def get_brightness(gray_image):
   im = Image.fromarray(gray_image)
   stat = ImageStat.Stat(im)
   return stat.rms[0]


# Prima, si cea mai slaba, versiune a algoritmului de crestere a luminozitatii
def increase_brightness(img, value):
    res_img = cv2.add(img, value)
    return res_img

# A doua versiune a algoritmului de crestere a luminozitatii
def hsv_increase_brightness(img, value):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    h += value
    merged = cv2.merge((h, s, v))
    res_img = cv2.cvtColor(merged, cv2.COLOR_HSV2RGB)
    return res_img

# A treia versiune a algoritmului de crestere a luminozitatii
def yen_method_increase_brightness(img):
    yen_threshold = threshold_yen(img)
    res_img = rescale_intensity(img, (0, yen_threshold), (0, 255))
    return res_img

# Ultima, si cea mai buna, metoda pentru cresterea luminozitatii dintr-o poza.
# Aceasta este metoda folosita in final in Bionica.
def alpha_beta_increase_brightness(img, bright):
    if bright < 125:
        min_bright = np.clip(125, 0, bright*5)
        print(f"[ INFO ] Brightness of the image is now {min_bright} instead of {bright}.")

        beta = 0
        alpha = min_bright / bright
        return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    else:
        return img


# A doua functie de testare a algoritmilor, aceasta aplicandu-i continuu pe un video, nu doar pe o poza
def testing():
    cap = cv2.VideoCapture("FilterVids/medium_white_light.mp4")
    value = 60
    while True:
        ret, frame = cap.read()
        frame = cv2.resize(frame, (800, 600))
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        bright = get_brightness(gray_frame)
        blur = get_blur(gray_frame)

        time_start = datetime.datetime.now()

        alpha_beta_frame = alpha_beta_increase_brightness(frame, bright)
        time_alpha_beta = datetime.datetime.now()

        hsv_frame = hsv_increase_brightness(frame, value)
        time_hsv = datetime.datetime.now()

        #yen_frame = np.asarray(yen_method_increase_brightness(frame), dtype=np.uint8)
        #time_yen = datetime.datetime.now()

        alpha_beta_bright = get_brightness(alpha_beta_frame)
        hsv_bright = get_brightness(hsv_frame)
        #yen_bright = get_brightness(yen_frame)

        a = time_alpha_beta - time_start
        b = time_hsv - time_alpha_beta
        
        time_blur1 = datetime.datetime.now()
        alpha_beta_blur = get_blur(cv2.cvtColor(alpha_beta_frame, cv2.COLOR_RGB2GRAY))
        enhanced_img = cv2.detailEnhance(alpha_beta_frame, sigma_s=5, sigma_r=0.15)
        time_blur2 = datetime.datetime.now()
        c = time_blur2 - time_blur1
        
        cv2.putText(frame,f"BLUR: {blur}", (10,40), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(alpha_beta_frame, f"BLUR: {alpha_beta_blur}", (10, 40), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        print(f"Image brightness is {bright} vs {hsv_bright} vs {alpha_beta_bright}")
        print(f"Alpha beta method: {a.microseconds/1000}ms -- hsv method: {b.microseconds/1000}ms")
        print(f"Blur method: {c.microseconds/1000}ms")
        cv2.imshow('frame', frame)
        #cv2.imshow('hsv_frame', hsv_frame)
        cv2.imshow('enhanced_img', enhanced_img)
        #cv2.imshow('yen_frame', yen_frame)
        cv2.imshow('alpha_beta_frame', alpha_beta_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        # time.sleep(0.01)
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # take_picture()
    testing()
