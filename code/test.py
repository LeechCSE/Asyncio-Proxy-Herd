import config

import sys, time
import asyncio
# ref. from asycio - 18.5.4.3.1. TCP echo client protocol
# https://docs.python.org/3/library/asyncio-protocol.html#asyncio-protocol
class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, msg, loop):
        self.msg = msg
        self.loop = loop

    def connection_made(self, transport):
        transport.write(self.msg.encode())
        print('Message sent: {!r}'.format(self.msg))

    def data_received(self, data):
        print('Message received: {}'.format(data.decode()))

    def connection_lost(self, exc):
        print(str(exc))
        self.loop.stop()

def main():
    server_name = sys.argv[1]
    msg = sys.argv[2]
    port = config.PORTS[server_name]

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(lambda: EchoClientProtocol(msg, loop),
                                  config.LOCALHOST, port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()

if __name__ == '__main__':
    main()
