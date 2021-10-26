# Google Maps Platform API info.
API_KEY = 'HIDDEN'
# given server list
SERVER_IDS = ['Riley', 'Jaquez', 'Juzang', 'Campbell', 'Bernard']
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
