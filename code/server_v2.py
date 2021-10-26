import config
import asyncio, aiohttp
import sys, time
import json, logging

# client_id : server_id, loc, time_stamp, time_recv
clients = {}

def get_time_stamp(time_recv):
    time_stamp = ''
    time_diff = time.time() - time_recv
    if time_diff >= 0.0:
        time_stamp += '+'
    time_stamp += '{:.9f}'.format(time_diff)
    
    return time_stamp

def respond_IAMAT(args):
    client_id = args[0]
    loc = args[1]
    time_recv = args[2]
    time_stamp = get_time_stamp(float(time_recv))
    # update client info
    clients[client_id] = [server_id, loc, time_stamp, time_recv]
    
    return 'AT ' + " ".join([server_id, time_stamp, client_id, loc, time_recv])

async def respond_WHATSAT(args):
    client_id = args[0]
    radius = int(args[1]) * 1000
    upper_bound = int(args[2])
    
    if client_id not in clients:
        print('Unknown client')
        return '? WHATSAT ' + " ".join(args)
    if not(0 < radius and radius <= 50000) or \
       not (0 < upper_bound and upper_bound <= 20):
        return '? WHATSAT ' + " ".join(args)
    
    loc = clients[client_id][1]
    
    pos = loc.find('-', 1)
    if pos == -1:
        pos = loc.find('+', 1)
    
    latitude = loc[0 : pos]
    longitude = loc[pos:]
    
    
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude}%2C{longitude}&radius={radius}&key={config.API_KEY}'
    
    print(url)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            json_res = await response.json()
    
    header_res = 'AT ' + " ".join([server_id, clients[client_id][2], client_id,\
        clients[client_id][1], clients[client_id][3]])
    json_res['results'] = json_res['results'][:upper_bound]
    
    final_res = header_res + '\n'\
        + json.dumps(json_res, indent=3, ensure_ascii=False) + '\n'
    
    return final_res

# List of valid queries:
#   IAMAT client_id location current_time
#   WHATSAT client_id radius upper_bound
async def make_resp_of(query):
    tokens = query.split()
    # queries from clients
    if tokens[0] == 'IAMAT': 
        resp = respond_IAMAT(tokens[1:5])
        await propagate(resp + f' {server_id}', tokens[6:])
        return resp
    elif tokens[0] == 'WHATSAT':
        return await respond_WHATSAT(tokens[1:])
    # for inter-server communication
    elif tokens[0] == 'AT':
        clients[tokens[3]] = [tokens[1], tokens[4], tokens[2], tokens[5]]
        print (f'Updated: {tokens[3]}: {clients[tokens[3]]}')
        await propagate(query + f' {server_id}', tokens[6:])
        return f'Propagated to {server_id}'
    else:
        return '? ' + query

async def propagate(message, visited):
    print (f'path: {visited}')
    for neighbor in config.COMMUNICATION_PATTERN[server_id]:
        if neighbor not in visited:
            try:
                reader, writer = await asyncio.open_connection(
                    config.LOCALHOST, config.PORTS[neighbor])
            
                writer.write(message.encode())
                
                data = await reader.read(-1)
                print(data.decode())
                
                writer.close()
            except:
                print (f'Neighbor {neighbor} is down')

# client_connected_cb: called whenever a new client connection is established
# takes two arguments, (reader, writer), which are intances of StreamReader and
# StreamWriter classes
# Since it is  a coroutine function, it is automatically scheduled as a Task
async def client_call_back(reader, writer):
    data = await reader.read(100)
    query = data.decode()
    
    print(f'RCVD: {query}')
    resp = await make_resp_of(query)
    
    print(f'SENT: {resp}')
    writer.write(resp.encode())
    await writer.drain()
    
    writer.close()

async def run_server(server_id):
    server = await asyncio.start_server(
        client_call_back, config.LOCALHOST, config.PORTS[server_id])
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

def main(): # TODO: logging, flood algorihtm
    global server_id
    server_id = sys.argv[1]
    if server_id not in config.SERVER_IDS:
        print(f'Error: {server_id} is not valid')
        sys.exit(1)
    
    asyncio.run(run_server(server_id))

if __name__ == '__main__':
    main()