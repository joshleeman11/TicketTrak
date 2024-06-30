from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import pandas as pd

# Set up the WebDriver with headless option
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

def gameTickets(game):
    try:
        print(game)
        driver.get(game)

        # Increase wait time to 20 seconds
        wait = WebDriverWait(driver, 20)
        
        # # Wait for "See more" button to be clickable and click it
        # see_more_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'See more')]")))
        # see_more_button.click()

        # Scroll down and click "See more" button multiple times
        scroll_count = 5
        for _ in range(scroll_count):
            try:

                # Scroll to the bottom of the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                time.sleep(2)  # Wait for new content to load
                
                # Refresh event_section reference
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                ticket_section = soup.find("div", id="listings-container")

            except TimeoutException:
                print("Timeout waiting for 'See more' button.")
                break

        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Find the section with the specific class name
        all_tickets = ticket_section.find_all("div", class_="sc-57jg3s-0 uNHdb")

        if all_tickets:
            
            sections = []
            rows = []
            seats = []
            prices = []
            
            for ticket in all_tickets:
                section_row = ticket.get_text(separator=' | ').split(' | ')
                sold = next((element for element in section_row if element.startswith('Sold')), None)
                if (len(section_row) > 1 and not sold):
                    
                    section = sold = next((element for element in section_row if element.startswith('Section')), None)
                    row = next((element for element in section_row if element.startswith('Row')), None)
                    seat = next((element for element in section_row if element.startswith('Seat')), None) or 1
                    price = next((element for element in section_row if element.startswith('$')), None)
                
                    sections.append(section)
                    rows.append(row)
                    seats.append(seat)
                    prices.append(price)
            
            df = pd.DataFrame({
                'Section': sections,
                'Row': rows,
                'Seats': seats,
                'Price': prices
            })
            print(df)
            print("\n")
        else:
            print("Ticket section not found.")
        
        return df

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()
