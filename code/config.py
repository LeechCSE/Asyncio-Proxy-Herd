# Google Maps Platform API info.
API_KEY = 'AIzaSyDnPUEwv54aplon8Q4HHdEGYwTuIrHrroY'
API_TARGET = '/maps/api/place/nearbysearch/'
API_FORMAT = 'json?'
API_HOST = 'maps.googleapis.com'
API_PORT = 443 # https: 443 / http: 80 for Google Maps Platform services
# given server list
SERVER_IDS = ['Goloman', 'Hands', 'Holiday', 'Welsh', 'Wilkes']
# bidirectional communication pattern
COMMUNICATION_PATTERN = {
    'Goloman': ['Hands', 'Holiday', 'Wilkes'],
    'Hands': ['Goloman', 'Wilkes'],
    'Holiday': ['Goloman', 'Welsh', 'Wilkes'],
    'Welsh': ['Holiday'],
    'Wilkes': ['Goloman', 'Hands', 'Holiday']
}
# assigned ports
PORTS = {}
PORTS['Goloman'] = 11645
PORTS['Hands'] = 11646
PORTS['Holiday'] = 11647
PORTS['Welsh'] = 11648
PORTS['Wilkes'] = 11649

LOCALHOST = '127.0.0.1'
