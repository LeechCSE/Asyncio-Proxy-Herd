# Proxy-herd
###### Originally from CS 131: Programming Languages, Spring 2018(Remastered with [Spring 2021 version](https://web.cs.ucla.edu/classes/spring21/cs131/hw/pr.html))
**Proxy-herd** project simulates a set of proxy servers that cache the information 
of clients and communicate not only with clients but also internally not only 
with clients. The inter-server communication guarantees redundancy and 
reliability of the server system. Caching the same information of clients into 
multiple servers, the servers can server clients consistently even if one or more 
server goes down accidently as long as one is survived. In addition, the 
performance would also increase if the data from the web is cached. In fact, 
caching output of the client request prevents servers from repeatively requesting
the same or similar request.  

The target clients are mobile devices with IP addresses and DNS names; therefore,
the servers take TCP connections. The remarkable characteristic of mobile devices
is that they frequently broadcast their GPS locations. In order to process the
frequently-updating information of clients, [asyncio](https://docs.python.org/3/library/asyncio.html) asynchronous networking library is used. It allows the servers concurrently 
process the requests that come simultaneously. More specifically, a request
that takes a long time doesn't block the other requests; first done, first out.  

In order to simulate the role of proxy server, the servers serve [Google Places
Nearby Search](https://developers.google.com/maps/documentation/places/web-service/search-nearby) 
requests.

## Structure
There are five servers connected to each other as the following:
```
                   +--------+       +---------+
            -------| Jaquez |-------| Bernard |            
+-------+   |      +--------+ \   / +---------+
| Riley |----                   X        |
+-------+   |      +--------+ /   \ +----------+
            -------| Juzang |-------| Campbell | 
                   +--------+       +----------+
```
The servers accept TCP connections from clients. Clients can access to any 
server of them(Let's call it *origin server*). The updated information of the 
clients are automatically propagated through the neighbor servers of the 
*origin server*, using inter-server communication with 
[flooding algorithm](https://en.wikipedia.org/wiki/Flooding_%28computer_networking%29).\
For example, a client reaches `Riley` and updates its location. Then, the
client information is propagated into `Jaquez` and `Juzang` and again into 
`Bernard` and `Campbell`. 

## Key features
- Inter-server communication for realiablity and performance
- Asynchronous process of requests
- Logging system of each server

## Requirements
- Python 3.7+
- [aiohttp](https://docs.aiohttp.org/en/stable/)

## How to use

#### Run servers
```
python server.py Riley &
python server.py Jaquez &
python server.py Juzang &
python server.py Campbell &
python server.py Bernard &
```

#### Query
`IAMAT client_id location time_stamp`  
`IAMAT` query updates client's location in 
[ISO 6709](https://en.wikipedia.org/wiki/ISO_6709) notation is updated with the
current time, expressed in [POSIX time](https://en.wikipedia.org/wiki/Unix_time)

`WHATSAT client_id radius upper_bound`  
`WHATSAT` query initiates Google Places Nearby Search of the points of interest
up to *upper_bound* numbers from the current location of the client within 
*radius* km. 

#### Expected response

**`AT` Query**  

`AT server_name response_delay client_id location time_stamp`  
The server which recieved the `IAMAT` query responds its `server_name` with 
`AT` message header followed by `response_delay`, which represents the time
difference between query and response moments, and the copy of client information.

**`WHATSAT` Query**
```
AT server_name response_delay client_id location time_stamp
{
   "html_attributions": [],
   ...
   "results": [
      {
         "geometry": {
         ...
   ],
   "status": "OK"
}
```
The first line of response is the same as the one of `AT` query. The following
is the JSON-format Google Places Nearby Search response.