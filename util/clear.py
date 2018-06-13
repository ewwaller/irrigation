#! /usr/bin/env python3

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
for i in range(16):
    GPIO.setup(i,GPIO.OUT)
for i in range(16):
    GPIO.output(i,1)

    

        

