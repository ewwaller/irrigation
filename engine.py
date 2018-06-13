"""
MIT License

Copyright (c) 2018 Eric Waller

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import threading
import time
import copy
import simplejson as json
import log
import io

dwell = 1
MaxChannels=16

daynames = ("Monday","Tuesday","Wednesday","Thursday",
            "Friday","Saturday","Sunday")

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

# Try to import the Raspberry Pi GPIO module. If it fails, assume this
# is a simulation
simulation=False
try:
    import RPi.GPIO as GPIO
except:
    # We are not on a Raspi, so run in simulator mode
    # build a pretend GPIO class that does nothing
    simulation=True
    class GPIO:
        BCM=None
        OUT=True
        def setmode(x):
            log.logger.warn("Running in simulator mode; setmode called")
        def setup(x,y):
            log.logger.warn("Running in simulator mode; configured GPIO %d to %d"%(x,y))
        def output(x,y):
            pass

class IrrigationEngine(threading.Thread):
    """ 
    This class provides the background process provides the real
    time control of the irrigation valves by comparing scheduled
    events to the current time and moving them to the queue.  This
    processing will only 

    When the system is running, the valve for the event at the top
    of the queue is opened and the remaining time decremented. When
    an event has no time left, it is dequeued and the next event
    processed.  When the system is not running, it will monitor the
    manual control inputs and will open the valves according to
    those controls.
    """

    def __init__ (self,theFile,channels):
        """
        Irrigation class constructor.  
        Set the run flag before the thread is started. Get the time
        and remember it as the thread needs the time for comparison
        during each pass 
        """
        log.logger.debug("Initalizing Irrigation Engine")
        threading.Thread.__init__(self)
        self.runFlag = True
        self.oldtime=time.localtime()
        self.theFile=theFile
        self.db=None
        self.queue=[]
        self.channels=channels
        self.manual=[False for i in range(self.channels)]
        self.lightsState={'state':False, 'changeCount':0}
        self.oldLightState=False
        self.lock=threading.Lock()
        if not self.readConfig():
            self.db={"schedule":[],
                "state":"running",
                "zoneNames":["Zone %d"%i for i in range(1,self.channels+1) ]
            }
        self.lastValve = -1
        self.clearGpio()

    def stop(self):
        """ 
        Stop the background thread.  
        This is done by clearing the run flag instance.  The next pass
        through the loop, the background thread will notice that the
        run flag is no longer set and will exit
        """
        self.runFlag = False
        log.logger.debug("Setting stop flag for irrigation engine")
    def writeConfig(self):
        """ Save the database to the configuration file"""
        try:
            with io.open(self.theFile, 'w', encoding='utf8') as outfile:
                str_ = json.dumps(self.db,
                                  indent=4, sort_keys=True,
                                  separators=(',', ': '), ensure_ascii=False)
                outfile.write(to_unicode(str_))
                return None
        except:
            log.logger.error("Unable to write configutation to file %s",self.theFile)
        return None
            
    def readConfig(self):
        """Read the configuration file to the database"""
        try:
            with open(self.theFile) as data_file:
                self.db = json.load(data_file)
                return data_file
        except:
            log.logger.error("Unable to read configuration to %s",self.theFile)
            return None
    def run(self):
        """ 
        Background thread to process the irrigation state machine.
        As long as the run flag remains set, stay in a loop processing
        the machine state.  When the flag clears, exit.  When the
        irrigation system is in the run state (not to be confused with
        the run flag; run state means irrigation is in auto mode), do
        the following: 
           Check as to whether it is time to turn on or off the yard
        lights. Debounce the light state to see if the state is
        actually changing, as the webapp can also turn the lights on
        or off at the whims of a user at a web browser.  Detect and
        log that when it happens.
           Every minute, check the schedule for events whoose time
        matches the current time, when found, and events to the queue
        for each valve that has an non-zero scheduled time.
           Every second, see if there is an event at the top of the
        queue , and if there is time remaining.  If there is an event,
        and the time remaing is zero, remove the event and move the
        queue up.  If  there is an active event, open the valve for
        that event. If there is no event, close all valves.

        When the irrigation is stopped, then set the valves according
        to the manual control settings.
        """
        log.logger.debug("Irrigation Engine is running")
        while self.runFlag:
            if self.db is not None:
                # We are sane, there is a database.  See if the lights
                # are as we left them.  If not, the web GUI changed them.
                if self.lightsState['state'] != self.oldLightState:
                    log.logger.info("Yard lights turned %s by web app"% ('on' if self.lightsState['state'] else 'off',))
                # Time to change the lights?  Are they in auto mode?
                self.time=time.localtime()
                if (self.oldtime[4] != self.time[4])\
                       and 'lights' in self.db \
                       and self.db['lights']['lightingAuto']:
                    newState=None
                    if self.db['lights']['lightOnTime'] ==  "%02d:%02d"%(self.time[3],self.time[4]) or \
                       self.db['lights']['lightOnTime2'] == "%02d:%02d"%(self.time[3],self.time[4]):
                           newState=True
                    if self.db['lights']['lightOffTime'] ==  "%02d:%02d"%(self.time[3],self.time[4]) or \
                       self.db['lights']['lightOffTime2'] == "%02d:%02d"%(self.time[3],self.time[4]):
                           newState=False
                    if newState is not None:
                        log.logger.info("Yard lights turned %s by timer"%("On" if newState else "Off", ))
                        self.lightsState['state']=newState
                        self.lightsState['changeCount']  += 1
                # Remember how we left rhe lights less they change
                # before we get back.
                self.oldLightState = self.lightsState['state']

                if self.getRunState()=="running":
                    # The sprinklers are in auto mode.  See if
                    # something is supposed to happen....  If so, add
                    # it to the queue.
                    # Any manual output state is now invalid
                    self.oldout = -1
                    if self.oldtime[4] != self.time[4]:
                        for i in self.getSchedule():
                            if (i['day'] == daynames[self.time[6]]) and (i['eventTime'] == "%02d:%02d"%(self.time[3],self.time[4])):
                                for x in range(1,self.channels +1):
                                    try:
                                        if int(i['valve%i'%(x,)])>0:
                                            self.queueAdd({'zone':x,'duration':[int(i['valve%i'%(x,)]),0]})
                                    except:
                                        pass
                    self.lock.acquire()
                    # If things are queued, is the first item done?
                    # If so, remove it and do the next event.
                    if len(self.queue) > 0:
                        if self.queue[0]['duration'][0] == 0 and self.queue[0]['duration'][1]==0:
                            log.logger.info("Finished event for valve %d",self.queue[0]["zone"])
                            self.queue.pop(0)
                            self.lastValve=-1
                    # If there is noting in the queue, clear all
                    # valves, but set the yard light control
                    # appropriately. 
                    if len(self.queue) ==0:
                        self.gpio(self.lightsState['state'] << 15)
                        self.lastValve=-1
                    # If there is an active event, open that valve,
                    # and set the light control as well.  Decrement
                    # the time remaining for the active event
                    else:
                        if self.lastValve != self.queue[0]["zone"]-1:
                            log.logger.info("Started event for valve %d for %d:%02d"
                                            ,self.queue[0]["zone"]
                                            ,self.queue[0]['duration'][0]
                                            ,self.queue[0]['duration'][1])
                            self.lastValve = self.queue[0]["zone"]-1
                        self.queue[0]['duration'][1] -= 1
                        if  self.queue[0]['duration'][1] < 0:
                             self.queue[0]['duration'][1] =59
                             self.queue[0]['duration'][0] -= 1
                        self.gpio((self.lightsState['state'] << 15) | (1 << self.queue[0]["zone"]-1))
                    self.lock.release()
                else: # not running 
                    # The sprinklers are in manual mode, so set the
                    # valves accordingly....  But also control the
                    # yard lights -- they may still be in auto mode.

                    # We may in the middle of watering a zone.  We
                    # will want to log when we restart it
                    self.lastValve = -1
                    
                    out = 0
                    for i in range(self.channels):
                        if self.manual[i]:
                            out |= (1 << i)
                    if self.oldout != out:
                        log.logger.info("Manual valve control change. Out=%d",out)
                    self.oldout = out
                    self.gpio(out | (self.lightsState['state'] << 15))
                self.oldtime = self.time
            time.sleep(dwell)
        log.logger.debug("Irrigation Engine exiting")
        self.clearGpio()


    def getSchedule(self):
        """ 
        Return a copy of the current schedule array
        with protection from other threads

        Inputs:  None
        Returns: A copy of the schedule array.
        """
        self.lock.acquire()
        a = copy.deepcopy(self.db['schedule'])
        self.lock.release()
        return a

    def getLightControls(self):
        """ 
        Return a copy of the current lighting controls
        with protection from other threads

        Inputs:  None
        Returns: A copy of the schedule array.
        """
        if 'lights' in self.db:
            self.lock.acquire()
            a = copy.deepcopy(self.db['lights'])
            self.lock.release()
            return a
        return None

    def zoneNames(self):
        """ 
        Return a copy of the current zone name dictionary
        with protection from other threads

        Inputs:  None
        Returns: A copy of the zone dictionary.
        """
        self.lock.acquire()
        a = copy.deepcopy(self.db['zoneNames'])
        self.lock.release()
        return a

    def getRunState(self):
        """ Return a copy of the current state dictionary
            with protection from other threads
                Inputs:  None
                Returns: A copy of the state dictionary.
        """
        self.lock.acquire()
        a = copy.deepcopy(self.db['state'])
        self.lock.release()
        return a

    def getQueue(self):
        """ 
        Return a copy of the current queue array
        with protection from other threads

        Inputs:  None
        Returns: A copy of the queue array
        """
        self.lock.acquire()
        a=copy.deepcopy(self.queue)
        self.lock.release()
        return a

    def setQueue(self,newQueue):
        """ 
        Replaces the current queue array with a new one
        with protection from other threads

        Inputs:  The new queue dictionary
        Returns: None
        """
        self.lock.acquire()
        self.db[queue]=newQueue
        self.lock.release()
        log.logger.debug("Queue replaced")

    def queueAdd(self,newEvent):
        """ 
        Add a new event to the existing queue array
        with protection from other threads.

        Inputs: The new event to be added
        Returns: None
        """
        self.lock.acquire()
        self.queue.append(newEvent)
        self.lock.release()
        log.logger.info("Queued zone %d for %d minutes",newEvent['zone'],newEvent['duration'][0])

    def gpio(self,out):
        """ 
        Set the GPIO Outputs
        For each valve (up to the value of Channels), set the gpio ooutput
        pin state based upon a bit is set in the control word 'out'

        Inputs:   out:  An integer in which each bit represents the state
                        of a given valve.  The least significant bit
                        controls valve 1.  Note that for each '1' in the
                        'out' word, the GPIO pin is driven to the low
                        state, whereas a '0' in the control word causes
                        the GPIO pin to be driven high.
        """ 
        for j in range(MaxChannels):
            GPIO.output(j,((out>>j)&1)^1)

    def clearGpio(self):
        """ Clear all GPIOS to ensure valves are all off """
        log.logger.info("Turning off all valves")
        GPIO.setmode(GPIO.BCM)
        for i in range(MaxChannels):
            GPIO.setup(i,GPIO.OUT)
            GPIO.output(i,1)

    def Simulation(self):
        return simulation
