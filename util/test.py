#! /usr/bin/env python3

import RPi.GPIO as GPIO
import time

delay = .05

GPIO.setmode(GPIO.BCM)
for i in range(16):
    GPIO.setup(i,GPIO.OUT)
    GPIO.output(i,1)
while True:
    for i in range(16):
        print(i)
        GPIO.output(i,0)
        time.sleep (delay)
        GPIO.output(i,1)

        

