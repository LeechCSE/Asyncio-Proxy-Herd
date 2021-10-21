# Google Maps Platform API info.
API_KEY = 'HIDDEN'
API_TARGET = '/maps/api/place/nearbysearch/'
API_FORMAT = 'json?'
API_HOST = 'maps.googleapis.com'
API_PORT = 443 # https: 443 / http: 80 for Google Maps Platform services
# given server list
SERVER_IDS = ['Goloman', 'Hands', 'Holiday', 'Welsh', 'Wilkes']
# bidirectional communication pattern
COMMUNICATION_PATTERN = {
    'Riley': ['Jaquez', 'Juzang'],
    'Jaquez': ['Riley', 'Bernard'],
    'Juzang': ['Riley', 'Bernard', 'Campbell'],
    'Campbell': ['Bernard', 'Juzang'],
    'Bernard': ['Jaquez', 'Juzang', 'Campbell']
}
# assigned ports
PORTS = {}
PORTS['Riley'] = 11645
PORTS['Jaquez'] = 11646
PORTS['Juzang'] = 11647
PORTS['Campbell'] = 11648
PORTS['Bernard'] = 11649

LOCALHOST = '127.0.0.1'
