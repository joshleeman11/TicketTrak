import json
import requests

def fetch_stubhub_games():
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-length': '0',
        'content-type': 'application/json',
        'origin': 'https://www.stubhub.com',
        'priority': 'u=1, i',
        'referer': 'https://www.stubhub.com/new-york-mets-tickets/performer/5649',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
    }
    base_url = 'https://www.stubhub.com/new-york-mets-tickets/performer/5649'
    query_parameters = {
        "gridFilterType": 0,
        "homeAwayFilterType": 0,
        "sortBy": 0,
        "nearbyGridRadius": 50,
        "venueIdFilterType": 0,
        "eventViewType": 0,
        "opponentCategoryId": 0,
        "method": "GetFilteredEvents",
        "categoryId": 5273,
        "radiusFrom": 0,
        "radiusTo": 80467,
        "from": "2024-07-06T03:08:53.529Z",
        "to": "9999-12-31T23:59:59.999Z",
        "lat": 40.713,
        "lon": -74.006,
        "genreId": "undefined",
        "eventCountryType": 0,
        "fromPrice": "undefined",
        "toPrice": "undefined"
    }
    games = []
    for i in range(1, 5):
        query_parameters['pageIndex'] = i
        response = requests.post(base_url, headers=headers, params=query_parameters)
        
        if response.status_code == 200:
            try:
                data = response.json()
                items = data.get('items', [])
                for item in items:
                    url = item.get('url')
                    name = item.get('name')
                    date = item.get('formattedDate')
                    games.append((url, name, date))
            except json.JSONDecodeError:
                print(f"Failed to decode JSON response for page index {i}")
        else:
            print(f"Error fetching data for page index {i}: {response.status_code}")
    return games