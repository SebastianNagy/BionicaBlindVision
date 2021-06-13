from google.cloud import vision
from google.cloud import storage
import io
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/pi/Desktop/BionicaV2/key/bionica-313019-67b05b67582e.json"

# Functia care se foloseste de Google Cloud pentru descrierea unei imagini
def detect_labels(path):
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    
    response = client.label_detection(image=image)
    labels = response.label_annotations

    labels_string = ""
    for label in labels:
        labels_string += label.description + ", "
        #print(label.description)

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    
    if labels_string == "":
        labels_string = "I'm afraid I can't describe what I see."
    
    print(f"[ INFO ] Labels: {labels_string}")
    
    return labels_string
    

# Functie pentru a verifica reusita conexiunii la serviciile Google Cloud
def check_auth():
    storage_client = storage.Client()

    buckets = list(storage_client.list_buckets())
    print(buckets)


# Functie pentru a mima comportamentul detect_labels, pentru a evita o taxare din partea Google. Folosit pentru debugging
def mimic_detect_labels():
    labels = ["Cloud", "Sky", "Green", "Plant", "Natural landscape" ,"Slope","People in nature","Land lot", "Grass", "Grassland"]
    if labels != []:
        labels_string = ", ".join(labels)
    else:
        labels_string = "I'm afraid I can't describe this picture."
    
    return labels_string


if __name__ == "__main__":
    # check_auth()
    # detect_labels("xp.jpg")
    mimic_detect_labels()


