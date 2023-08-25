import time
import requests
import math
import random
import RPi.GPIO as GPIO
from datetime import datetime
import sqlite3
from ubidots import ApiClient
import threading
import schedule

DB_NAME = "dataSensor.db"
con = False

#Telegram
TOKENTELE = '5936063047:AAEegGclhoRYVF2AnKsnWlAn-g0uwgLvT6o'
chat_id = 672670660   #chat id pengguna

#Ubidots
TOKEN = "BBFF-SPIdNe2oiBj1aHhXaA4App7zHsXczY"
api = ApiClient(token="BBFF-MOVEvayAV5PhVSZmkJiIMXrcJSs5uT")
DEVICE_LABEL = "chairiot"
VARIABLE_LABEL_1 = "ultrasonicatas"
VARIABLE_LABEL_2 = "ultrasonicbawah"
VARIABLE_LABEL_3 = "punggung"
VARIABLE_LABEL_4 = "duduk"
new_variable = api.get_variable('64e414d593129e000eeb6569')
last_value = new_variable.get_values(1)

GPIO.setmode(GPIO.BCM)

#set GPIO Pins
GPIO_TRIGGER1 = 17
GPIO_ECHO1 = 15
GPIO_TRIGGER2 = 24
GPIO_ECHO2 = 22
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


#Sqlite
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

def start_distance1():
    t1 = threading.Thread(target=distance1)
    t1.start()

def distance1():
    global distance1_glb
    while True:
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
        distance1_glb = round((TimeElapsed * 34300) / 2,1)
        time.sleep(1)
 
def start_distance2():
    t1 = threading.Thread(target=distance2)
    t1.start()

def distance2():
    global distance2_glb
    while True:
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
        distance2_glb = round((TimeElapsed * 34300) / 2,1)
        time.sleep(1)

def build_payload(variable_1, variable_2, variable_3, variable_4):
    global wabung
    global waduk
    global distance1_glb
    global distance2_glb

    value_1 = distance1_glb
    value_2 = distance2_glb #mengambil data dari sensor
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
    else:
        wabung = 0
        payload.update({variable_3:2,variable_4:0})
        return payload

def start_kondisi():
    t1 = threading.Thread(target=kondisi)
    t1.start()

def kondisi():
    global waduk, wabung
    time.sleep(3)
    while True:
        if waduk > 3600:
            GPIO.output(buzzer,GPIO.HIGH)
            kirimPesan("Kamu telah duduk terlalu lama, berdirilah dan gerakan badanmu")
            time.sleep(1)
            GPIO.output(buzzer,GPIO.LOW)
            waduk = 0
        else:
            pass
        if wabung>5:
            GPIO.output(buzzer,GPIO.HIGH)
        else:
            GPIO.output(buzzer,GPIO.LOW)
        time.sleep(1)
    


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

def kirimPesan(text):
   chat_id = str(int(last_value[0]['value']))
   url_req = "https://api.telegram.org/bot" + TOKENTELE + "/sendMessage" + "?chat_id=" + chat_id + "&text=" + text 
   results = requests.get(url_req)
   print(results.json())

def kirimReport():
    pass

def main():
    payload = build_payload(
        VARIABLE_LABEL_1, VARIABLE_LABEL_2, VARIABLE_LABEL_3, VARIABLE_LABEL_4) # payload merupakan dict
    print("[INFO] Attemping to send data")
    print("[INFO] send payload to ubidots => \n" + str(payload),"\n")
    post_request(payload)   #kirim data ke ubidots
    insert_datasensor(payload) #simpan data ke db
    print("[INFO] finished")

schedule.every().day.at("09:05:00").do(kirimReport)

def start_jadwal():
    t1 = threading.Thread(target=jadwal)
    t1.start()
def jadwal():
    schedule.run_pending()
    time.sleep(1)


if __name__ == '__main__':
    global wabung,waduk
    wabung,waduk = 0,0
    try:
        start_distance1()
        time.sleep(0.5)
        start_distance2()
        start_kondisi()
        start_jadwal()
        GPIO.output(LEDR,GPIO.HIGH)
        try:
            while True:
                main()
                print("waktu bungkuk:",wabung,'\n'+'waktu duduk:',waduk)
                #print(distance2_glb,'CM\n')
                time.sleep(1)
                print("\n")
        except KeyboardInterrupt:
            GPIO.cleanup()
            print("\n","dihentikan pengguna")
    except Exception as e:
        GPIO.cleanup()
        print(e)