#! /usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
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

import os
from cmdline import CmdLineArgs
import cherrypy
import log
from pathlib import Path
from webapp import Root
import cherrypy
from engine import IrrigationEngine
            
Channels = 10
theConfigFile=""
            
class IrrigationPlugin(cherrypy.process.plugins.SimplePlugin):
    """
    Plug in for the CherryPy engine that controls the irrigtion state machine.
    This plugin is registered with the CherryPy plug in to control the
    starting and stopping of the irrigaton state machine.
    """
    def __init__(self, bus, IrrigationClass,ConfigFile):
        """
        Instanciate the class.  
        Set up the super class and then create an instance of the
        irrigation state machine
        """
        log.logger.debug("Irrigation Plugin Initializing")
        cherrypy.process.plugins.SimplePlugin.__init__(self, bus)
        self.engine = IrrigationClass(ConfigFile,Channels)

    def start(self):
        """ 
        Start the irrigation state machine
        Called by the CherryPy engine when it is starting.  This
        starts the background thread in the irrigation satte machine
        """
        log.logger.debug("Irrigation plug in start")
        self.engine.start()
        
    def stop(self):
        """ 
        Stop the irrigation state machine
        Called by the CherryPy engine when the engine is stopping.
        This calls the stop method which sets a flag that will cause
        the child thread to stop (eventually)
        """
        log.logger.debug("Irrigation plug in stop")
        self.engine.stop()
        
        
def setConfigFile(theFile):
    """ 
    Set the configuration file name
    Helper function called by the command line argument logic when the
    user provides a config file name
    """
    global theConfigFile
    theConfigFile= theFile


        
def main():
    CmdLineArgs("Web Server for prototype single page application",
                (
                    (('-v', '--verbose'), 'verbose', 'store_true', None, None,
                     "Generate information", None,
                     lambda x: log.setLog(x,'INFO')
                    ),
                    (('-d', '--debug'),'debug', 'store_true', None, None,
                     "Generate debugging information", None,
                     lambda x: log.setLog(x,'DEBUG')
                    ),
                    (('-q', '--quiet'), 'notQuiet', 'store_false', None, None,
                     "Supress logs to screen", None,
                     lambda x: cherrypy.config.update({'log.screen':x,})
                    ),
                    (('-l', '--logfile'), 'logfile', 'store', str, '',
                     "Access Log File Name", None,
                     lambda x: cherrypy.config.update({'log.access_file':x,})
                    ),
                    (('-c', '--configfile'), 'configfile', 'store', str, str(Path.home())+"/.config/irrigation",
                     "Configuration File Name", None,
                     lambda x: setConfigFile(x)
                    ),
                    (('-e', '--errfile'), 'errfile', 'store', str, 'err.log',
                     "Error Log File Name",None,
                     lambda x: cherrypy.config.update({'log.error_file':x,})
                    ),
                    (('-H','--host'), 'host', 'store', str,'localhost',
                     "Host base URL", None,
                     lambda x: cherrypy.config.update({'server.socket_host': x})
                    ),
                ),
    )
    thePlugIn=IrrigationPlugin(cherrypy.engine,IrrigationEngine,theConfigFile)
    thePlugIn.subscribe()
    cherrypy.quickstart(Root(thePlugIn.engine,Channels),
                        '/',
                        { '/' :
                          {'tools.staticdir.root': os.path.abspath(os.getcwd()),
                          },
                          '/static':
                          {'tools.staticdir.on' : True,
                           'tools.staticdir.dir' : './public'
                          },
                        }
    )
    thePlugIn.engine.clearGpio()
    log.logger.info("Exiting program")
                    
if __name__ == '__main__':
    main()
 
