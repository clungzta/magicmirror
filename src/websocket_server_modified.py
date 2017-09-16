import json
import uuid
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

class MMZMQWebSocketBridge(object):

    def __init__(self, callback):
        self.callback = callback

    def connect(self, uri_in, uri_out):
        self.context = zmq.Context()

        self.sub_socket = self.context.socket(zmq.SUB)
        print("Subscribing to {}".format(uri_in))
        self.sub_socket.connect(uri_in)

        self.in_stream = ZMQStream(self.sub_socket)
        self.in_stream.on_recv(self.callback)

        # self.pub_socket = self.context.socket(zmq.PUB)
        # self.pub_socket.bind(uri_out)
        
    def sub_init(self, channel_id):
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, channel_id)        

class MyWebSocket(WebSocketHandler):

    def open(self):
        self.session_name = uuid.uuid4().hex[:8]
        self.websocket_opened = True        
       
        self.bridge = MMZMQWebSocketBridge(self.on_data)
        self.bridge.connect(get_uri('0.0.0.0', 6700), get_uri('0.0.0.0', 6701))
        self.bridge.sub_init('')
        
        # self.bridge.speech_sub_init('{}-SPEECH_OUTPUT'.format(self.session_name))

        print('Websocket session {} opened.'.format(self.session_name))

    def on_message(self, data):
        print('{}: {}'.format(self.session_name, data))

        # try:
        #     msg = json.loads(data)
        #     self.bridge.pub_socket.send("{}-{}-{}".format(self.session_name, msg['topic_suffix'], msg['message']))
        # except KeyError as e:
        #     print('Ensure that the websocket JSON message contains "topic_suffix" and "message" keys')

    def on_close(self):
        self.websocket_opened = False                
        print('websocket closed')

    def on_data(self, data):
        ''' zmq sub callback '''
        
        print('at callback')
        print(data)

        if self.websocket_opened:
            self.write_message(data[0])

    def check_origin(self, origin):
        # parsed_origin = urlparse(origin)
        return True

def main():
    application = Application([(r'/channel', MyWebSocket)])
    application.listen(10001)
    print('starting websocket server on port 10001')
    ioloop.start()

if __name__ == '__main__':
    main()