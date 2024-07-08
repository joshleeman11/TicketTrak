import requests
import pandas as pd

def fetch_stubhub_tickets(gameUrl, currentPage, team, date, minPrice = 0, maxPrice = 100000, quantity = 2):
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.stubhub.com',
        'priority': 'u=1, i',
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
        "Quantity": quantity,
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
        "PriceOption": f"1,{minPrice},{maxPrice}",
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
        links = []
        for item in items:
            id = item.get('id')
            if id < 0:
                continue
            
            sections.append(item.get('section', ' '))
            teams.append(team)
            dates.append(date)
            rows.append(item.get('row', ' '))
            prices.append(item.get('priceWithFees', ' '))
            seats.append(f'{item.get("seatFrom", " ")} - {item.get("seatTo", " ")}')
            links.append(f'{gameUrl}/?quantity=&listingId={id}')
        
        df = pd.DataFrame({
            'Teams': teams,
            'Dates': dates,
            'Section': sections,
            'Row': rows,
            'Price': prices,
            'Seats': seats,
            'Link': links
        })
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error executing curl command: {e}")