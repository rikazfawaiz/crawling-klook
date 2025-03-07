# Crawling Klook Flight

### Running Code
1. Create a virtual environment ```python -m venv venv```
2. Install all requirements ```pip install -r .\requirements.txt```
3. Search for flights manually on the Klook Website https://www.klook.com/flights/search/
4. Extract the `origin_position` and `destination_position` data from the URL of the search results, along with the date, and pass them to the main function.
5. Run the crawling.py file ```python crawling.py```

### Output

The result of running the script will produce two files in CSV and JSON formats.

    The JSON file contains the raw data from the API.

    The CSV file contains data that has been selected and formatted according to specific needs.

In the JSON file, the data is unstructured because the API combines data for multiple days without a clear format. This is because, from the beginning, the JSON output was intended only as a sample to understand the structure of the data.