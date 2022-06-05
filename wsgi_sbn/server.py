import socket
import sbn
from worker import WSGIWorker
from utils import get_socket_args, init_socket

class WSGIServer(sbn.Kernel):

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 5

    def __init__(self, server_address, application):
        self._create_server(server_address)
        self.application = application
        super(WSGIServer, self).__init__()

    def _create_server(self, server_address):
        listen_socket = socket.create_server(
            server_address, family=self.address_family, backlog=self.request_queue_size, reuse_port=True)

        self.listen_socket_args = get_socket_args(listen_socket)

        host, port = listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

        listen_socket.detach()

    def act(self):
        self._serve_run()

    def react(self, child):
        self._serve_run()

    def _serve_run(self):
        try:                                                                                                                                                                                                       listen_socket = init_socket(self.listen_socket_args)
        except Exception as e:                                                                                                                                                                                     print('>>>> Python (WSGI Server) [ERROR]: %s' % e, file=open('wsgisbn.log', 'a'))
        while True:
            print('>>>> Python (WSGI Server) [DEBUG]: Waiting connection', file=open('wsgisbn.log', 'a'))
            try:
                client_connection, client_address = listen_socket.accept()
            except Exception as e:
                print('>>>> Python (WSGI Server) [ERROR]: %s' % e, file=open('wsgisbn.log', 'a'))
            # Handle one request and close the client connection. Then
            # loop over to wait for another client connection
            print('>>>> Python (WSGI Server) [INFO]: Connection from %s:%s' % client_address, file=open('wsgisbn.log', 'a'))
            self._handle_request(client_connection)
            client_connection.detach()
            break # TODO

    def _handle_request(self, client_connection):
        worker = WSGIWorker(get_socket_args(client_connection), self.application, self.server_name, self.server_port)
        sbn.upstream(self, worker, target=sbn.Target.Remote)
