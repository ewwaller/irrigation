from argparse import ArgumentParser
from enum import IntEnum
import logging
try:
    import argcomplete
    argcompleteAvailable=True
except ImportError:
    argcompleteAvailable=False

class CmdLineArgs:
    """ Class to generate command line options and how to parse them
     
     Initialize the CmdLineArgs class with (description, theParameters).  This class
     uses ArgumentParser to provide a command line interface. Hint: Run this program 
     with the --help option to request the usage information to see this class in action.

     description:  A string that describes the program.

     theParameters: A tuple of inner tuples that  defines the command line options, where
                    and how their data are stored, and define the relation
                    of the command line parameters to things that are stored in
                    persistent storage. These are obtained using the next_arg method.
                    Each inner tupple (as defined below) defines each possible 
                    command line parameter.  If there are n possible command line 
                    parameters the outer tuple will contain n inner tuples.
                    For each inner tupple:
                         Element 0 is a tuple of the string defining the short option name,
                                   and a string defining the long option name,
                         Element 1 is the destination name in the ArgumentParser object,
                         Element 2 is a string describing the ArgumentParser action,
                         Element 3 is the python type,
                         Element 4 is the default value
                         Element 5 is the help string, and
                         Element 6 is the required flag
                         Element 7 (optional) is a function for the option
    """

    argNames = ('name', 'dest', 'action', 'type',
                'default', 'help', 'required', 'callBack')
    items = IntEnum('argValues',argNames,start=0)
    
    def __init__(self, description,theParameters,logger=None):
        self.theParameters = theParameters
        self.logger=logging.getLogger(__name__)
        global argcompleteAvailable
        
        parser = ArgumentParser(description=description)
        [parser.add_argument(*option[0], **option[1]) for option in self.next_arg()]

        if argcompleteAvailable:
            argcomplete.autocomplete(parser)

        # Process all Args first, then act upon the function calls
        # after all inputs have been processed and stored.
        
        self.args = parser.parse_args()
        self.process_args()

        # Delay logging until the end -- only then do we know if we
        # are logging and if we have a logger.
        
        self.logger.debug("Command line arguments: {}".format(self.args))
 
    def next_arg(self):
        """
        Generate the next command line argment descriptor

           Inputs: None
           Yields: The next argument definition as a 2-tuple consisting of:

                       1. a tuple containing the short and long names used
                       as the positional parameters for a function
                       call ( *args) 

                       2. a dictionary containing keys defined by
                       parameter names and values from theParameters
                       for which the user provided value is not None.
                       IOW, None values are not placed in the
                       dictionary. The dictionary is used as keyword
                       parameters for a function call (**kwarg)
        """

        for option in self.theParameters:
            yield (
                option[CmdLineArgs.items.name],
                {k:v for k, v in
                   dict(zip(CmdLineArgs.argNames
                            [CmdLineArgs.items.dest
                             : CmdLineArgs.items.required],
                            option[CmdLineArgs.items.dest:])
                   ).items() if v is not None
                }
            )

    def process_args(self):
        """
        Process the function callbacks of the Argument
        
           Inputs: None.
           Oututs: None

           Side Effects: For each input parameter, if the value is not
                         None, and if there is a callback function and
                         it is not None, then call the callback with
                         the argument value. 
        """
        
        [option[CmdLineArgs.items.callBack](getattr(self.args, option[CmdLineArgs.items.dest]))
           for option in self.theParameters
              if len(option) > CmdLineArgs.items.callBack and
                 option[CmdLineArgs.items.callBack] and
                 getattr(self.args, option[CmdLineArgs.items.dest]) is not None]
