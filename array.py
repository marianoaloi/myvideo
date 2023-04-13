
import os
import sys

separetor=":"

if(len(sys.argv)>1 and sys.argv[1]):
    separetor=sys.argv[1]

    

print(separetor.join([x for x in os.getenv('NAUTILUS_SCRIPT_SELECTED_FILE_PATHS').split("\n") if x]))