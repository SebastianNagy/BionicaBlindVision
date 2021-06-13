import serial
import time
import string
import pynmea2
import mpu
from threading import Thread


port="/dev/ttyS0"
ser=serial.Serial(port, baudrate=9600, timeout=0.01, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
dataout = pynmea2.NMEAStreamReader()
close_serial_thread = False
last_coords = None

def gps_thread():
    global ser, dataout, close_serial_thread, last_coords
    
    while close_serial_thread == False:
        last_coords = get_gps_coord(ser,dataout)
        print("Thread: ", last_coords)


def get_gps_coord(ser, dataout):
    nr_fails = 0
    ser.flushInput()
    while True:
        newdata=ser.readline()
        newdata_str = str(newdata)[2:]
        newdata_str = newdata_str[:-5]
    
    
        if newdata_str[0:6] == '$GPGLL':
            
            newmsg=pynmea2.parse(newdata_str)
            lat =newmsg.latitude
            lat_dir = newmsg.data[1]
            long =newmsg.longitude
            long_dir = newmsg.data[3]
            
            if lat != 0.0 and long != 0.0:
                return lat, long
            else:
                nr_fails +=1
                
            if nr_fails == 20:
                print("[ POS WARNING] Could not retrieve current position!")
                return 0, 0


if __name__ == "__main__":
    gps_thread = Thread(target=gps_thread)
    gps_thread.start()
    time.sleep(1)
    
    for i in range(6):
        coord = last_coords
        if i > 0:
            d = round(mpu.haversine_distance(coord, old_coord) * 1000)
            print(f"Difference is: {d} meters.")
        else:
            first_coord = coord
        print(coord)
        old_coord = coord
        time.sleep(10)
        
    close_serial_thread = True
    d = round(mpu.haversine_distance(coord, first_coord) * 1000)
    print(f"Beginning vs now difference is: {d} meters.")
    gps_thread.join()
    ser.close()