import undetected_chromedriver as uc
import time
import requests
import json
import pandas as pd
import logging
import xmltodict
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FlightCrawler:
    def __init__(self):
        self.base_url = "https://www.klook.com"
        self.api_url = f"{self.base_url}/v3/flightbffserv/search/result"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": self.base_url,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def setup_chrome_options(self) -> uc.ChromeOptions:
        """Setup and return Chrome options."""
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        return chrome_options

    def get_cookies(self, url: str) -> Dict[str, str]:
        """Fetch cookies from the given URL using a headless Chrome browser."""
        driver = uc.Chrome(options=self.setup_chrome_options())
        try:
            driver.get(url)
            time.sleep(10)  # Adjust based on your internet speed
            cookies = driver.get_cookies()
            return {cookie['name']: cookie['value'] for cookie in cookies}
        finally:
            driver.quit()

    def send_api_request(self, api_url: str, headers: Dict[str, str], payload: Dict, cookies: Dict[str, str], date: str) -> Optional[Dict]:
        """Send a POST request to the API and return the response."""
        start_time = time.time()
        try:
            response = requests.post(api_url, headers=headers, json=payload, cookies=cookies, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"{date} - API request failed: {e}")
            return None
        
        elapsed_time = time.time() - start_time
        logging.info(f"{date} - API request completed in {elapsed_time:.2f} seconds.")
        return response.json() if response.text.strip() else None

    def save_data_to_file(self, data: List[Dict], filename: str) -> None:
        """Save data to a JSON file."""
        start_time = time.time()
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            elapsed_time = time.time() - start_time
            logging.info(f"Saving data to {filename} took {elapsed_time:.2f} seconds.")
        except IOError as e:
            logging.error(f"Error saving data to file: {e}")

    def generate_date_range(self, start_date: str, end_date: str) -> List[str]:
        """Generate a list of dates between start_date and end_date."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        date_list = [start + timedelta(days=x) for x in range(0, (end - start).days + 1)]
        return [date.strftime("%Y-%m-%d") for date in date_list]

    def extract_flight_data(self, api_responses: List[Dict]) -> pd.DataFrame:
        """Extract flight data from a list of API responses and return a DataFrame."""
        start_time = time.time()

        flight_data = []

        # Get the current date for crawling_date
        crawling_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Handle empty or invalid API responses
        if not api_responses or not isinstance(api_responses, list):
            logging.warning("No valid API responses provided.")
            return pd.DataFrame(flight_data)

        for api_response in api_responses:
            # Safely extract sections and journey_type
            result = api_response.get("result", {})
            sections = result.get("section", [])
            journey_type = result.get("journey_type", "Unknown")

            for section in sections:
                body = section.get("body", {})
                if not body:
                    continue  # Skip if body is empty

                # Extract airline information
                airline_icons = body.get("airline_icons", [])
                airline_name = airline_icons[0].get("airline_name") if airline_icons else None
                airline_code = airline_icons[0].get("airline") if airline_icons else None

                # Extract itinerary details
                itinerary_detail = body.get("itinerary_detail_param", {})
                search_condition = itinerary_detail.get("search_condition", [{}])[0]
                seat_class = search_condition.get("seat_class")
                passengers = search_condition.get("passengers", [])
                passengers = ", ".join([f"{psg.get('count', 0)} {psg.get('passenger_type', 'unknown')}" for psg in passengers])

                # Extract route and segment details
                routes = itinerary_detail.get("routes", [{}])[0]
                segments = routes.get("segments", [{}])[0]

                # Append flight data to the list
                flight_data.append({
                    "display_origin_position": body.get("display_origin_position"),
                    "display_destination_position": body.get("display_destination_position"),
                    "display_departure_date": body.get("display_departure_date"),
                    "departure_time": body.get("departure_time"),
                    "display_arrival_date": body.get("display_arrival_date"),
                    "arrival_time": body.get("arrival_time"),
                    "display_duration": body.get("display_duration"),
                    "display_price": body.get("display_price"),
                    "amount": body.get("amount"),
                    "airline_name": airline_name,
                    "airline_code": airline_code,
                    "route_duration": routes.get("duration"),
                    "seat_class": seat_class,
                    "journey_type": journey_type,
                    "passengers": passengers,
                    "segment_airline": segments.get("airline"),
                    "segment_flight_num": segments.get("flight_num"),
                    "segment_departure": segments.get("departure"),
                    "segment_departure_date": segments.get("departure_date"),
                    "segment_departure_time": segments.get("departure_time"),
                    "segment_arrival": segments.get("arrival"),
                    "segment_arrival_date": segments.get("arrival_date"),
                    "segment_arrival_time": segments.get("arrival_time"),
                    "segment_duration": segments.get("duration"),
                    "crawling_date": crawling_date
                })
        
        elapsed_time = time.time() - start_time
        logging.info(f"Extracting flight data took {elapsed_time:.2f} seconds.")

        # Return as DataFrame
        return pd.DataFrame(flight_data)

    def get_currency_data(self) -> Optional[Dict[str, float]]:
        """
        Fetch currency exchange rate data from Bank Indonesia's API.
        Returns a dictionary with currency codes as keys and exchange rates as values.
        """
        url = "https://www.bi.go.id/biwebservice/wskursbi.asmx/getSubKursLokal4?startdate=2025-03-05"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                xml_data = response.text
                dict_data = xmltodict.parse(xml_data)
                table_data = dict_data["DataSet"]["diffgr:diffgram"]["NewDataSet"]["Table"]
                
                # Extract currency codes and exchange rates
                currency_data = {
                    item["mts_subkurslokal"]: float(item["jual_subkurslokal"])
                    for item in table_data
                }
                return currency_data
            else:
                logging.error(f"Failed to fetch currency data: HTTP {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching currency data: {e}")
            return None

    def convert_amount_to_idr(self, df: pd.DataFrame, currency_column: str, amount_column: str, currency_data: Dict[str, float]) -> pd.DataFrame:
        """
        Convert the amount in the DataFrame to IDR based on the provided currency data.
        
        :param df: DataFrame containing flight data.
        :param currency_column: Column name containing currency symbols and amounts.
        :param amount_column: Column name containing amounts to convert.
        :param currency_data: Dictionary containing currency exchange rates.
        :return: DataFrame with a new column 'amount_idr'.
        """
        # Mapping for currency symbols to currency codes
        currency_mapping = {
            "HK$": "HKD",  # Hong Kong Dollar
            "US$": "USD",  # US Dollar
            "€": "EUR",    # Euro
            "¥": "JPY",    # Japanese Yen
            # Add more mappings as needed
        }
        
        # Create a new column for the converted amount
        df["amount_idr"] = 0.0
        
        for index, row in df.iterrows():
            # Split the display_price into currency symbol and amount
            display_price = row[currency_column].strip()
            try:
                currency_symbol, amount_str = display_price.split()
                # Remove commas from the amount string and convert to float
                amount = float(amount_str.replace(",", ""))
            except ValueError:
                logging.warning(f"Invalid format in display_price: {display_price}")
                continue
            
            # Map currency symbol to currency code
            currency_code = currency_mapping.get(currency_symbol)
            if currency_code and currency_code in currency_data:
                # Convert amount to IDR and round to 2 decimal places
                df.at[index, "amount_idr"] = round(amount * currency_data[currency_code], 2)
            else:
                logging.warning(f"Currency {currency_symbol} not found or not supported.")
        
        return df

    def crawl_flights(self, origin: str, destination: str, start_date: str, end_date: str) -> None:
        """Crawl flight data for the given origin, destination, and date range."""
        program_start_time = time.time()
        
        cookies_dict = self.get_cookies(f"{self.base_url}/transport/?target_slug=%2Fflight")
        cookies_dict["klk_currency"] = "IDR"
        
        list_date = self.generate_date_range(start_date, end_date)
        all_data = []

        # Start API data fetching timer
        api_fetch_start_time = time.time()
        
        for date in list_date:
            payload = {
                "search_condition": [
                    {
                        "origin_position": origin,
                        "destination_position": destination,
                        "departure_date": date,
                        "seat_class": "Economy_PremiumEconomy",
                        "passengers": [
                            {"count": 1, "passenger_type": "adult", "name": "Adult"},
                            {"count": 1, "passenger_type": "child", "name": "Child"},
                            {"count": 1, "passenger_type": "infant", "name": "Infant"}
                        ],
                        "is_from_filter": False,
                        "sort_type": "price_low_high"
                    }
                ],
                "is_need_loop": True
            }

            response_data = self.send_api_request(self.api_url, self.headers, payload, cookies_dict, date)
            if response_data:
                all_data.append(response_data)
        
        # End API data fetching timer
        api_fetch_elapsed_time = time.time() - api_fetch_start_time
        logging.info(f"Fetching data from API took {api_fetch_elapsed_time:.2f} seconds.")
        
        self.save_data_to_file(all_data, "flight_data_raw.json")
        
        flight_df = self.extract_flight_data(all_data)
        
        # Fetch currency data and convert amounts to IDR
        currency_data = self.get_currency_data()
        if currency_data:
            flight_df = self.convert_amount_to_idr(flight_df, "display_price", "amount", currency_data)
        
        # Save DataFrame to CSV
        flight_df.to_csv("flight_data_raw.csv", index=False, encoding="utf-8")
        
        # End overall program timer
        program_elapsed_time = time.time() - program_start_time
        logging.info(f"Total program execution time: {program_elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    crawler = FlightCrawler()

    origin = "13055"
    destination = "13482"
    start_date = "2025-03-05"
    end_date = "2025-03-10"
    
    crawler.crawl_flights(origin, destination, start, end_date)