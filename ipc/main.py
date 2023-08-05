import asyncio
import struct

async def send_msg(sock, msg: bytes):
    """
    Send a message to the socket prefixed with the length
    :param sock: socket to send to
    :param msg: message

    :type msg: bytes
    """
    # get event loop
    loop = asyncio.get_event_loop()
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    # send
    await loop.sock_sendall(sock, msg)

async def recv_msg(sock) -> bytes or None:
    """
    Receive a message prefixed with the message length
    :param sock: socket
    :return: bytes
    """
    # Read message length and unpack it into an integer
    raw_msglen = await recv_all(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return await recv_all(sock, msglen)

async def recv_all(sock, n) -> bytes or None:
    """
    Recieve all
    :param sock: socket
    :param n: length to read
    :return: bytes or None
    """
    # get event loop
    loop = asyncio.get_event_loop()
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = await loop.sock_recv(sock, (n - len(data)))
        if not packet:
            return None
        data.extend(packet)
    return data