from utils.unpickle import unpickle

import socket
import struct
import pickle
import os

inside_docker = os.environ.get("INSIDE_DOCKER", False)
send_host = os.environ.get("SEND_HOST", '172.0.0.1')

HOST = '127.0.0.1' if not inside_docker or not inside_docker == 'true' else send_host  # The server's hostname or IP address
PORT = 5421  # The port used by the server

def send_arg(arg_dict: dict, get_response: bool = True):
    """
    Send an argument dictionary to the socket and return the response
    :param arg_dict: dictionary to send
    :param get_response: whether to wait for a response
    :return: response dictionary or None
    """
    # Create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    # serialize and send
    msg = pickle.dumps(arg_dict)
    send_msg(s, msg)

    if get_response:
        response = recv_msg(s)

        if response is None:
            return None

        return unpickle(response)

def send_msg(sock, msg: bytes):
    """
    Send a message to the socket prefixed with the length
    :param sock: socket to send to
    :param msg: message

    :type msg: bytes
    """
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock) -> bytes or None:
    """
    Receive a message prefixed with the message length
    :param sock: socket
    :return: bytes
    """
    raw_msg_len = recv_all(sock, 4)

    if not raw_msg_len:
        return None
    msg_len = struct.unpack('>I', raw_msg_len)[0]

    return recv_all(sock, msg_len)

def recv_all(sock, n) -> bytes or None:
    """
    Recieve all
    :param sock: socket
    :param n: length to read
    :return: bytes or None
    """
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(int(n - len(data)))
        if not packet:
            return None
        data.extend(packet)
    return data
