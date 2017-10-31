#!/usr/bin/python
 
import RPi.GPIO as GPIO
import time
import threading

class keypad():
    def __init__(self, columnCount=3, rows=None, cols=None):
        self._running = False
        self._thread = None
        self._lastKey = None

        # CONSTANTS 
        if columnCount is 3:
            self.KEYPAD = [
                [1,2,3],
                [4,5,6],
                [7,8,9],
                ["*",0,"#"]
            ]

            self.ROW         = [18,23,24,25]
            self.COLUMN      = [4,17,22]

        elif columnCount is 4:
            self.KEYPAD = [
                [1,2,3,"A"],
                [4,5,6,"B"],
                [7,8,9,"C"],
                ["*",0,"#","D"]
            ]

            self.ROW         = [18,23,24,25]
            self.COLUMN      = [4,17,22,21]
        else:
            return

        if rows:
            self.ROW = rows

        if cols:
            self.COLUMN = cols

    def watch(self, downFn=None, pressFn=None):
        self._thread = threading.Thread(target=self._watch, kwargs={"pressFn":pressFn, "downFn":downFn}, name="Keypad")
        self._thread.start()

    def _watch(self, downFn=None, pressFn=None):
        self._running = True
        while self._running:
            v = self.getKey()
            if v != self._lastKey:
                if v == None:
                    if pressFn:
                        pressFn(self._lastKey)
                else:
                    if downFn:
                        downFn(v)
                self._lastKey = v
            else:
                time.sleep(0.01)

    def stop(self):
        self._running = False
        self._thread.join()

    def getKey(self):
         
        # Set all columns as output low
        for j in range(len(self.COLUMN)):
            GPIO.setup(self.COLUMN[j], GPIO.OUT)
            GPIO.output(self.COLUMN[j], GPIO.LOW)
         
        # Set all rows as input
        for i in range(len(self.ROW)):
            GPIO.setup(self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
         
        # Scan rows for pushed key/button
        # A valid key press should set "rowVal"  between 0 and 3.
        rowVal = -1
        for i in range(len(self.ROW)):
            tmpRead = GPIO.input(self.ROW[i])
            if tmpRead == 0:
                rowVal = i
                 
        # if rowVal is not 0 thru 3 then no button was pressed and we can exit
        if rowVal <0 or rowVal >3:
            self.exit()
            return
         
        # Convert columns to input
        for j in range(len(self.COLUMN)):
                GPIO.setup(self.COLUMN[j], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
         
        # Switch the i-th row found from scan to output
        GPIO.setup(self.ROW[rowVal], GPIO.OUT)
        GPIO.output(self.ROW[rowVal], GPIO.HIGH)
 
        # Scan columns for still-pushed key/button
        # A valid key press should set "colVal"  between 0 and 2.
        colVal = -1
        for j in range(len(self.COLUMN)):
            tmpRead = GPIO.input(self.COLUMN[j])
            if tmpRead == 1:
                colVal=j
                 
        # if colVal is not 0 thru 2 then no button was pressed and we can exit
        if colVal <0 or colVal >3:
            self.exit()
            return
 
        # Return the value of the key pressed
        self.exit()
        return self.KEYPAD[rowVal][colVal]
         
    def exit(self):
        # Reinitialize all rows and columns as input at exit
        for i in range(len(self.ROW)):
                GPIO.setup(self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP) 
        for j in range(len(self.COLUMN)):
                GPIO.setup(self.COLUMN[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)
         
if __name__ == '__main__':
    # Initialize the keypad class
    kp = keypad()
     
    # Loop while waiting for a keypress
    digit = None
    while digit == None:
        digit = kp.getKey()
     
    # Print the result
    print digit
