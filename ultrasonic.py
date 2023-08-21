import time
import requests
import math
import random
import RPi.GPIO as GPIO
from datetime import datetime
import sqlite3
#from pymongo.mongo_client import MongoClient

#uri = "mongodb+srv://prayogoaan:SlXg2lmR2tTQ0iDh@cluster0.hr3gng9.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
#client = MongoClient(uri)


TOKEN = "BBFF-SPIdNe2oiBj1aHhXaA4App7zHsXczY"
DEVICE_LABEL = "chairiot"
VARIABLE_LABEL_1 = "ultrasonicatas"
VARIABLE_LABEL_2 = "ultrasonicbawah"
VARIABLE_LABEL_3 = "punggung"
VARIABLE_LABEL_4 = "duduk"

GPIO.setmode(GPIO.BCM)

#set GPIO Pins
GPIO_TRIGGER1 = 18
GPIO_ECHO1 = 15
GPIO_TRIGGER2 = 22
GPIO_ECHO2 = 23
LEDR = 25
LEDG = 8
buzzer = 4
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER1, GPIO.OUT)
GPIO.setup(GPIO_ECHO1, GPIO.IN)
GPIO.setup(GPIO_TRIGGER2, GPIO.OUT)
GPIO.setup(GPIO_ECHO2, GPIO.IN)
GPIO.setup(LEDG, GPIO.OUT)
GPIO.setup(LEDR, GPIO.OUT)
GPIO.setup(buzzer,GPIO.OUT)


'''def simpan_data(payload):
    res = {}
    try:
        print("\nmasuk fungsi simpan data\n")
        db = client['SIC4']
        my_collection = db['Kelompok24'] # diganti sesuai nomor kelompok 
        payload.update({'createdAt':int(time.time())})
        my_collection.insert_one(payload)
    except Exception as e:
        print(e)'''

DB_NAME = "dataSensor.db"
con = False

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


con = sqlite3.connect(DB_NAME)  #membuat koneksi python ke Database
con.row_factory = dict_factory
print("\n")

if con:
    print("Sukses konek ke DB")
else:
    print("Gagal konek DB")

def insert_datasensor(payload):
    del payload["ultrasonicatas"]
    del payload["ultrasonicbawah"]
    payload.update({'createdAt':int(time.time())})
    try:  
        sql = 'INSERT INTO DataSensor (punggung, duduk, createdAt) VALUES (:punggung, :duduk, :createdAt)'
        cursor = con.cursor().execute(sql, payload)
        con.commit()
        print("succes insert data dengan parameter => " + str(payload))
    except Exception as e:
        print("ERROR insert => " + str(e))

def distance1():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER1, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER1, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO1) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO1) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance

def distance2():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER2, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER2, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO2) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO2) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance

def build_payload(variable_1, variable_2, variable_3, variable_4):
    global wabung #waktu bungkuk
    global waduk #waktu duduk
    global wari #waktu berdiri
    value_1 = round(distance1(),1) #mengambil data dari sensor
    value_2 = round(distance2(),1)
    payload = {variable_1: value_1,
                variable_2: value_2}
    if value_1 < 30 and value_2 < 30:   #untuk mendeteksi apakah pengguna duduk
        waduk +=1
        payload.update({variable_4:1})
        if abs(value_1 - value_2) > 5:
            wabung+=1
            payload.update({variable_3:0})  #bungkuk
            return payload
        else :
            wabung=0
            payload.update({variable_3:1}) #tegap
            return payload
    elif wari > 900 :
        waduk,wabung = 0,0
        payload.update({variable_3:2,variable_4:0})
        return payload
    else:
        wabung = 0
        payload.update({variable_3:2,variable_4:0})
        return payload

    


def post_request(payload):
    # Creates the headers for the HTTP requests
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
    headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}

    # Makes the HTTP requests
    status = 400
    attempts = 0
    while status >= 400 and attempts <= 5:
        GPIO.output(LEDG, GPIO.HIGH)
        req = requests.post(url=url, headers=headers, json=payload)
        print(req.json())
        status = req.status_code
        attempts += 1
        GPIO.output(LEDG, GPIO.LOW)
        time.sleep(1)

    # Processes results
    print(req.status_code, req.json())
    if status >= 400:
        print("[ERROR] Could not send data after 5 attempts, please check \
            your token credentials and internet connection")
        return False

    print("[INFO] request made properly, your device is updated")
    return True


def main():
    payload = build_payload(
        VARIABLE_LABEL_1, VARIABLE_LABEL_2, VARIABLE_LABEL_3, VARIABLE_LABEL_4) # payload merupakan dict
    print("[INFO] Attemping to send data")
    print("[INFO] send payload to ubidots => " + str(payload))
    post_request(payload)   #kirim data ke ubidots
    #insert_datasensor(payload)
    #simpan_data(payload)    #simpan data ke db
    print("[INFO] finished")


if __name__ == '__main__':
    global wabung
    global waduk
    global wari
    wabung,waduk,wari = 0,0,0
    GPIO.output(LEDR,GPIO.HIGH)
    try:
        while True:
            main()
            if wabung>5:
                GPIO.output(buzzer,GPIO.HIGH)
            else:
                GPIO.output(buzzer,GPIO.LOW)
            time.sleep(1)
            print("\n")
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\n","dihentikan pengguna")
