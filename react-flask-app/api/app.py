from flask import Flask, jsonify, request, json
from dotenv import load_dotenv
from datetime import datetime
import os
from flask_cors import CORS
import requests
import time
import pandas as pd
from StubHub.EventScrape import fetch_stubhub_games
from StubHub.TicketScrape import fetch_stubhub_tickets

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

game_urls_cache = {
    'urls': None,
    'timestamp': None
}

CACHE_TTL = 60 * 60

def get_cached_game_urls():
    current_time = time.time()
    if game_urls_cache['urls'] and (current_time - game_urls_cache['timestamp'] < CACHE_TTL):
        return game_urls_cache['urls']
    else:
        game_urls = fetch_stubhub_games()
        game_urls_cache['urls'] = game_urls
        game_urls_cache['timestamp'] = current_time
        return game_urls
    
def fetch_game_urls():
    return fetch_stubhub_games()

def fetch_tickets_game(gameUrl, currentPage, team, date, minPrice, maxPrice, quantity):
    return fetch_stubhub_tickets(gameUrl, currentPage, team, date, minPrice, maxPrice, quantity)

@app.route("/nextPage", methods=["GET", "POST", "OPTIONS"])
def nextPage():
    if request.method == 'POST':
        data = request.json
        print(data)
        nextPage = data.get("pageIndex")
        dates = data.get("dates")
        
        games = get_cached_game_urls()
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
                    df.append(fetch_tickets_game(f'https://www.stubhub.com{game[0]}', nextPage, team, date))
            final_df = pd.concat(df, ignore_index=True)
            return jsonify(final_df.to_json(orient="records"))
        else:
            return jsonify({"message": "not get"})

@app.route("/search", methods=["GET","POST", "OPTIONS"])
def main_route():
    if request.method == 'POST':
        data = request.json
        print(data)
        dates = data.get("dates")
        minPrice = data.get("minPrice", 0)
        maxPrice = data.get("maxPrice", float('inf'))
        quantity = data.get("quantity", 2)
        print(f"Received parameters - dates: {dates} quantity: {quantity}, min_price: {minPrice}, max_price: {maxPrice}")
        
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
                    df.append(fetch_tickets_game(f'https://www.stubhub.com{game[0]}', 1, team, date, minPrice, maxPrice, quantity))
            final_df = pd.concat(df, ignore_index=True)
            return jsonify(final_df.to_json(orient="records"))
        else:
            return jsonify({"message": "not get"})

if __name__ == "__main__":
    app.run()
