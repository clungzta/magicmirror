
import zmq
import json
import time
from google.cloud import datastore

client = datastore.Client()
print(vars(client))

current_milli_time = lambda: int(round(time.time() * 1000))

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://127.0.0.1:6700')
socket.setsockopt(zmq.SUBSCRIBE, '')

names = set()

loopCount = 0
while True:
    loopCount += 1
    message = json.loads(socket.recv())
    names.update([name.lower() for name in message.keys()])

    print(list(names))

    if (loopCount % 100 == 0):
        entity = datastore.Entity(client.key('Interaction', current_milli_time()))
        entity['people'] = list(names)
        
        print('Putting')
        with client.batch() as batch:
            batch.put(entity)
        
        names = set()

