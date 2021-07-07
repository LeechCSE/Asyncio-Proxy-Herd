import config

import sys, time, datetime, os, logging
import asyncio, ssl, aiohttp, json

class ProxyServerProtocol(asyncio.Protocol):
    clients = {} # clientID: [serverID, time_skew, location, send_time]
    def __init__(self, serverID):
        self.server_name = serverID
        self.pattern = config.COMMUNICATION_PATTERN[serverID]
    ############
    ## parser ##
    ############
    def parse_time(self, client_info):
        return float(client_info.split()[5])
    def parse_location(self, location):
        lat_str, lng_str = '', ''
        split_flag, first_flag = True, True
        for char in location:
            if ((not first_flag) and (char == '+' or char == '-')):
                split_flag = False
            if split_flag: lat_str += char
            else: lng_str += char
            if first_flag: first_flag = False
        return lat_str, lng_str
    #############
    ## generic ##
    #############
    # ref. 18.5.4.2.2. Transports & protocols - Connection callbacks
    # https://docs.python.org/3/library/asyncio-protocol.html#asyncio-protocol
    # connection callback: called when connection is made
    def connection_made(self, transport):
        # ref. 18.5.4.1.1. BaseTransport
        # 'peername': the remote address to which the socket is connected
        peername = transport.get_extra_info('peername')
        logger.info('New connection from {}'.format(peername))
        self.transport = transport
    # ref. 18.5.4.2.3. Transports & protocols - Streaming protocols
    # streaming callback: called when some data is received
    def data_received(self, data):
        msg = data.decode()
        logger.info('Message received: {!r}'.format(msg))
        tokens = msg.split()
        cmd = tokens[0]
        args = tokens[1:]
        
        if cmd == 'IAMAT' and self.valid_IAMAT(args):
            res = self.IAMAT(tokens[1], tokens[2], tokens[3]) + '\n'
        elif cmd == 'AT':
            res = self.AT(tokens[3], msg)
        elif cmd == 'WHATSAT' and self.valid_WHATSAT(args):
            self.WHATSAT(tokens[1], tokens[2], tokens[3])
            return
        else:
            res = '? ' + msg + '\n' # invalid cmd

        send(self.transport, res)
        drop(self.transport)
    #########################    
    ## 'tsunami' algorithm ##
    #########################
    # ref. Flooding (computer networking)
    # https://en.wikipedia.org/wiki/Flooding_%28computer_networking%29
    def flooding_route(self, msg):
        origin = msg.split()[5:]
        for serverID in self.pattern: 
            if serverID not in origin: # except itself, or inf loop
                self.propagate(serverID, config.PORTS[serverID], msg)
    def propagate(self, serverID, port, msg):
        coro = loop.create_connection(lambda:
                                      ProxyClientProtocol(msg, serverID),
                                      config.LOCALHOST, port)
        loop.create_task(coro)
    ######################
    ## validity checker ##
    ######################
    def valid_location(self, location, clientID):
        try:
            temp_latitude, temp_longitude = self.parse_location(location)
            latitude, longitude = float(temp_latitude), float(temp_longitude)
        except ValueError:
            return False

        if not (latitude < 90 and latitude > -90):
            return False
        if not (longitude < 180 and latitude > -180):
            return False
        return True
    def valid_time(self, temp_time):
        try:
            time = float(temp_time)
            datetime.datetime.utcfromtimestamp(time)
        except ValueError:
            return False
        return True
    # IAMAT <clientID> <location> <time_sent>
    def valid_IAMAT(self, arguments):
        clientID = arguments[0]
        location = arguments[1]
        time_sent = arguments[2]
        if len(arguments) != 3:
            logger.error('Invalid number of arguments for IAMAT')
            return False
        if not self.valid_time(time_sent):
            logger.error('Invalid Unix time for IAMAT')
            return False
        if not self.valid_location(location, clientID):
            logger.error('Invalid ISO-6709 location for IAMAT')
            return False
        return True
    # WHATSAT <clientID> <radius> <bound>
    def valid_WHATSAT(self, arguments):
        clientID = arguments[0]
        radius = arguments[1]
        bound = arguments[2]
        try:
            ProxyServerProtocol.clients[arguments[0]]
        except KeyError:
            logger.error('Location was not sent(IAMAT first)')
            return False
        try:
            f_radius = float(arguments[1])
            i_bound = int(arguments[2])
        except ValueError:
            logger.error('Invalid data type for radius/bound')
            return False
        if (len(arguments) != 3):
            logger.error('Invalid number of args for WHATSAT')
            return False
        if not(f_radius < 50 and f_radius > 0):
            logger.error('Radius must be in-between 0-50 km')
            return False
        if not(i_bound < 20 and i_bound > 0):
            logger.error('Bound must be in-between 0-20')
            return False
        return True
    ####################
    ## core: response ##
    ####################
    # communication of servers eachother
    def AT(self, clientID, msg):
        host = msg.split()[-1]
        peername = self.transport.get_extra_info('peername')
        logger.info('{} propagated message to {}'.format(peername, host))

        # Update client's AT stamp
        stamp = ' '.join(msg.split()[:6])
        self.update_info(clientID, stamp)

        flood_msg = msg + ' {}'.format(self.server_name)
        self.flooding_route(flood_msg)
        res = '{} received updated location'.format(self.server_name)

        return res
    def get_location(self, clientID):
        temp_location = ProxyServerProtocol.clients[clientID].split()[4]
        location = self.parse_location(temp_location)
        return location
    # AT <serverID> <time_diff> <clientID> <location> <time_stamp>
    def IAMAT(self, clientID, location_str, time_str):
        time_diff = time.time() - float(time_str)
        time_diff_str = '{:.9f}'.format(time_diff)
        if time_diff > 0:
            time_diff_str = '+' + time_diff_str
        elif time_diff < 0: # negative time due to clock skew
            time_diff_str = '-' + time_diff_str

        stamp = 'AT {} {} {} {} {}'.format(self.server_name,
                                           time_diff_str,
                                           clientID, location_str, time_str)
        if self.update_info(clientID, stamp):
            self.flooding_route(stamp + ' ' + self.server_name)

        return ProxyServerProtocol.clients[clientID]
    def update_info(self, clientID, info):
        if info.split()[3] != clientID:
            return False
        updated = False
        try:
            if self.parse_time(info) > self.parse_time(ProxyServerProtocol.clients[clientID]):
                ProxyServerProtocol.clients[clientID] = info
                updated = True
        except KeyError:
            ProxyServerProtocol.clients[clientID] = info
            updated = True
        if updated:
            logger.info('Location updated for {}'.format(clientID))
        
        return updated
    # ref. 5.1.2. Request-URI
    # https://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html
    # request-URI = "*" | absoluteURI | abs_path | authority
    # absoluteURI: GET http://www.w3.org/pub/WWW/TheProject.html HTTP/1.1
    # most common from: GET /pub/WWW/TheProject.html HTTP/1.1
    #                   Host: www.w3.org
    def WHATSAT(self, clientID, radius_in_km, info_bound):
        ''' aiohttp version -- failed to embed 
        location = self.get_location(clientID)
        latitude = location[0]
        longitude = location[1]
        radius = float(radius_km) * 1000
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%s,%s&radius=%d&key=%s' % (latitude, longitude, radius, config.API_KEY)

        async with aiohttp.ClientSession() as session:
            json_res = await fetch(session, url)
            json_res['results'] = json_res['results'][:info_bound]
            res = json_res(json_res, indent=3)
        final_res = self.parse_json(res)

        return final_res
        '''

        latitude = self.get_location(clientID)[0]
        longitude = self.get_location(clientID)[1]
        radius = float(radius_in_km) * 1000
        request = 'GET '+ config.API_TARGET + config.API_FORMAT +\
                  'location=%s,%s&radius=%d&key=%s HTTP/1.1\n' %\
                  (latitude, longitude, radius, config.API_KEY) +\
                  'Host: %s\n\n' % config.API_HOST 
        ##print('HERE:\n' + request)

        # ref. 17.3 ssl - TLS/SSL wrapper for socket objects
        # https://docs.python.org/2/library/ssl.html
        # returns a new SSLContext obj with default settings
        context = ssl.create_default_context()
        # whether to match the peer cert's hostname with 
        context.check_hostname = False
        # whether to try to verify other peers' certificates and
        # how to behave if verification fails.
        # CERT_NONE: no certificates will be required
        context.verify_mode = ssl.CERT_NONE

        protocol = lambda: HTTPProtocol(request, self.transport,
                                        int(info_bound),
                                        ProxyServerProtocol.clients[clientID])

        logger.info('Request sent: ' + request)
        coro = loop.create_connection(protocol, config.API_HOST,
                                      config.API_PORT, ssl=context)
        loop.create_task(coro)
        
class ProxyClientProtocol(asyncio.Protocol):
    def __init__(self, msg, serverID):
        self.msg = msg
        self.server_name = serverID
    def connection_made(self, transport):
        logger.info('Connected to server {}'.format(self.server_name))
        self.transport = transport
        self.transport.write(self.msg.encode())
        logger.info('Propagated location to {}'.format(self.server_name))
    def connection_lost(self, exc):
        self.transport.close()
        logger.info('Dropped connection to server {}'.format(self.server_name))

class HTTPProtocol(asyncio.Protocol):
    def __init__(self, request, rtransport, bound, header):
        self.request = request
        self.bound = bound
        self.header = header
        self.rtransport = rtransport
        self.eof_counter = 0
        self.resp = ''
    def rsend(self, transport, message):
        resp = self.parse_json(message)
        send(transport, resp)
        drop(transport)
        transport.close()
    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(self.request.encode())
    def data_received(self, data):
        eof = '\r\n\r\n'
        self.resp += data.decode()
        self.eof_counter += data.decode().count(eof)
        if (self.eof_counter >= 2):
            self.rsend(self.rtransport, self.resp)
    def parse_json(self, data):
        rhs = data.split('\r\n\r\n')[1]
        s_label = rhs.index('{')
        e_label = rhs.rindex('}')
        temp = rhs[s_label:e_label + 1]
        res = temp.strip().replace('\r\n', '').replace('\n', '')

        json_res = json.loads(res)
        if len(json_res['results']) > self.bound:
            json_res['results'] = json_res['results'][:self.bound]
        resp = self.header + '\n' + json.dumps(json_res, indent=3) + '\n\n'

        return resp

def send(transport, message):
    transport.write(message.encode())
    logger.info('Response sent: {!r}'.format(message))
def drop(transport):
    transport.close()
    peername = transport.get_extra_info('peername')
    logger.info('Dropped connection from {}'.format(peername))
    
def main():
    # check the number of input arguments
    if (len(sys.argv) != 2):
        print('Error: specify serverID')
        sys.exit(1)
    # check serverID
    global serverID
    serverID = sys.argv[1]
    if not serverID in config.SERVER_IDS:
        print('Error: invalid serverID')
        sys.exit(1)
    port = config.PORTS[serverID]
    # set up logging
    global logger
    logger = logging.getLogger(serverID)
    formatter = logging.Formatter( # <time>/<level>-<serverID> : <log>
        '%(asctime)s/%(levelname)s-%(name)s : %(message)s')
    destination = './' + serverID + '.log' # *.log in current dir
    ## for outputing in .log file
    file_handler = logging.FileHandler(destination, mode='w')
    file_handler.setFormatter(formatter)
    ## for console log
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(20) # INFO level
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    # ref. 18.5.4.3.2 TCP echo server protocol
    # https://docs.python.org/3/library/asyncio-protocol.html#asyncio-protocol
    # start server
    global loop
    loop = asyncio.get_event_loop()
    coro = loop.create_server(lambda: ProxyServerProtocol(serverID),
                              config.LOCALHOST, port)
    server = loop.run_until_complete(coro)
    # serve requests utill Ctrl+C is pressed
    logger.info('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Closing server ...')

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

    
if __name__ == '__main__':
    main()
