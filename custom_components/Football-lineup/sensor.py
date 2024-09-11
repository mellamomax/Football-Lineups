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
        url = "https://v3.football.api-sports.io/fixtures/?season=2024&league=140&team=529&last=1"
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
        response = requests.get(url, headers=headers)
        data = response.json()
        
        fixture_info = self._get_fixture_info(fixture_id)  # Get team names and fixture details
        
        if data['response']:
            home_team_lineup = {}
            away_team_lineup = {}
            
            for team in data['response']:
                if team['team']['id'] == fixture_info['home_team_id']:  # Check if team is home
                    home_team_lineup = {
                        'coach': team['coach']['name'],
                        'formation': team['formation'],
                        'starting XI': [
                            {
                                'name': player['player']['name'],
                                'ID': player['player']['id'],
                                'position': player['player']['pos'],
                                'number': player['player']['number'],
                                'grid': player['player']['grid']  # Include the grid position
                            }
                            for player in team['startXI']
                        ],
                        'substitutes': [
                            {
                                'name': sub['player']['name'],
                                'ID': sub['player']['id'],
                                'position': sub['player']['pos'],
                                'number': sub['player']['number'],
                                'grid': sub['player'].get('grid', None)
                            }
                            for sub in team['substitutes']
                        ]
                    }
                elif team['team']['id'] == fixture_info['away_team_id']:  # Check if team is away
                    away_team_lineup = {
                        'coach': team['coach']['name'],
                        'formation': team['formation'],
                        'starting XI': [
                            {
                                'name': player['player']['name'],
                                'ID': player['player']['id'],
                                'position': player['player']['pos'],
                                'number': player['player']['number'],
                                'grid': player['player']['grid']
                            }
                            for player in team['startXI']
                        ],
                        'substitutes': [
                            {
                                'name': sub['player']['name'],
                                'ID': sub['player']['id'],
                                'position': sub['player']['pos'],
                                'number': sub['player']['number'],
                                'grid': sub['player'].get('grid', None)
                            }
                            for sub in team['substitutes']
                        ]
                    }

            # Combine home and away team info into the attributes
            self._state = f"{fixture_info['home_team']} vs {fixture_info['away_team']} lineups"
            self._attributes = {
                'home_team': fixture_info['home_team'],
                'home_team_lineup': home_team_lineup,
                'away_team': fixture_info['away_team'],
                'away_team_lineup': away_team_lineup,
                'fixture_date': fixture_info['date'],
            }

                    
                    
    def _get_fixture_info(self, fixture_id):
        url = f"https://v3.football.api-sports.io/fixtures/?id={fixture_id}"
        headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': self._api_key
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        if data['response']:
            fixture = data['response'][0]
            return {
                'home_team': fixture['teams']['home']['name'],
                'home_team_id': fixture['teams']['home']['id'],
                'away_team': fixture['teams']['away']['name'],
                'away_team_id': fixture['teams']['away']['id'],
                'date': fixture['fixture']['date']
            }
        return None
