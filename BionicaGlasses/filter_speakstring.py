from collections import Counter
import numpy as np

# Functia primeste o lista cu coordonatele fetelor detectate
def face_build_speakstring(det_objects, det_boxes, shape, name, distance):
    speakstring = ""
    if len(det_objects) == 0:  # Daca nu se gaseste nici o persoana, utilizatorul este atentionat
        speakstring = f"I can't see {name}."
    elif len(det_objects) == 1:  # Daca este o singura fata, inseamna ca e persoana cautata
        # In continuare, se construieste string-ul cu pozitia persoanei ce va fi spus utilizatorului 
        speakstring = f"{name} is "
        if det_boxes[0][0] <= int(shape[1]/3):
            speakstring += " to your left, "
        elif det_boxes[0][0] > int(shape[1]/3) and det_boxes[0][0] < int(shape[1]/3)*2:
            speakstring += " in front of you, "
        else:
            speakstring += " to your right, "
        
        speakstring += f"{int(distance[0]/550)} steps away"
    elif len(det_objects) > 1:
        speakstring = f"I see multiple {name}."
        
    return speakstring


# Functia primeste o lista cu obiectele detectate si pozitiile lor
# Si construieste string-uri care sa descrie aceasta pozitie
# Ex.: "Book to your left, Bed in front of you"
def build_speakstring(det_objects, det_boxes, shape):
    speakstring = ""

    for i in range(len(det_objects)):
        speakstring += " " + det_objects[i]
        if det_boxes[i][0] <= int(shape[1]/3):
            speakstring += " to your left"
        elif det_boxes[i][0] > int(shape[1]/3) and det_boxes[i][0] < int(shape[1]/3)*2:
            speakstring += " in front of you"
        else:
            speakstring += " to your right"
        speakstring += ","
    
    return speakstring

# Aceasta functie are scopul de a modifica stringul care va fi spus, astfel incat sa sune cat mai "uman"
def filter_speakstring(speakstring, text_object):  
    final_string = ""
            
    if text_object != "what do I see":
        
        obj_pos = speakstring.find(text_object)
        while obj_pos >= 0:
            comma_pos = speakstring.find(",",obj_pos)
            final_string += " " + speakstring[obj_pos:comma_pos] + ","
            obj_pos = speakstring.find(text_object, comma_pos)
        if final_string == "":
            final_string = "I can't see any " + text_object
    else:
        final_string = speakstring
        
        
    if final_string != "" and final_string[-1] == ',':
        final_string = final_string[:-1]
    return final_string


# Aceasta functie are scopul de sterge aparitiile multiple ale aceluiasi obiect
# De exemplu, daca detectam 2 carti, in loc de "There is a book to your left, There is book to your left"
# Se va spune "There are 2 books to your left"
def remove_duplicates(speakstring, distance, text_object):
    final_string = ""
    list_string = speakstring.split(",")
    list_string.sort()
    
    unique_list = list(Counter(list_string).keys())
    list_nr     = list(Counter(list_string).values())
    
    if unique_list == ['']:
        unique_list = []
    
    if text_object == "what do I see":
        if len(unique_list) == 1 and list_nr[0] == 1:
            final_string = "There is "
        elif len(unique_list) > 0:
            final_string = "There are "
        else:
            final_string = "I can't recognize any object"
            
    for i in range(len(unique_list)):
        if list_nr[i] == 1:
            if text_object != "what do I see":
                final_string += "There is 1" + unique_list[i] + ", "
            else:
                final_string += "1" + unique_list[i] + ", "
        else:
            if text_object != "what do I see":
                final_string += "There are " + str(list_nr[i]) + unique_list[i] + ", "
            else:
                final_string += " " + str(list_nr[i]) + unique_list[i] + ", "
       
    # De asemenea, daca se cauta un anume obiect, se estimeaza si distanta pana la el
    if len(unique_list) == 1 and text_object != "what do I see":
        final_string += f"{int(distance[0]/550)} steps away"
        
    if final_string[-2] == ',':
        final_string = final_string[:-2]
    return final_string
