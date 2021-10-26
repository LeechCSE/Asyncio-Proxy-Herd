# Proxy-herd
###### Originally from CS 131: Programming Languages, Spring 2018
---

## Background

## Structure

## Key features

## Requirements
- Python 3.7+
- [aiohttp](https://docs.aiohttp.org/en/stable/)

## How to use

#### Run servers
```
python3 server.py Riley &
python3 server.py Jaquez &
python3 server.py Juzang &
python3 server.py Campbell &
python3 server.py Bernard &
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