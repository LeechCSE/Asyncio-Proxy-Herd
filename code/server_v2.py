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

async def handle_WHATSAT(args):
    client_id = args[0]
    radius = args[1] * 1000
    upper_bound = args[2]
    
    if client_id not in clients:
        return '? WHATSAT ' + " ".join(args)
    if not(0 < radius and radius <= 50) or \
       not (0 < upper_bound and upper_bound <= 20):
        return '? WHATSAT ' + " ".join(args)
    
    loc = clients[client_id][1]
    
    pos = loc.find('-', 1)
    if pos == -1:
        pos = loc.find('+', 1)
    
    latitude = loc[0 : pos]
    longitude = loc[pos:]
    
    # TODO: not tested yet. maybe need to use session.post(url, json =...)
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?language=en&location={latitude},{longitude}&radius={radius}&key={config.API_KEY}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    
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
    
    print(f'Sending: {resp}')
    writer.write(resp.encode())
    await writer.drain()
    
    print('Close the connection')
    writer.close()

async def run_server(server_id):
    server = await asyncio.start_server(
        client_call_back, config.LOCALHOST, config.PORTS[server_id])
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

def main():
    global server_id
    server_id = sys.argv[1]
    
    asyncio.run(run_server(server_id))

if __name__ == '__main__':
    main()