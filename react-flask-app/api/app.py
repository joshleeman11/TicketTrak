from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
from flask_cors import CORS
import http
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from multiprocessing import Pool

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


# Set up the WebDriver with headless option
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def scroll_and_load(driver, scroll_count=5):
    try:
        # Locate and click the first "See More" button
        see_more_button = driver.find_element(By.CLASS_NAME, "sc-6f7nfk-0 coJOSI sc-1u6ezo7-7 ewQWpR")
        if see_more_button:
            driver.execute_script("arguments[0].click();", see_more_button)
            time.sleep(2)
    except Exception as e:
        print("Error clicking 'See More' button:", e)

    for _ in range(scroll_count):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Check if the first "See More" button is still present
        try:
            see_more_button = driver.find_element(By.CLASS_NAME, "sc-6f7nfk-0 coJOSI sc-1u6ezo7-7 ewQWpR")
            if not see_more_button.is_displayed():
                print("No more 'See More' buttons visible.")
                break  # Exit the loop if the first button is no longer visible
        except Exception as e:
            print("Error checking 'See More' button visibility:", e)



def extract_event_links(driver):
    driver.get("https://www.stubhub.com/new-york-mets-tickets/performer/5649")
    scroll_and_load(driver)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    event_section = soup.find("ul", class_="sc-1u6ezo7-1 jFZzcj")

    if event_section:
        # Finding all <a> tags within that section
        event_links = event_section.find_all("a", href=True)
        game_links = [link["href"] for link in event_links]

        # Finding each away and home team
        all_game_teams = event_section.find_all("div", class_="sc-1mafo1b-2 bIhILW")
        away_teams = []
        home_teams = []

        for game_teams in all_game_teams:
            teams_text = game_teams.get_text()
            away_team, home_team = teams_text.split(" at ")
            away_teams.append(away_team.strip())
            home_teams.append(home_team.strip())

        # Finding date and time
        all_dates = event_section.find_all("time")
        game_dates = []
        for dateTime in all_dates:
            dateTime_text = dateTime.get_text()
            game_dates.append(dateTime_text)

        return game_links, away_teams, home_teams, game_dates

    else:
        print("Event section not found.")
        return [], [], [], []


def gameTickets(args):
    game_link, game_date = args
    print(game_link)
    driver = setup_driver()

    try:
        driver.get(game_link)
        scroll_and_load(driver)

        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        tickets = soup.find("div", id="listings-container")

        all_tickets = tickets.find_all("div", class_="sc-57jg3s-0 uNHdb")

        if all_tickets:

            sections = []
            rows = []
            seats = []
            prices = []
            id = []

            for ticket in all_tickets:
                
                id_element = ticket.find("div", {"data-listing-id": True})
                if id_element:
                    data_listing_id = id_element['data-listing-id'] if id_element else None
                    if not data_listing_id.startswith("-"):
                        print(data_listing_id)
                        id.append(f'{game_link}&data_listing_id={data_listing_id}')
                
                ticket_info = ticket.get_text(separator=" | ").split(" | ")
                sold = next(
                    (element for element in ticket_info if element.startswith("Sold")),
                    None,
                )
                if len(ticket_info) > 1 and not sold:
                    section = sold = next(
                        (
                            element
                            for element in ticket_info
                            if element.startswith("Section")
                        ),
                        None,
                    )
                    row = next(
                        (
                            element
                            for element in ticket_info
                            if element.startswith("Row")
                        ),
                        None,
                    )
                    seat = ticket_info[3]
                    price = next(
                        (element for element in ticket_info if element.startswith("$")),
                        None,
                    )
                    
                    sections.append(section)
                    rows.append(row)
                    seats.append(seat)
                    prices.append(price)
            print(len(prices))
            print(len(id))
            df = pd.DataFrame(
                {
                    "Game Date": game_date,
                    "Section": sections,
                    "Row": rows,
                    "Seats": seats,
                    "Price": prices,
                    "Link": id
                }
            )
            print(df)
            print("\n")
            return df
        else:
            print("Ticket section not found.")
            return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()


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
        
        driver = setup_driver()
        try:
            game_links, away_teams, home_teams, game_dates = extract_event_links(driver)
            full_urls = [f'https://www.stubhub.com{game}' for game in game_links]
            print(full_urls)
            game_info = list(zip(full_urls, away_teams, home_teams, game_dates))
            print(game_info)
            # with Pool() as pool:
            #     all_games = []
            #     for game in pool.imap_unordered(gameTickets, game_info):
            #         all_games.append(game)
            #     if all_games:
            #         final_df = pd.concat(all_games, ignore_index=True)
            #         json_df = final_df.to_json(orient='records')
            #         print(json_df)
            #         return jsonify(json_df)
            #     else:
            #         return jsonify({"error": "No games found"})
            
            # game_info = []
            # for date in dates:
            #     game_info.append((f'https://www.stubhub.com/new-york-mets-flushing-tickets-{date}/event/152162324/?quantity={quantity}&priceOption=1,{min_price},{max_price}', date))
            # df = []
            # for info in game_info:
            #     df.append(gameTickets(info))
            # final_df = pd.concat(df, ignore_index=True)
            # data_store.set_dataframe(final_df)

            # return jsonify(final_df.to_json(orient="records"))
        except Exception as e:
            print(e)
            return e
        finally:
            driver.quit()
    else:
        return jsonify({"message": "not get"})

if __name__ == "__main__":
    app.run()
