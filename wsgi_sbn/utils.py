import socket

def get_socket_args(socket):
    return dict(
        fd=socket.fileno(),
        family=socket.family,
        type=socket.type,
        proto=socket.proto,
    )
    
def init_socket(socket_args):
    return socket.fromfd(**socket_args)
