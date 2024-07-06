from flask import Flask, jsonify, request, json
from dotenv import load_dotenv
from datetime import datetime
import os
from flask_cors import CORS
import requests
import pandas as pd

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG")


class DataStore:
    def __init__(self):
        self.dataframe = None

    def set_dataframe(self, dataframe):
        self.dataframe = dataframe

    def get_dataframe(self):
        return self.dataframe


data_store = DataStore()


def fetch_game_urls():
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

def fetch_tickets_game(gameUrl, currentPage, team, date):
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.stubhub.com',
        'priority': 'u=1, i',
        'referer': 'https://www.stubhub.com/new-york-mets-flushing-tickets-7-9-2024/event/152162310/?quantity=2',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    payload = {
        "ShowAllTickets": True,
        "HideDuplicateTicketsV2": False,
        "Quantity": 2,
        "PageVisitId": "483C6BDF-C53D-499A-B200-CA4030920263",
        "PageSize": 20,
        "CurrentPage": currentPage,
        "SortBy": "NEWPRICE",
        "SortDirection": 0,
        "Sections": "",
        "Rows": "",
        "ListingNotes": "",
        "PriceRange": "0,100",
        "EstimatedFees": False,
        "BetterValueTickets": True,
        "PriceOption": "",
        "HasFlexiblePricing": False,
        "ExcludeSoldListings": False,
        "RemoveObstructedView": False,
        "NewListingsOnly": False,
        "PriceDropListingsOnly": False,
        "SelectBestListing": False,
        "ConciergeTickets": False,
        "Method": "IndexSh"
    }
        
    try:
        response = requests.post(gameUrl, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        items = data.get('items', [])
        teams = []
        dates = []
        sections = []
        rows = []
        prices = []
        seats = []
        for item in items:
            if item.get('soldXTimeAgoSiteMessage'):
                continue
            
            sections.append(item.get('section', ' '))
            teams.append(team)
            dates.append(date)
            rows.append(item.get('row', ' '))
            prices.append(item.get('price', ' '))
            seats.append(f'{item.get("seatFrom", " ")} + {item.get("seatTo", " ")}')
        
        df = pd.DataFrame({
            'Teams': teams,
            'Dates': dates,
            'Section': sections,
            'Row': rows,
            'Price': prices,
            'Seats': seats
        })
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error executing curl command: {e}")


@app.route("/search", methods=["GET","POST", "OPTIONS"])
def main_route():
    if request.method == 'POST':
        data = request.json
        print(data)
        dates = data.get("dates")
        quantity = data.get("quantity")
        min_price = data.get("minPrice")
        max_price = data.get("maxPrice")
        print(f"Received parameters - dates: {dates} quantity: {quantity}, min_price: {min_price}, max_price: {max_price}")
        
        games = fetch_game_urls()
        if len(games) > 0:
            df = []
            month_map = {
                'Jan': '1', 'Feb': '2', 'Mar': '3', 'Apr': '4',
                'May': '5', 'Jun': '6', 'Jul': '7', 'Aug': '8',
                'Sep': '9', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
        
            for game in games:
                print(f"Name: {game[1]}, URL: {game[0]}")
                team = game[1]
                date = game[2]
                
                month, day = date.split()
                if int(day) < 10:
                    day = str(day)[1]
                month_num = month_map[month]
                if f"{month_num}-{day}-2024" in dates:
                    df.append(fetch_tickets_game(f'https://www.stubhub.com{game[0]}', 1, team, date))
            final_df = pd.concat(df, ignore_index=True)
            return jsonify(final_df.to_json(orient="records"))
        else:
            return jsonify({"message": "not get"})

if __name__ == "__main__":
    app.run()
