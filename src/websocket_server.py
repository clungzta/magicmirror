import zmq
from zmq_utils import get_uri
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream
ioloop.install()

from urlparse import urlparse
from tornado.websocket import WebSocketHandler
from tornado.web import Application
from tornado.ioloop import IOLoop
ioloop = IOLoop.instance()

class ZMQPubSub(object):

    def __init__(self, callback):
        self.callback = callback

    def connect(self, uri):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        print("Subscribing to {}".format(uri))
        self.socket.connect(uri)

        self.stream = ZMQStream(self.socket)
        self.stream.on_recv(self.callback)

    def subscribe(self, channel_id):
        self.socket.setsockopt(zmq.SUBSCRIBE, channel_id)

class MyWebSocket(WebSocketHandler):

    def open(self):
        self.session_name = ''
        self.websocket_opened = True        
        self.pubsub = ZMQPubSub(self.on_data)
        self.pubsub.connect(get_uri('0.0.0.0', 6700))
        self.pubsub.subscribe(self.session_name)

        print('websocket opened')

    def on_message(self, message):
        print(message)
    
    def on_close(self):
        self.websocket_opened = False                
        print('websocket closed')

    def on_data(self, data):
        ''' zmq pubsub callback '''
        
        print(data)

        if self.websocket_opened:
            self.write_message(data[0])

    def check_origin(self, origin):
        parsed_origin = urlparse(origin)
        print(parsed_origin)
        return True
        # return parsed_origin.netloc.endswith(".mydomain.com")

def main():
    application = Application([(r'/channel', MyWebSocket)])
    application.listen(10001)
    print('starting websocket server on port 10001')
    ioloop.start()

if __name__ == '__main__':
    main()