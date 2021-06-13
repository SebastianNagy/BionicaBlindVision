import googlemaps
import time
import re
import mpu
from datetime import datetime

def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def get_next_step(current_position, directions_result, last_speak, step_size):
    current_step = directions_result[0]
    next_step = directions_result[1]

    distance = round(mpu.haversine_distance(current_position, (current_step['end_location']['lat'], current_step['end_location']['lng'])) * (1000 / step_size))
    print(f"[ INFO DISTANCE ] Distance is {distance} meters.")
    s = next_step['maneuver'].replace("-", " ")
    return_string = f"{s} in {round(distance/step_size)} steps."
    return_string = return_string.replace("Str. ", "")
    if distance <= (25 / step_size):
        speak = 1
        return_string = f"{next_step['maneuver']} now!"
        return_string = return_string.replace("-", " ")
    elif last_speak == 4:
        speak = 2
        print()
        print(f"Current step is {current_step}.")
        print(f"Next step is {next_step}")
    else:
        speak = 0

    return return_string, speak


if __name__ == "__main__":
    mapskey_file = open("mapskey.txt", "r")
    mapskey = mapskey_file.readline()
    # gmaps = googlemaps.Client(key=mapskey)

    now = datetime.now()
    # directions_result = gmaps.directions(origin=(45.749779,21.24252), destination="BRD, Strada Socrate Nr.1, Timișoara", mode="walking", departure_time=now)
    # directions_result = [{'bounds': {'northeast': {'lat': 45.7500191, 'lng': 21.2423001}, 'southwest': {'lat': 45.7494811, 'lng': 21.2406226}}, 'copyrights': 'Map data ©2021', 'legs': [{'distance': {'text': '0.2 km', 'value': 157}, 'duration': {'text': '2 mins', 'value': 111}, 'end_address': 'Aleea Studenților 8, Timișoara, Romania', 'end_location': {'lat': 45.7494811, 'lng': 21.2406226}, 'start_address': 'Strada Daliei 11C, Timișoara, Romania', 'start_location': {'lat': 45.749823, 'lng': 21.2423001}, 'steps': [{'distance': {'text': '24 m', 'value': 24}, 'duration': {'text': '1 min', 'value': 16}, 'end_location': {'lat': 45.7500191, 'lng': 21.2421575}, 'html_instructions': 'Head <b>northwest</b> toward <b>Aleea Studenților</b>', 'polyline': {'points': 'kofvGk{s`Cg@Z'}, 'start_location': {'lat': 45.749823, 'lng': 21.2423001}, 'travel_mode': 'WALKING'}, {'distance': {'text': '0.1 km', 'value': 133}, 'duration': {'text': '2 mins', 'value': 95}, 'end_location': {'lat': 45.7494811, 'lng': 21.2406226}, 'html_instructions': 'Turn <b>left</b> onto <b>Aleea Studenților</b><div style="font-size:0.9em">Destination will be on the left</div>', 'maneuver': 'turn-left', 'polyline': {'points': 'spfvGozs`C~@vDHX\\tABJ'}, 'start_location': {'lat': 45.7500191, 'lng': 21.2421575}, 'travel_mode': 'WALKING'}], 'traffic_speed_entry': [], 'via_waypoint': []}], 'overview_polyline': {'points': 'kofvGk{s`Cg@Z~@vDf@nBBJ'}, 'summary': 'Aleea Studenților', 'warnings': ['Walking directions are in beta. Use caution – This route may be missing sidewalks or pedestrian paths.'], 'waypoint_order': []}]
    directions_result = [{'bounds': {'northeast': {'lat': 45.7500927, 'lng': 21.2423001}, 'southwest': {'lat': 45.7492253, 'lng': 21.2381578}}, 'copyrights': 'Map data ©2021', 'legs': [{'distance': {'text': '0.4 km', 'value': 437}, 'duration': {'text': '5 mins', 'value': 314}, 'end_address': 'Strada Socrate Nr. 1, Timișoara 300551, Romania', 'end_location': {'lat': 45.7494676, 'lng': 21.2381578}, 'start_address': 'Strada Daliei 11C, Timișoara, Romania', 'start_location': {'lat': 45.749823, 'lng': 21.2423001}, 'steps': [{'distance': {'text': '24 m', 'value': 24}, 'duration': {'text': '1 min', 'value': 16}, 'end_location': {'lat': 45.7500191, 'lng': 21.2421575}, 'html_instructions': 'Head <b>northwest</b> toward <b>Aleea Studenților</b>', 'polyline': {'points': 'kofvGk{s`Cg@Z'}, 'start_location': {'lat': 45.749823, 'lng': 21.2423001}, 'travel_mode': 'WALKING'}, {'distance': {'text': '0.2 km', 'value': 201}, 'duration': {'text': '2 mins', 'value': 144}, 'end_location': {'lat': 45.7492253, 'lng': 21.239829}, 'html_instructions': 'Turn <b>left</b> onto <b>Aleea Studenților</b>', 'maneuver': 'turn-left', 'polyline': {'points': 'spfvGozs`C~@vDHX\\tAt@hD'}, 'start_location': {'lat': 45.7500191, 'lng': 21.2421575}, 'travel_mode': 'WALKING'}, {'distance': {'text': '0.1 km', 'value': 118}, 'duration': {'text': '1 min', 'value': 86}, 'end_location': {'lat': 45.7500927, 'lng': 21.2389638}, 'html_instructions': 'Turn <b>right</b>', 'maneuver': 'turn-right', 'polyline': {'points': 'ukfvG}ks`CgAhA[ZgAfA'}, 'start_location': {'lat': 45.7492253, 'lng': 21.239829}, 'travel_mode': 'WALKING'}, {'distance': {'text': '94 m', 'value': 94}, 'duration': {'text': '1 min', 'value': 68}, 'end_location': {'lat': 45.7494676, 'lng': 21.2381578}, 'html_instructions': 'Turn <b>left</b><div style="font-size:0.9em">Destination will be on the right</div>', 'maneuver': 'turn-left', 'polyline': {'points': 'aqfvGofs`CDLJPP\\^l@JLVTRN'}, 'start_location': {'lat': 45.7500927, 'lng': 21.2389638}, 'travel_mode': 'WALKING'}], 'traffic_speed_entry': [], 'via_waypoint': []}], 'overview_polyline': {'points': 'kofvGk{s`Cg@Z~@vDf@nBt@hDgAhAcBbBP^p@jAb@b@RN'}, 'summary': 'Aleea Studenților', 'warnings': ['Walking directions are in beta. Use caution – This route may be missing sidewalks or pedestrian paths.'], 'waypoint_order': []}]

    print(directions_result)
    print(directions_result[0].keys())
    print(directions_result[0]['legs'][0].keys())
    print(directions_result[0]['legs'][0]['steps'])

    for step in directions_result[0]['legs'][0]['steps']:
        print(step)