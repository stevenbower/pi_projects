#!/usr/bin/env python
import RPi.GPIO as GPIO
import matrix_keypad
import time
import threading
import random

led_configs = [
    {
        "sdi": 11,
        "rclk": 12,
        "srclk": 13,
        "count": 8,
    },
    {
        "sdi": 16,
        "rclk": 18,
        "srclk": 15,
        "count": 4,
    },

]

#SDI   = 11
#RCLK  = 12
#SRCLK = 13

KEYPAD_ROWS = [29, 31, 33, 35]
KEYPAD_COLS = [32, 36, 38, 40]

def print_msg():
    print 'Program is running...'
    print 'Please press Ctrl+C to end the program...'

class LedManager(object):
    def __init__(self, configs, mapping):
        self.configs = configs
        self.mapping = mapping
        self._thread = None
        self._running = False
        self.count = sum([x["count"] for x in self.configs])
        self.drivers = None

    def setup(self):
        self.drivers = []
        for cfg in self.configs: 
            self.drivers.append(LedDriver(cfg["sdi"], cfg["rclk"], cfg["srclk"], cfg["count"]))

    def allOff(self, flush=True):
        for driver in self.drivers:
            driver.allOff(flush=flush)

    def allOn(self, flush=True):
        for driver in self.drivers:
            driver.allOn(flush=flush)

    def _getMappedDriverOffset(self, bulbIdx):
        return self._getDriverOffset(self.mapping[bulbIdx])

    def _getDriverOffset(self, bulbIdx):
        print "IDX: ", bulbIdx
        for driver in self.drivers:
            print "DRIVER: ", driver.count, bulbIdx
            if bulbIdx >= driver.count:
                print "XXX"
                bulbIdx = bulbIdx - driver.count
            else:
                return driver, bulbIdx

    def on(self, bulbIdx, flush=True):
        driver, idx = self._getMappedDriverOffset(bulbIdx)
        print bulbIdx, idx
        driver.on(idx, flush=flush)

    def off(self, bulbIdx, flush=True):
        driver, idx = self._getMappedDriverOffset(bulbIdx)
        print bulbIdx, idx
        driver.off(idx, flush=flush)

    def flush(self):
        for driver in self.drivers:
            driver.flush()

    def running(self):
        return self._running

    def stop(self):
        if self._thread != None:
            self._running = False
            self._thread.join()

    def start(self, fn, *args):
        self._running = True
        a = [self.running]
        a.extend(args)

        self._thread = threading.Thread(target=fn, args=a, name="led-effect-loop")
        self._thread.start()

class LedDriver(object):

    def __init__(self, sdi, rclk, srclk, count=8):
        self._thread = None
        self._state = 0x00
        self._running = False
        self.count = count
        self.sdi = sdi
        self.rclk = rclk
        self.srclk = srclk

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

    def start(self, fn, *args):
        self._running = True
        a = [self.running]
        a.extend(args)

        self._thread = threading.Thread(target=fn, args=a, name="led-effect-loop")
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
            mapping = [
                2,
                11,
                7,
                8,
                9,
                10,
                0,
                1,
                3,
                4,
                5,
                6,
            ]
            self.leds = LedManager(led_configs, mapping)
            self.leds.setup()

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

    def effect_starry_night(self, checkFn, delay):
        while checkFn():
            idx = random.randint(0, self.leds.count-1) 
            state = random.randint(0, 1) 
            if state == 1:
                self.leds.on(idx)
            else:
                self.leds.off(idx)
            time.sleep(delay)

    def effect_fader(self, checkFn):
        while checkFn():
            for x in range(0, self.leds.count):
                bulbs = [x]
                if x+1 < self.leds.count: bulbs.append(x+1)
                if x+2 < self.leds.count: bulbs.append(x+2)
                for f in range(0, len(bulbs)):
                    self.leds.allOff(flush=False)
                    for i in range(0, len(bulbs)):
                        if i < f:
                            self.leds.off(bulbs[i], flush=False)
                        else:
                            self.leds.on(bulbs[i], flush=False)
                        self.leds.flush()
                    time.sleep(0.00001)
            for x in range(self.leds.count-1, -1, -1):
                bulbs = []
                if x-2 > 0: bulbs.append(x-2)
                if x-1 > 0: bulbs.append(x-1)
                bulbs.append(x)
                for f in range(0, len(bulbs)):
                    self.leds.allOff(flush=False)
                    for i in range(0, len(bulbs)):
                        if i < f:
                            self.leds.off(bulbs[i], flush=False)
                        else:
                            self.leds.on(bulbs[i], flush=False)
                        self.leds.flush()
                    time.sleep(0.00001)

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
            self.leds.start(self.effect_starry_night, 0.1)
        elif key == "D":
            self.leds.start(self.effect_fader)
        #elif key == 0:
            #self.leds.start(self.effect_starry_night, 0.001)
        #elif key == 1:
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
        
