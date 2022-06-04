import socket
import sbn
from worker import WSGIWorker

class WSGIServer(sbn.Kernel):

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 5

    def __init__(self, server_address, application):
        super(WSGIServer, self).__init__()
        self._init_server(server_address)
        self._init_app(application)


    def _init_server(self, server_address):
        # Create a listening socket
        self.listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        # Allow to reuse the same address
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind
        self.listen_socket.bind(server_address)
        # Activate
        self.listen_socket.listen(self.request_queue_size)
        # Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by Web framework/Web application
        self.headers_set = []

    def _init_app(self, application):
        self.application = application

    def act(self):
        self._serve_forever()

    def _serve_forever(self):
        listen_socket = self.listen_socket
        print('>>>> Python (WSGI Server) [DEBUG]: Socket - %s' % listen_socket, file=open('wsgisbn.log', 'a'))
        while True:
            print('>>>> Python (WSGI Server) [DEBUG]: Waiting connection', file=open('wsgisbn.log', 'a'))
            #sbn.sleep(1000)
            # New client connection
            try:
                client_connection, client_address = listen_socket.accept()
            except Exception as e:
                print('>>>> Python (WSGI Server) [ERROR]: %s' % e, file=open('wsgisbn.log', 'a'))
            # Handle one request and close the client connection. Then
            # loop over to wait for another client connection
            print('>>>> Python (WSGI Server) [INFO]: Connection from %s:%s' % client_address, file=open('wsgisbn.log', 'a'))
            self._handle_request(client_connection)

    def _handle_request(self, client_connection):
        worker = WSGIWorker(client_connection, self.application, self.server_name, self.server_port)
        sbn.upstream(self, worker, target=sbn.Target.Remote)
