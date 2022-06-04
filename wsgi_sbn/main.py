import os
import sys
import sbn

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server import WSGIServer

SERVER_ADDRESS = (HOST, PORT) = '', 8888

class Main(sbn.Kernel):

    def __init__(self, *args, **kwargs):
        if len(sys.argv) < 2:
            print('>>>> Python (WSGI Main) [ERROR]: Provide a WSGI application object as module:callable', file=open('wsgisbn.log', 'a'))
            sys.exit()
        module, application = sys.argv[1].split(':')
        try:
            self.module = __import__(module)
            self.application = getattr(self.module, application)
        except Exception as e:
            print('>>>> Python (WSGI Main) [ERROR]: %s' % e, file=open('wsgisbn.log', 'a'))
        super(Main, self).__init__(*args, **kwargs)

    def act(self):
        print('\n>>>> Python (WSGI Main) [INFO]: ============= program start! =============', file=open('wsgisbn.log', 'a'))
        httpd = WSGIServer(SERVER_ADDRESS, self.application)
        httpd.enable_carries_parent()  # carries_parent
        print('>>>> Python (WSGI Main) [INFO]: Serving HTTP on port %s ...' % PORT, file=open('wsgisbn.log', 'a'))
        sbn.upstream(self, httpd, target=sbn.Target.Remote)

    def react(self, child: sbn.Kernel):
        print('>>>> Python (WSGI Main) [INFO]: program finished!', file=open('wsgisbn.log', 'a'))
        sbn.commit(self, target=sbn.Target.Remote)
