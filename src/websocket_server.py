
import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream
ioloop.install()

import uuid

from tornado.websocket import WebSocketHandler
from tornado.web import Application
from tornado.ioloop import IOLoop
ioloop = IOLoop.instance()

class ZMQPubSub(object):

    def __init__(self, callback):
        self.callback = callback

    def connect(self):
        uri_sub = 'tcp://127.0.0.1:6700'
        uri_pub = 'tcp://127.0.0.1:6701'

        self.context = zmq.Context()
        # FIXME: getting address already in use error
        # self.pub_socket = self.context.socket(zmq.PUB)
        # self.pub_socket.bind(uri_pub)

        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(uri_sub)
        self.stream = ZMQStream(self.sub_socket)
        self.stream.on_recv(self.callback)

    def subscribe(self, channel_id):
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, channel_id)

class MyWebSocket(WebSocketHandler):

    def open(self):
        self.session_name = uuid.uuid4().hex[:8]
        self.websocket_opened = True        
        self.pubsub = ZMQPubSub(self.on_data)
        self.pubsub.connect()
        self.pubsub.subscribe("")
        print('ws opened')

    def on_message(self, message):
        print(message)
        self.pubsub.pub_socket.send('{} {}'.format(self.session_name, message))
    
    def on_close(self):
        self.websocket_opened = False
        print('ws closed')

    def on_data(self, data):
        # print(data)

        if self.websocket_opened:
            self.write_message(data[0])
    
    def check_origin(self, origin):
        return True

def main():
    application = Application([(r'/channel', MyWebSocket)])
    application.listen(10001)
    print 'starting ws on port 10001'
    ioloop.start()

if __name__ == '__main__':
    main()