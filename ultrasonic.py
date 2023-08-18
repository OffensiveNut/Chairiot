import time
import requests
import math
import random
import RPi.GPIO as GPIO
import threading

TOKEN = "BBFF-9DdXBU8MAziwsslZNTcYXTSTuauWCo"
DEVICE_LABEL = "chairiot"
VARIABLE_LABEL_1 = "ultrasonicatas"
VARIABLE_LABEL_2 = "ultrasonicbawah"
VARIABLE_LABEL_3 = "punggung"

GPIO.setmode(GPIO.BCM)

#set GPIO Pins
GPIO_TRIGGER1 = 18
GPIO_ECHO1 = 15
GPIO_TRIGGER2 = 22
GPIO_ECHO2 = 23
LEDR = 25
LEDG = 8
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER1, GPIO.OUT)
GPIO.setup(GPIO_ECHO1, GPIO.IN)
GPIO.setup(GPIO_TRIGGER2, GPIO.OUT)
GPIO.setup(GPIO_ECHO2, GPIO.IN)
GPIO.setup(LEDG, GPIO.OUT)
GPIO.setup(LEDR, GPIO.OUT)

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

def build_payload(variable_1, variable_2, variable_3):
    value_1 = round(distance1(),1) #mengambil data dari sensor
    value_2 = round(distance2(),1)
    if abs(value_1 - value_2 > 5): # if abs(value_1 - value_2) > 5:
        value_3 = 0   #value_3 = "bungkuk"
        payload = {variable_1: value_1,
                variable_2: value_2,
                variable_3: value_3}  #dictionary / JSON
        return payload
    else :
        value_3 = 1 #value_3 = "tegap"
        payload = {variable_1: value_1,
                variable_2: value_2,
                variable_3: value_3} 
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
        VARIABLE_LABEL_1, VARIABLE_LABEL_2, VARIABLE_LABEL_3)

    print("[INFO] Attemping to send data")
    print("[INFO] send payload to ubidots => " + str(payload))
    post_request(payload)   #kirim data ke ubidots
    print("[INFO] finished")


if __name__ == '__main__':
    while (True):
        main()
        time.sleep(1)
        print("\n")
