import config
import asyncio, aiohttp
import sys, time

# client_id : server_id, loc, time_stamp
clients = {}

def handle_IAMAT(args):
    client_id = args[0]
    loc = args[1]
    time_recv = float(args[2])
    
    time_stamp = ''
    time_diff = time.time() - time_recv
    if time_diff >= 0.0:
        time_stamp += '+'
    time_stamp += '{:.9f}'.format(time_diff)
    
    clients[client_id] = [server_id, loc, time_stamp]
    
    return 'AT ' + " ".join([server_id, time_stamp, loc, args[2]])

def handle_WHATSAT(args):
    client_id = args[0]
    radius = args[1]
    upper_bound = args[2]
    
    if client_id not in clients:
        return '? WHATSAT ' + " ".join(args)
    
    return 'WORKING...' # TODO: embed aiohttp connecting with Google Places API
    
def make_resp_of(query):
    tokens = query.split()
    if tokens[0] == 'IAMAT':
        return handle_IAMAT(tokens[1:])
    elif tokens[0] == 'WHATSAT':
        return handle_WHATSAT(tokens[1:])
    else:
        return '? ' + query
        
# client_connected_cb: called whenever a new client connection is established
# takes two arguments, (reader, writer), which are intances of StreamReader and
# StreamWriter classes
# Since it is  a coroutine function, it is automatically scheduled as a Task
async def client_call_back(reader, writer):
    data = await reader.read(100)
    query = data.decode()
    
    resp = make_resp_of(query)
    
    print('Sending: {}'.format(resp))
    writer.write(resp.encode())
    await writer.drain()
    
    print('Close the connection')
    writer.close()

async def run_server(server_id):
    server = await asyncio.start_server(
        client_call_back, config.LOCALHOST, config.PORTS[server_id])
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print('Serving on {}'.format(addrs))

    async with server:
        await server.serve_forever()

def main():
    global server_id
    server_id = sys.argv[1]
    
    asyncio.run(run_server(server_id))

if __name__ == '__main__':
    main()