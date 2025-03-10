# Crawling Klook Flight

### Running Code
1. Create a virtual environment ```python -m venv venv```
2. Install all requirements ```pip install -r .\requirements.txt```
3. Search for flights manually on the Klook Website https://www.klook.com/flights/search/
4. Extract the `origin_position` and `destination_position` data from the URL of the search results, along with the date, and pass them to the main function.
5. Run the crawling.py file ```python crawling.py```

### Output

The output of this result is saved in a CSV file format, and to view the structure of the API response data, refer to the `structure_data.txt` file