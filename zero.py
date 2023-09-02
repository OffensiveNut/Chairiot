import time
import requests
import math
import random
from datetime import datetime, timedelta
import sqlite3
import threading
import schedule
from gpiozero import LED,Buzzer,DistanceSensor

DB_NAME = "dataSensor.db"
con = False

#Telegram
TOKENTELE = '6341354896:AAEWv80n9mSi1Jzw9il8psnrjbqF41qXuXk'

#Ubidots
TOKEN = "BBFF-SPIdNe2oiBj1aHhXaA4App7zHsXczY"
DEVICE_LABEL = "chairiot"
VARIABLE_LABEL_1 = "idtelegram"
VARIABLE_LABEL_2 = "mode"
VARIABLE_LABEL_3 = "punggung"
VARIABLE_LABEL_4 = "duduk"

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

def get_last_last_7_days_data():
    try:
        now = get_epoch_time_delta(7)
        time_delta = get_epoch_time_delta(14) # 7 hari terkahir
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
def start_payloadgen():
    t1=threading.Thread(target=payloadgen)
    t1.start()

def payloadgen():
    global payload
    while True:
        payload = build_payload()
        time.sleep(1)

def build_payload(variable_3=VARIABLE_LABEL_3, variable_4=VARIABLE_LABEL_4):
    global wabung
    global waduk
    value_1 = round(sensor1.distance*100,1)
    value_2 = round(sensor2.distance*100,1)
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
    while True:
        mode = get_request(VARIABLE_LABEL_2)
        while mode >1:
            if waduk > 1800:
                buzzer.on()
                kirimPesan("Kamu telah duduk terlalu lama, berdirilah dan gerakan badanmu🏃🏃🏃")
                time.sleep(3)
                buzzer.off()
                waduk = 0
            else:
                pass
            if wabung>5:
                buzzer.on()
            else:
                buzzer.off()
            mode = get_request(VARIABLE_LABEL_2)
            time.sleep(1)
        else: pass
        while mode ==1:
            if waduk > 3600:
                buzzer.on()
                kirimPesan("Kamu telah duduk terlalu lama, berdirilah dan gerakan badanmu🏃🏃🏃")
                time.sleep(0.5)
                buzzer.off()
                waduk = 0
            else:
                pass
            if wabung>5:
                buzzer.on()
                time.sleep(3)
                buzzer.off()
            else:
                buzzer.off()
            mode = get_request(VARIABLE_LABEL_2)
            time.sleep(1)
        else: 
            buzzer.off()
            time.sleep(1)
    
def get_request(variable):
    url = 'https://industrial.api.ubidots.com/api/v1.6/devices/{}/{}/lv'.format(DEVICE_LABEL,variable)
    headers = {"X-Auth-Token": TOKEN}
    status = 400
    attempts = 0
    while status >= 400 and attempts <= 5:
        req = requests.get(url=url, headers=headers)
        print(req,req.json())
        status = req.status_code
        attempts += 1
        time.sleep(1)
    return int(req.json())

def start_post_request(payload):
    t1 = threading.Thread(target= post_request, args=(payload,))
    t1.start()

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

def start_kirimPesan(text):
    t1 = threading.Thread(target= kirimPesan, args=(text,))
    t1.start()

def kirimPesan(text):
   chat_id = str(get_request(VARIABLE_LABEL_1))
   url_req = "https://api.telegram.org/bot" + TOKENTELE + "/sendMessage" + "?chat_id=" + chat_id + "&text=" + text 
   results = requests.get(url_req)
   print(results.json())

def kirimReport():
    if get_last_7_days_data:
        if get_last_last_7_days_data:

            detik,avgPunggung = get_last_7_days_data()
            print(detik,avgPunggung)
            jam, detik = divmod(detik, 60 ** 2)
            menit, detik = divmod(detik, 60)
            waktuDuduk = '{:02} Jam, {:02} Menit, {:02} Detik.'.format(jam, menit, detik)

            detik2,avgPunggung2 = get_last_last_7_days_data()
            if avgPunggung>avgPunggung2:
                ratio = 100-int((avgPunggung2/avgPunggung)*100)
                if avgPunggung>0.8:
                    kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu SANGAT BAGUS!, Pertahankan!🔥🔥🔥\n\nSikap duduk kamu lebih baik {}% dari minggu lalu! MANTAP!🔥🔥🔥".format(ratio))
                elif avgPunggung>0.5:
                    kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu sudah CUKUP BAGUS, Tingkatkan!👍\n\nSikap duduk kamu lebih baik {}% dari minggu lalu! NICE!🔥🔥🔥".format(ratio))
                else :
                    kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu CUKUP BURUK, Perbaikilah!💪\n\nSikap duduk kamu lebih baik {}% dari minggu lalu!".format(ratio))
            else:
                ratio = 100-int((avgPunggung/avgPunggung2)*100)
                if avgPunggung>0.8:
                    kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu SANGAT BAGUS!, Pertahankan!🔥🔥🔥\n\nSikap duduk kamu lebih buruk {}% dari minggu lalu! Tingkatkan!".format(ratio))
                elif avgPunggung>0.5:
                    kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu sudah CUKUP BAGUS, Tingkatkan!👍 \n\nSikap duduk kamu lebih buruk {}% dari minggu lalu! Tingkatkan!".format(ratio))
                else :
                    kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu CUKUP BURUK, Perbaikilah!💪\n\nSikap duduk kamu lebih buruk {}% dari minggu lalu! Tingkatkan!".format(ratio))
        else:
            detik,avgPunggung = get_last_7_days_data()
            print(detik,avgPunggung)
            jam, detik = divmod(detik, 60 ** 2)
            menit, detik = divmod(detik, 60)
            waktuDuduk = '{:02} Jam, {:02} Menit, {:02} Detik.'.format(jam, menit, detik)
            if avgPunggung>0.8:
                kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu SANGAT BAGUS!, Pertahankan!🔥🔥🔥")
            elif avgPunggung>0.5:
                kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu sudah CUKUP BAGUS, Tingkatkan!👍🔥🔥🔥💪💪💪")
            else :
                kirimPesan("Minggu ini kamu telah duduk selama "+waktuDuduk+"⌛\nPosisi duduk kamu CUKUP BURUK, Perbaikilah!💪")
    else:
        pass

def main():
    global payload
    insert_datasensor(payload)
    print("[INFO] Attemping to send data")
    print("[INFO] send payload to ubidots => \n" + str(payload),"\n")
    #post_request(payload)   #kirim data ke ubidots
    start_post_request(payload)
    schedule.run_pending()
    print("[INFO] finished")


if __name__ == '__main__':
    try:
        global wabung,waduk
        global switch
        wabung,waduk = 0,0
        start_payloadgen()
        schedule.every().monday.at("12:00:00").do(kirimReport)
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