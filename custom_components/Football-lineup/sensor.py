from datetime import timedelta
import requests
import logging
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Football Lineup'
SCAN_INTERVAL = timedelta(minutes=120)  # Set the update interval to 120 minutes

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    api_key = config.get(CONF_API_KEY)
    name = config.get(CONF_NAME)

    add_entities([FootballLineupSensor(api_key, name)], True)

class FootballLineupSensor(Entity):
    def __init__(self, api_key, name):
        self._api_key = api_key
        self._name = name
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    def update(self):
        fixture_id = self._get_latest_fixture_id()
        if fixture_id:
            self._get_lineup(fixture_id)

    def _get_latest_fixture_id(self):
        url = "https://v3.football.api-sports.io/fixtures/?season=2023&league=140&team=529&last=1"
        headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': self._api_key
        }
        _LOGGER.debug("Fetching latest fixture ID for Barcelona")
        response = requests.get(url, headers=headers)
        data = response.json()
        _LOGGER.debug("Response data: %s", data)
        if data['response']:
            return data['response'][0]['fixture']['id']
        return None

    def _get_lineup(self, fixture_id):
        url = f"https://v3.football.api-sports.io/fixtures/lineups?fixture={fixture_id}"
        headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': self._api_key
        }
        _LOGGER.debug("Fetching lineup for fixture ID: %s", fixture_id)
        response = requests.get(url, headers=headers)
        data = response.json()
        _LOGGER.debug("Lineup response data: %s", data)
        if data['response']:
            for team in data['response']:
                if team['team']['id'] == 529:  # Filter for Barcelona team ID
                    lineup_data = team
                    self._state = f"{lineup_data['team']['name']} lineup"

                    self._attributes = {
                        'coach': lineup_data['coach']['name'],
                        'formation': lineup_data['formation'],
                        'starting XI': [
                            {
                                'name': player['player']['name'],
                                'ID': player['player']['id'],
                                'position': player['player']['pos'],
                                'number': player['player']['number'],
                           	'grid': player['player']['grid']  # Include the grid position
                            }
                            for player in lineup_data['startXI']
                        ],
                        'substitutes': [
                            {
                                'name': sub['player']['name'],
                                'ID': sub['player']['id'],
                                'position': sub['player']['pos'],
                                'number': sub['player']['number'],
                            	'grid': sub['player'].get('grid', None)  # Include grid if available
                            }
                            for sub in lineup_data['substitutes']
                        ]
                    }
                    break
