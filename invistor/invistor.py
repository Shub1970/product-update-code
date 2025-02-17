import json
import requests
import logging
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:1337/api"
INVESTORS_CATEGORY_PATH = "investors-category.json"
INVESTORS_DATA_PATH = "investordatas.json"

# Configure more detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='investor_processing.log'
)
logger = logging.getLogger(__name__)


def format_date(date_string):
    """Convert date string to yyyy-MM-dd format."""
    if not date_string or date_string == "null":
        return None
    try:
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
    except ValueError:
        return datetime.strptime(date_string, "%Y-%m-%d").strftime("%Y-%m-%d")


def send_request(method, url, data=None, max_retries=5, initial_delay=2):
    """
    Enhanced request method with exponential backoff and detailed error logging.

    Args:
        method (str): HTTP method (GET, POST, PUT, etc.)
        url (str): Target URL
        data (dict, optional): Request payload
        max_retries (int): Number of retry attempts
        initial_delay (float): Initial delay between retries

    Returns:
        dict: JSON response from server
    """
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, json=data, timeout=10)

            # Log full request and response details for debugging
            logger.info(f"Request URL: {url}")
            logger.info(f"Request Method: {method}")
            logger.info(f"Request Data: {json.dumps(
                data, indent=2) if data else 'None'}")
            logger.info(f"Response Status: {response.status_code}")

            # Raise an exception for HTTP errors
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            delay = initial_delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Request failed (Attempt {
                           attempt + 1}/{max_retries}): {e}")

            if attempt == max_retries - 1:
                logger.error(f"Final attempt failed for URL: {url}")
                raise

            time.sleep(delay)


def process_investors(categories, data):
    """Process and upload investor data with error handling."""
    successful_uploads = 0
    failed_uploads = 0

    for category in [c for c in categories if c["parent_id"] == "0"]:
        try:
            # Create top-level investor
            top_investor = send_request('POST', f"{API_URL}/investors", {
                "data": {"title": category["name"]}
            })
            investor_id = top_investor['data']['documentId']
            logger.info(f"Created investor: {
                        category['name']} (ID: {investor_id})")

            # Process child categories
            child_categories = [
                child for child in categories
                if child["parent_id"] == category["id"] and child["status"] == "1"
            ]
            child_categories.sort(key=lambda x: x["order_c"])
            # add parent category to child_categories
            child_categories.insert(0, category)

            investor_info = []
            for child in child_categories:
                child_data = [
                    {
                        "title": item["name"],
                        "date": format_date(item["edate"]),
                        "file_url": 'https://www.centuryply.com/'+item["file"],
                    }
                    for item in data
                    if item["catid"] == child["id"] and item["status"] == "1"
                ]
                child_data.sort(key=lambda x: x["date"], reverse=True)
                if child_data:
                    investor_info.append({
                        "title": child["name"],
                        "file_info": child_data
                    })

            # Update investor with child information
            if investor_info:
                response_of_put = send_request('PUT', f"{API_URL}/investors/{investor_id}", {
                    "data": {"investor_info": investor_info}
                })

                successful_uploads += 1

        except Exception as e:
            failed_uploads += 1
            logger.error(f"Failed to process category {category['name']}: {e}")

    logger.info(f"Upload Summary: Successful={
                successful_uploads}, Failed={failed_uploads}")


def main():
    """Main execution function."""
    with open('/Users/shubhamk/Developer/office_work/century-product-work/invistor/investors-category.json', "r") as f:
        categories = json.load(f)

    with open('/Users/shubhamk/Developer/office_work/century-product-work/invistor/investordatas.json', "r") as f:
        data = json.load(f)

    process_investors(categories, data)


if __name__ == "__main__":
    main()
