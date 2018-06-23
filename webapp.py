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

import cherrypy
from jinja2 import Environment, FileSystemLoader
import time
import simplejson as json
import copy
import log

dayNumbers = {"Sunday" :1, "Monday" : 2, "Tuesday" : 3,
              "Wednesday" : 4, "Thursday" : 5, "Friday" : 6,
              "Saturday" : 7}


class Root:
    """
    This class is the CherryPy web application
    """
    def __init__(self,theIrrigationEngine,channels):
        """ 
        The web application constructor
        Set up the Jinja templating system and initalize the database
        by reading from theFile, or, if unable to read the file,
        create a blank database.  The queue is always empty at the
        start. 

        theFile: The name of the file from which to read the database
        """
        self.theIrrigationEngine = theIrrigationEngine
        self.env = Environment(loader=FileSystemLoader('templates'))
        self.channels=channels

    @cherrypy.expose
    def index(self):
        """
        Serve the index page of the website using the Jinja templeting
        engine. Called from the CherryPy framework.  This is (mostly)
        a single page webapp that is heavily controlled by javascript
        on the client side.  
        """
        args = {'title':"%d Channel Irrigation Controller" % self.channels,
                'request':cherrypy.request.headers,
                'simulation':self.theIrrigationEngine.Simulation(),
                'leftcol' : (
                ),
                'centercol': (
                    ('schedule.html', "id='schedule'"),
                    ('addevent.html', "id='addevent'"),
                ),
                'rightcol': (
                    ('queue.html' , "id='queue'" ),
                    ('manual.html', "id='manual'"),
                    ('lighting.html', "id='lighting'"),
                ),
                'scripts' : (
                    "static/javascript/jquery.js",
                    "static/javascript/form.js",
                    "static/javascript/main.js",
                    "static/javascript/jquery-ui.js",
                    ),
                'channels':self.channels,
               }
        return self.env.get_template('index.html').render(args)

    @cherrypy.expose
    def zone(self):
        """
        Serve the zone page of the website using the Jinja templeting
        engine. Called from the CherryPy framework.  This and about
        are the  is the only web application pages besides the index
        page.  This page provides a form to permit the zone names to
        be edited  
        """
        args = {'title':"%d Channel Irrigation Controller" % self.channels,
                'simulation':self.theIrrigationEngine.Simulation(),
                'request':cherrypy.request.headers,
                'leftcol' : (
                ),
                'centercol': (
                    ('zone.html', "id='zone'"),
                ),
                'rightcol': (
                ),
                'scripts' : (
                    "static/javascript/jquery.js",
                    "static/javascript/form.js",
                    "static/javascript/zone.js",
                    
                ),
                'channels':self.channels,
        }
        return self.env.get_template('index.html').render(args)
    
    @cherrypy.expose
    def about(self):
        """
        Serve the about page of the website using the Jinja templeting
        engine. Called from the CherryPy framework.  This is and zone
        are the only web application pages besides the index page.
        This page provides information only
        """
        args = {'title':"%d Channel Irrigation Controller" % self.channels,
                'simulation':self.theIrrigationEngine.Simulation(),
                'request':cherrypy.request.headers,
                'leftcol' : (
                ),
                'centercol': (
                    ('about.html', "id='schedule'"),
                ),
                'rightcol': (
                ),
                'scripts' : (
                ),
        }
        return self.env.get_template('index.html').render(args)
    
    @cherrypy.expose
    def log(self):
        """
        Serve the about page of the website using the Jinja templeting
        engine. Called from the CherryPy framework.  This is and zone
        are the only web application pages besides the index page.
        This page provides information only
        """
        with open ("asRun.log","r") as theFile:
            data=theFile.read()
        args = {'title':"%d Channel Irrigation Controller" % self.channels,
                'simulation':self.theIrrigationEngine.Simulation(),
                'request':cherrypy.request.headers,
                'leftcol' : (
                ),
                'centercol': (
                    ('log.html', "id='asrunlog'"),
                ),
                'rightcol': (
                ),
                'scripts' : (
                ),
                'logdata': data
        }
        return self.env.get_template('index.html').render(args)
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def servertime(self):
        """ 
        Serve a JSON formated response containing the current time,
        the current runstate, and the current manual control settings.
        Used by client side Javascript as an ajax callback to update
        the single page application  
        """
        keys=('year', 'month', 'day', 'hour', 'min', 'sec','wkday')
        theResponse =  dict(zip(keys,time.localtime()))
        theResponse['running']=self.theIrrigationEngine.getRunState()
        theResponse['manual']=self.theIrrigationEngine.manual
        theResponse['lightsState']=self.theIrrigationEngine.lightsState
        theResponse['lights']=self.theIrrigationEngine.getLightControls()
        return theResponse

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def schedule(self):
        """ 
        Serve a JSON formated response containing the current schedule
        Used by client side Javascript as an ajax callback to update
        the single page application  
        """
        return self.theIrrigationEngine.getSchedule()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getzones(self):
        """ 
        Serve a JSON formated response containing the current zone names
        Used by client side Javascript as an ajax callback to update
        the single page application  
        """
        return self.theIrrigationEngine.zoneNames()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getqueue(self):
        """ 
        Serve a JSON formated response containing the current queue
        Used by client side Javascript as an ajax callback to update
        the single page application  
        """
        return self.theIrrigationEngine.getQueue()
 
    @cherrypy.expose
    def deleteevent(self):
        """ 
        Handle a post event to delete an item from the schedule.  The
        post contains an array of indicies to delete.  Used by
        Javascript on the client side to update the database  
        """
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        body = json.loads(rawbody)
        # Sort the array and start with the greatest index and work
        # backwards so that the elements assocaited with the lesser
        # indicies don't shift around 
        body.sort();
        self.theIrrigationEngine.lock.acquire()
        while len(body) > 0 :
            b=body.pop()
            if (b <= len(self.theIrrigationEngine.db["schedule"])) and b > 0:
                log.logger.info("Deleting event index %d",b-1)
                del self.theIrrigationEngine.db["schedule"][b-1]
                self.theIrrigationEngine.writeConfig()
        a = copy.deepcopy(self.theIrrigationEngine.db["schedule"])
        self.theIrrigationEngine.lock.release()
        return "Updated %r." % (a,)

    @cherrypy.expose
    def queueevent(self):
        """ 
        Handle a post event to imeadiately queue a scheduled event.  The
        post contains an array of indicies of the schedule to enqueue now.  Used by
        Javascript on the client side to update the queue  
        """
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        body = json.loads(rawbody)
        # Sort the array and start with the greatest index and work
        # backwards so that the elements assocaited with the lesser
        # indicies don't shift around 
        body.sort();
        while len(body) > 0 :
            b=body.pop(0)
            if (b <= len(self.theIrrigationEngine.db["schedule"])) and b > 0:
                for x in range(1,self.channels +1):
                    try:
                        if int(self.theIrrigationEngine.db["schedule"][b-1]['valve%i'%(x,)])>0:
                            self.theIrrigationEngine.queueAdd({'zone':x,'duration':[int(self.theIrrigationEngine.db['schedule'][b-1]['valve%i'%(x,)]),0]})
                    except:
                        pass
        return "Queue Updated"

    @cherrypy.expose
    def addevent(self):
        """ 
        Handle a post event to add an item to the schedule.  The
        post contains an element to add to the schedule array.  Used by
        Javascript on the client side to update the database  
        """
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        body = json.loads(rawbody)
        self.theIrrigationEngine.lock.acquire()
        self.theIrrigationEngine.db["schedule"].append(body)
        self.theIrrigationEngine.db["schedule"].sort( key = lambda x : x["eventTime"])
        self.theIrrigationEngine.db["schedule"].sort( key = lambda x : dayNumbers[x['day']])
        log.logger.info("Added event to schedule")
        self.theIrrigationEngine.writeConfig()
        a = copy.deepcopy(self.theIrrigationEngine.db["schedule"])
        self.theIrrigationEngine.lock.release()
        return "Updated %r." % (a,)

    @cherrypy.expose
    def runstate(self):
        """ 
        Handle a post event to update the current run state.  The
        post contains an element called 'running' which contains a
        binary that becomes the new run state.  As a side effect, the
        manual controls are cleared when the state is updated. Used by
        Javascript on the client side to update the database.  
        """
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        body = json.loads(rawbody)
        self.theIrrigationEngine.manual=[False for i in range(self.channels)]
        self.theIrrigationEngine.lock.acquire()
        self.theIrrigationEngine.db["state"]=body['running']
        self.theIrrigationEngine.writeConfig()
        a=copy.deepcopy(self.theIrrigationEngine.db["state"])
        self.theIrrigationEngine.lock.release()
        log.logger.warn("Run state changed to %s",a)
        return "Updated %r." % (a,)

    @cherrypy.expose
    def manual(self):
        """ 
        Handle a post event to update the current manual controls
        state.  The post contains an dictionary of binary valve
        states. Used by Javascript on the client side to update the
        database.   
        """
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        body = json.loads(rawbody)
        for i in range(self.channels):
            self.theIrrigationEngine.manual[i]= body["manual%d"%(i+1)]
        a=copy.deepcopy(self.theIrrigationEngine.manual)
        return "Updated %r." % (a,)

    @cherrypy.expose
    def lights(self):
        """ 
        Handle a post event to update the current light controls
        state.  Used by Javascript on the client side to update the
        database.   
        """
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        body = json.loads(rawbody)
        self.theIrrigationEngine.lock.acquire()
        self.theIrrigationEngine.db["lights"]=body["controls"]
        self.theIrrigationEngine.lightsState['state']=body["state"]
        self.theIrrigationEngine.lightsState['changeCount'] += 1
        self.theIrrigationEngine.writeConfig()
        self.theIrrigationEngine.lock.release()
        return "Updated Lights"

    @cherrypy.expose
    def setzonenames(self):
        """ 
        Handle a post event to update the zone names. The post
        contains a dict of zone names by valve number. Used by
        Javascript on the client side to update the database.   
        """
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        body = json.loads(rawbody)
        self.theIrrigationEngine.lock.acquire()
        self.theIrrigationEngine.db["zoneNames"]=body
        self.theIrrigationEngine.writeConfig()
        a=copy.deepcopy(self.theIrrigationEngine.db["zoneNames"])
        self.theIrrigationEngine.lock.release()
        return "Updated %r." % (a,)

    @cherrypy.expose
    def clearqueue(self):
        """ 
        Handle a post event to clear the queue. The post
        contains nothing of importance. Used by
        Javascript on the client side to update the database.   
        """
        self.theIrrigationEngine.lock.acquire()
        self.theIrrigationEngine.queue=[]
        self.theIrrigationEngine.lock.release()
        return "Queue Cleared"
