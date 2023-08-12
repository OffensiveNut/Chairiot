import RPi.GPIO as GPIO
import time
from paho.mqtt import client as mqtt_client
import random
import threading


broker = 'mqtt-dashboard.com'
port = 1883
topic1 = "SIC-Hyperion-US1"
topic2 = "SIC-Hyperion-US2"
# Generate a Client ID with the publish prefix.
client_id = f'publish-{random.randint(0, 1000)}' 
#GPIO Mode (BOARD / BCM)
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
 
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client):
    while True:
        'status = result[0]'
        GPIO.output(LEDG, GPIO.HIGH)
        dist1 = round(distance1(),1)
        dist2 = round(distance2(),1)
        result = client.publish(topic1, dist1)
        result2 = client.publish(topic2, dist2)

        print ("sensor 1 = %.1f cm" % dist1,"\nsensor 2 = %.1f cm" % dist2)
        GPIO.output(LEDG, GPIO.LOW)
        time.sleep(0.5)

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

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()

if __name__ == '__main__':
    print('sukses')
    GPIO.output(LEDR, GPIO.HIGH)
    try:
        run()
 
        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("\n Dihentikan Oleh Pengguna")
        GPIO.cleanup()