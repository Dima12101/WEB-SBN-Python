
import io
import sys
import sbn

class WSGIWorker(sbn.Kernel):
    
    def __init__(self, client_connection, application, server_name, server_port):
        super(WSGIWorker, self).__init__()
        self._client_connection = client_connection
        self.application = application
        self.server_name = server_name
        self.server_port = server_port
        
    def act(self):
        # Read the request
        self.request_data = self._read_request()
        
        # Break down the request line into components
        (self.request_method,  # GET
         self.path,            # /hello
         self.request_version  # HTTP/1.1
         ) = self._parse_request(self.request_data)
        
        # Construct environment dictionary using request data
        self.env = self._get_environ()
        
        # It's time to call our application callable and get
        # back a result that will become HTTP response body
        self.result = self.application(self.env, self.start_response)

        # Construct a response and send it back to the client
        self._finish_response(self.result)
        
        sbn.commit(self, target=sbn.Target.Remote)
        
    def _read_request(self):
        request_data = self.client_connection.recv(1024).decode('utf-8')
        # Print formatted request data a la 'curl -v'
        print(''.join(
            '< %s\n' % line for line in request_data.splitlines()
        ))
        return request_data

    def _parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')
        return request_line.split()

    def _get_environ(self):
        env = {}
        # The following code snippet does not follow PEP8 conventions
        # but it's formatted the way it is for demonstration purposes
        # to emphasize the required variables and their values
        #
        # Required WSGI variables
        env['wsgi.version']      = (1, 0)
        env['wsgi.url_scheme']   = 'http'
        env['wsgi.input']        = io.StringIO(self.request_data)
        env['wsgi.errors']       = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = True
        env['wsgi.run_once']     = False
        # Required CGI variables
        env['REQUEST_METHOD']    = self.request_method    # GET
        env['PATH_INFO']         = self.path              # /hello
        env['SERVER_NAME']       = self.server_name       # localhost
        env['SERVER_PORT']       = str(self.server_port)  # 8888
        return env

    def start_response(self, status, response_headers, exc_info=None):
        # Add necessary server headers
        server_headers = [
            ('Date', 'Mon, 15 Jul 2019 5:54:48 GMT'), # TODO
            ('Server', 'WSGIServer SBN'),
        ]
        self.headers_set = [status, response_headers + server_headers]
        # To adhere to WSGI specification the start_response must return
        # a 'write' callable. We simplicity's sake we'll ignore that detail
        # for now.
        # return self.finish_response

    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = 'HTTP/1.1 %s\r\n' % status
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')
            # Print formatted response data a la 'curl -v'
            print(''.join(
                '> %s\n' % line for line in response.splitlines()
            ))
            response_bytes = response.encode()
            self.client_connection.sendall(response_bytes)
        finally:
            self.client_connection.close()
