
import pymongo
from send2trash import send2trash
from datetime import datetime
import hashlib , pathlib

import os
import sys

def flatMap(files):
    result=[]

    for file in files:
        if os.path.isfile(file):
            result.append(file)
        elif os.path.isdir(file) :
            result += map(lambda x:os.path.join(file,x),next(os.walk(file), (None, None, []))[2]  )# [] if no file

    return result

files=[x 
        for x in os.getenv('NAUTILUS_SCRIPT_SELECTED_FILE_PATHS').split("\n") 
        if x]

files=flatMap(files)


md5s=list(map(lambda x: hashlib.md5(pathlib.Path(x).read_bytes()).hexdigest() , files))


db=pymongo.MongoClient(
                    'mongodb://maloi:J4v4P0w3r@192.168.25.42:27017/?authSource=admin&readPreference=primary&appname=MaloyPython&directConnection=true&ssl=false'
                    )["4shared"]
ColPost=db["posts"]
ColPost.update_many({'md5':{'$in':md5s}},{'$set':{'deleted':datetime.now(),'statustransition':"deleted"}})
videos_deleted=ColPost.find({'md5':{'$in':md5s},'mimeType':{'$regex':'video'}})
try:
    ColPost.insert_many([ {"_id":"fake_"+x["_id"],"md5":x["md5"]} for x in videos_deleted])
except Exception as e :
    print(e)    
send2trash(files);