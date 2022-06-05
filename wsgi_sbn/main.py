import os
import sys
import importlib
import sbn

cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cwd)
sys.path.append(os.path.dirname(cwd))
from server import WSGIServer

SERVER_ADDRESS = (HOST, PORT) = '', 8888

class Main(sbn.Kernel):

    def __init__(self, *args, **kwargs):
        if len(sys.argv) < 2:
            print('>>>> Python (WSGI Main) [ERROR]: Provide a WSGI application object as module:callable', file=open('wsgisbn.log', 'a'))
            sys.exit()
        self.app_path = sys.argv[1]
        module, application = self.app_path.split(':')

        try:
            module = importlib.import_module(module)
            self.application = getattr(self.module, application)
        except Exception as e:
            print('>>>> Python (WSGI Main) [ERROR]: %s' % e, file=open('wsgisbn.log', 'a'))
            sys.exit()
        super(Main, self).__init__(*args, **kwargs)

    def act(self):
        print('\n>>>> Python (WSGI Main) [INFO]: ============= program start! =============', file=open('wsgisbn.log', 'a'))
        print('>>>> Python (WSGI Main) [INFO]: App - %s' % self.app_path, file=open('wsgisbn.log', 'a'))
        httpd = WSGIServer(SERVER_ADDRESS, self.application)
        httpd.enable_carries_parent()  # carries_parent
        print('>>>> Python (WSGI Main) [INFO]: Serving HTTP on %s:%s ...' % (httpd.server_name, httpd.server_port), file=open('wsgisbn.log', 'a'))
        sbn.upstream(self, httpd, target=sbn.Target.Remote)

    def react(self, child: sbn.Kernel):
        print('>>>> Python (WSGI Main) [INFO]: program finished!', file=open('wsgisbn.log', 'a'))
        sbn.commit(self, target=sbn.Target.Remote)
