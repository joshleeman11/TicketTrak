import http
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
from multiprocessing import Pool
from TicketScrape import gameTickets

# Set up the WebDriver with headless option
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)
    
def scroll_and_load(driver, scroll_count = 5):
    for _ in range(scroll_count):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

def extract_event_links(driver):
    driver.get("https://www.stubhub.com/new-york-mets-tickets/performer/5649")
    scroll_and_load(driver)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    event_section = soup.find("ul", class_="sc-1u6ezo7-1 jFZzcj")

    if event_section:
        # Finding all <a> tags within that section
        event_links = event_section.find_all("a", href=True)
        game_links = [link['href'] for link in event_links]
        
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
    game_link, away_team, home_team, game_date = args
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
            
            for ticket in all_tickets:
                ticket_info = ticket.get_text(separator=' | ').split(' | ')
                sold = next((element for element in ticket_info if element.startswith('Sold')), None)
                if (len(ticket_info) > 1 and not sold):
                    section = sold = next((element for element in ticket_info if element.startswith('Section')), None)
                    row = next((element for element in ticket_info if element.startswith('Row')), None)
                    seat = ticket_info[3]
                    price = next((element for element in ticket_info if element.startswith('$')), None)
                
                    sections.append(section)
                    rows.append(row)
                    seats.append(seat)
                    prices.append(price)
            
            df = pd.DataFrame({
                'Game Date': game_date,
                'Section': sections,
                'Row': rows,
                'Seats': seats,
                'Price': prices,
                'Away Team': away_team,
                'Home Team': home_team
            })
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

    

def main():
    driver = setup_driver()
    try:
        game_links, away_teams, home_teams, game_dates = extract_event_links(driver)
        full_urls = [f'https://www.stubhub.com{game}' for game in game_links]
        
        game_info = list(zip(full_urls, away_teams, home_teams, game_dates))
        with Pool() as pool:
            all_games = []
            for game in pool.imap_unordered(gameTickets, game_info):
                all_games.append(game)
            if all_games:
                final_df = pd.concat(all_games, ignore_index=True)
                print(final_df)
            else:
                print("No games found")
    except Exception as e:
        print(e)
    finally:
        driver.quit()
        
if __name__ == "__main__":
    main()
