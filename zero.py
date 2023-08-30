import time
import requests
import math
import random
from datetime import datetime, timedelta
import sqlite3
from ubidots import ApiClient
import threading
import schedule
from gpiozero import LED,Buzzer,DistanceSensor

DB_NAME = "dataSensor.db"
con = False

#Telegram
TOKENTELE = '6341354896:AAEWv80n9mSi1Jzw9il8psnrjbqF41qXuXk'

#Ubidots
TOKEN = "BBFF-SPIdNe2oiBj1aHhXaA4App7zHsXczY"
api = ApiClient(token="BBFF-MOVEvayAV5PhVSZmkJiIMXrcJSs5uT")
DEVICE_LABEL = "chairiot"
VARIABLE_LABEL_3 = "punggung"
VARIABLE_LABEL_4 = "duduk"
new_variable = api.get_variable('64e414d593129e000eeb6569')
last_value = new_variable.get_values(1)

sensor1 = DistanceSensor(echo=19, trigger=26)
sensor2 = DistanceSensor(echo=20, trigger=16)
LEDR = LED(2)
LEDG = LED(3)
buzzer = Buzzer(4)

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
    
    
def get_epoch_time_delta(delta_days):
    current_datetime = datetime.now()
    time_delta = current_datetime - timedelta(days=delta_days)
    time_delta_epoch = int(time_delta.timestamp())
    return time_delta_epoch
    

def get_last_7_days_data():
    try:
        now = int(time.time())
        time_delta = get_epoch_time_delta(7) # 7 hari terkahir
        param= {
            'start_time' : now,
            'end_time' : time_delta
        }
        
        sql = 'SELECT * FROM DataSensor WHERE createdAt BETWEEN :start_time AND :end_time'
        cursor = con.cursor().execute(sql,param)
        result = cursor.fetchall()
        return result
    except Exception as e:
        print("[ERROR] get 7 days data")
        return False

def insert_datasensor(payload):
    payload.update({'createdAt':int(time.time())})
    try:  
        sql = 'INSERT INTO DataSensor (punggung, duduk, createdAt) VALUES (:punggung, :duduk, :createdAt)'
        cursor = con.cursor().execute(sql, payload)
        con.commit()
        print("succes insert data dengan parameter => " + str(payload))
    except Exception as e:
        print("ERROR insert => " + str(e))

def get_epoch_time_delta(delta_days):
    current_datetime = datetime.now()
    time_delta = current_datetime - timedelta(days=delta_days)
    time_delta_epoch = int(time_delta.timestamp())
    return time_delta_epoch


def get_last_7_days_data():
    try:
        now = int(time.time())
        time_delta = get_epoch_time_delta(7) # 7 hari terkahir
        param= {
            'start_time' : time_delta,
            'end_time' : now
        }

        sql = 'SELECT * FROM DataSensor WHERE createdAt BETWEEN :start_time AND :end_time'
        cursor = con.cursor().execute(sql,param)
        result = cursor.fetchall()

        punggung = [a['punggung'] for a in result]
        while 2 in punggung : punggung.remove(2)
        avgPunggung =sum(punggung)/len(punggung)
        
        duduk = [a['duduk'] for a in result]
        sumDuduk =sum(duduk)

        return sumDuduk,avgPunggung
    except Exception as e:
        print("[ERROR] get 7 days data\n",e)
        return False

def build_payload(variable_3, variable_4):
    global wabung
    global waduk

    value_1 = round(sensor1.distance*100,1)
    value_2 = round(sensor2.distance*100,1) #mengambil data dari sensor
    print(value_1,'\n',value_2)
    if value_1 < 30 and value_2 < 30:   #untuk mendeteksi apakah pengguna duduk
        waduk +=1
        payload={variable_4:1}
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
        payload={variable_3:2,variable_4:0}
        return payload

def start_kondisi():
    t1 = threading.Thread(target=kondisi)
    t1.start()

def kondisi():
    global waduk, wabung
    time.sleep(3)
    while True:
        if waduk > 3600:
            buzzer.on()
            kirimPesan("Kamu telah duduk terlalu lama, berdirilah dan gerakan badanmu")
            time.sleep(1)
            buzzer.off()
            waduk = 0
        else:
            pass
        if wabung>5:
            buzzer.on()
        else:
            buzzer.off()
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
        LEDG.on()
        req = requests.post(url=url, headers=headers, json=payload)
        print(req.json())
        status = req.status_code
        attempts += 1
        LEDG.off()
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
    if get_last_7_days_data:
        detik,avgPunggung = get_last_7_days_data()
        print(detik,avgPunggung)
        jam, detik = divmod(detik, 60 ** 2)
        menit, detik = divmod(detik, 60)
        waktuDuduk = '{:02} Jam, {:02} Menit, {:02} Detik.'.format(jam, menit, detik)
        if avgPunggung>0.8:
            kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"\nDan posisi duduk kamu SANGAT BAGUS!, Pertahankan!🔥🔥🔥")
        elif avgPunggung>0.5:
            kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"\nDan posisi duduk kamu sudah CUKUP BAGUS, Tingkatkan!👍🔥🔥🔥💪💪💪")
        else :
            kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"\nDan posisi duduk kamu CUKUP BURUK, Perbaikilah!💪")
    else:
        pass

def main():
    payload = build_payload( VARIABLE_LABEL_3, VARIABLE_LABEL_4) # payload merupakan dict
    print("[INFO] Attemping to send data")
    print("[INFO] send payload to ubidots => \n" + str(payload),"\n")
    post_request(payload)   #kirim data ke ubidots
    insert_datasensor(payload) #simpan data ke db
    schedule.run_pending()
    print("[INFO] finished")



if __name__ == '__main__':
    global wabung,waduk
    wabung,waduk = 0,0
    try:
        schedule.every().monday.at("14:01:00").do(kirimReport)
        start_kondisi()
        LEDR.on()
        print('7 hari terakhir',get_last_7_days_data())
        print(schedule.get_jobs())
        while True:
            main()
            print("waktu bungkuk:",wabung,'\n'+'waktu duduk:',waduk)
            time.sleep(1)
            print("\n")
    except Exception as e:
        print(e)