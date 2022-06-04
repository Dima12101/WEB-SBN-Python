import sys
import sbn
from server import WSGIServer

SERVER_ADDRESS = (HOST, PORT) = '', 8888

class Main(sbn.Kernel):
 
    def __init__(self, *args, **kwargs):
        if len(sys.argv) < 2:
            sys.exit('Provide a WSGI application object as module:callable')
        super(Main, self).__init__(*args, **kwargs)
        module, application = sys.argv[1].split(':')
        self.module = __import__(module)
        self.application = getattr(module, application)
 
    def act(self):
        print('>>>> Python (WSGI Main): ============= program start! =============', file=open('wsgisbn.log', 'a'))
            
        httpd = WSGIServer(SERVER_ADDRESS, self.application)
        httpd.enable_carries_parent()  # carries_parent
        print('>>>> Python (WSGI Main): Serving HTTP on port %s ...\n' % PORT, file=open('wsgisbn.log', 'a'))
        sbn.upstream(self, httpd, target=sbn.Target.Remote)
 
    def react(self, child: sbn.Kernel):
        print('>>>> Python (WSGI Main): program finished!', file=open('wsgisbn.log', 'a'))
        sbn.commit(self, target=sbn.Target.Remote)
