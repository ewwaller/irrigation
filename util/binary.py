#! /usr/bin/env python3

import RPi.GPIO as GPIO
import time

delay = 0.1

GPIO.setmode(GPIO.BCM)
for i in range(8):
    GPIO.setup(i,GPIO.OUT)
while True:
    for i in range(256):
        for j in range(8):
            GPIO.output(j,((i>>j)&1)^1)
            print(((i>>j)&1) ,end='')
        time.sleep (delay)
        print()    

    

        

