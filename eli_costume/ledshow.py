#!/usr/bin/env python
import RPi.GPIO as GPIO
import matrix_keypad
import time
import threading
import random

SDI   = 11
RCLK  = 12
SRCLK = 13

KEYPAD_ROWS = [29, 31, 33, 35]
KEYPAD_COLS = [32, 36, 38, 40]

def print_msg():
    print 'Program is running...'
    print 'Please press Ctrl+C to end the program...'

def text_loop():
    state = 0x00
    sleeptime = 0.05     # Change speed, lower value, faster speed
    #num = int(raw_input("Enter your name: ").strip())
    #l = LED0[num]
    #if cur > -1
    #hc595_in(WhichLeds[i])
    #hc595_out()
    while True:
        hc595_in(0)
        hc595_out()
        for i in range(0, 6):
            state = 0
            state = setState(state, i, True)
            #if i > 1:
                #state = setState(state, i-2, False)
            #state = state | (0x01 << i)
            hc595_in(state)
            hc595_out()
            time.sleep(sleeptime)

class LedDriver(object):

    def __init__(self, sdi, rclk, srclk, count=8):
        self.count = count
        self._state = 0x00
        self.sdi = sdi
        self.rclk = rclk
        self.srclk = srclk
        self._running = False
        GPIO.setup(self.sdi, GPIO.OUT)
        GPIO.setup(self.rclk, GPIO.OUT)
        GPIO.setup(self.srclk, GPIO.OUT)
        GPIO.output(self.sdi, GPIO.LOW)
        GPIO.output(self.rclk, GPIO.LOW)
        GPIO.output(self.srclk, GPIO.LOW)

    def hc595_in(self, dat):
        for bit in range(0, 8): 
            GPIO.output(self.sdi, 0x80 & (dat << bit))
            GPIO.output(self.srclk, GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(self.srclk, GPIO.LOW)

    def hc595_out(self):
        GPIO.output(self.rclk, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(self.rclk, GPIO.LOW)

    def setState(self, state, flush=True):
        self._state = state
        if flush:
            self.flush()

    def allOff(self, flush=True):
        self.setState(0x00,flush=flush)

    def allOn(self, flush=True):
        self.setState(0xFF,flush=flush)

    def on(self, bulbIdx, flush=True):
        self.setState(self._state | (0x01 << bulbIdx), flush=flush)

    def off(self, bulbIdx, flush=True):
        self.setState(self._state & ~(0x01 << bulbIdx), flush=flush)

    def flush(self):
        self.hc595_in(self._state)
        self.hc595_out()

    def running(self):
        return self._running

    def stop(self):
        if self._thread != None:
            self._running = False
            self._thread.join()

    def start(self, fn):
        self._running = True
        self._thread = threading.Thread(target=fn, args=[self.running], name="led-program-%d")
        self._thread.start()

class Costume(object):

    def __init__(self):
        self.keypad = None
        self.kpThread = None
        self.leds = None

    def setup(self):
        if self.keypad == None and self.leds == None:
            GPIO.setmode(GPIO.BOARD)

        if self.keypad == None:
            self.keypad = matrix_keypad.keypad(columnCount=4, rows=KEYPAD_ROWS, cols=KEYPAD_COLS)
            self.keypad.watch(pressFn=self.keypress)

        if self.leds == None:
            self.leds = LedDriver(SDI, RCLK, SRCLK, count=5)

    def effect_led_cycle(self, checkFn):
        while checkFn():
            for i in range(0, self.leds.count):
                self.leds.allOff(flush=False)
                self.leds.on(i)
                time.sleep(0.05)

    def effect_night_rider(self, checkFn):
        while checkFn():
            for i in range(0, self.leds.count):
                self.leds.allOff(flush=False)
                self.leds.on(i)
                time.sleep(0.1)

            for i in range(self.leds.count-1, -1, -1):
                self.leds.allOff(flush=False)
                self.leds.on(i)
                time.sleep(0.1)

    def effect_starry_night(self, checkFn):
        while checkFn():
            idx = random.randint(0, self.leds.count-1) 
            state = random.randint(0, 1) 
            if state == 1:
                self.leds.on(idx)
            else:
                self.leds.off(idx)
            time.sleep(0.1)

    def keypress(self, key):
        if self.leds.running():
            self.leds.stop()

        print key
        if key == "*":
            self.leds.allOff()
        elif key == "#":
            self.leds.allOn()
        elif key == "A":
            self.leds.start(self.effect_led_cycle)
        elif key == "B":
            self.leds.start(self.effect_night_rider)
        elif key == "C":
            self.leds.start(self.effect_starry_night)
        elif key == "D":
            pass
        else:
            self.leds.on(int(key)-1)

    def __enter__(self):
        self.setup()

    def __exit__(self, t, val, tb):
        self.keypad.stop()
        self.leds.stop()
        GPIO.cleanup()

if __name__ == '__main__': # Program starting from here
    random.seed(23)
    print_msg()
    with Costume() as costume:
        while True:
            time.sleep(60)
        
