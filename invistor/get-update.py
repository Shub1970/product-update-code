import json
import requests
import re
import concurrent.futures
import logging
from PyPDF2 import PdfWriter, PdfReader
import io
from tenacity import retry, stop_after_attempt, wait_fixed
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_URL = "http://localhost:1337/api/investors?populate[0]=investor_info&populate[1]=investor_info.file_info&status=draft"
UPLOAD_URL = "http://localhost:1337/api/upload"
MAX_WORKERS = 5  # Adjust based on system capabilities
REQUEST_TIMEOUT = 30  # Timeout for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/pdf",
    "Referer": "https://www.centuryply.com/",
    "Connection": "keep-alive"
}

session = requests.Session()
session.headers.update(HEADERS)


def get_request_with_pagination(url):
    """Fetch all paginated results from the API efficiently."""
    results = []
    page = 1
    while True:
        try:
            paginated_url = f"{url}&pagination[page]={
                page}&pagination[pageSize]=50"
            response = session.get(paginated_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if "data" not in data or "meta" not in data:
                logger.error("Invalid API response format")
                break

            results.extend(data.get("data", []))

            if page >= data["meta"]["pagination"]["pageCount"]:
                break
            page += 1
        except requests.RequestException as e:
            logger.error(f"Pagination request error: {e}")
            break
    return results


def sanitize_file_name(file_name):
    """Sanitize file names safely."""
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", file_name)[:255]


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def download_file(file_url):
    try:
        file_url = quote(file_url, safe=":/")  # Ensure URL is properly encoded
        logger.info(f"Downloading file: {file_url}")
        response = session.get(file_url, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logger.info(f"Downloaded file: {file_url}")
        return response
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError for {file_url}: {
                     e.response.status_code} {e.response.reason}")
        logger.debug(f"Response content: {e.response.text}")
        if e.response.status_code == 404:
            return None  # Skip if file not found
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException for {file_url}: {e}")
        raise


def download_and_process_file(file_info):
    """
    Download and process a single file with error handling.

    Args:
        file_info (dict): File information dictionary

    Returns:
        tuple: (success, file_url, error_message)
    """
    try:
        file_url = file_info.get("file_url")
        if not file_url:
            return False, None, "Missing file URL"

        file_url = file_url.replace('\\', '/')
        response = download_file(file_url)

        if response is None:  # Skip processing if the file was not found
            return False, file_url, "File not found (404)"

        content_type = response.headers.get("Content-Type", "")
        if "application/pdf" not in content_type:
            return False, file_url, f"Invalid content type: {content_type}"

        file_data = response.content
        upload_response = upload_file(
            file_data, file_info.get("id"), file_url.split("/")[-1])

        return True, file_url, "Success"

    except Exception as e:
        return False, file_url, str(e)


def upload_file(file_data, ref_id, file_name):
    """Upload a file to the API with robust error handling."""
    sanitized_name = sanitize_file_name(file_name)

    # Construct the form-data payload
    files = {
        "files": (sanitized_name, file_data, "application/pdf")
    }
    data = {
        "refId": ref_id,          # Matches the 'refId' field in Postman
        "ref": "investors.file-data",  # Matches the 'ref' field in Postman
        "field": "file"           # Matches the 'field' field in Postman
    }

    # Perform the POST request
    logger.info(f"Uploading file: {sanitized_name}")
    response = session.post(UPLOAD_URL, files=files,
                            data=data, timeout=REQUEST_TIMEOUT)
    logger.debug(f"Upload response: {response.status_code} {response.text}")
    response.raise_for_status()
    return response.json()


def process_request():
    """
    Efficiently process files with concurrent downloads and uploads.

    Uses ThreadPoolExecutor for parallel processing of files.
    """
    try:
        all_data = get_request_with_pagination(API_URL)

        files_to_process = []
        for item in all_data:
            investor_info = item.get("investor_info", [])
            for investor in investor_info:
                files_to_process.extend(investor.get("file_info", []))

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(download_and_process_file, file_info): file_info
                for file_info in files_to_process
            }

            for future in concurrent.futures.as_completed(futures):
                success, file_url, message = future.result()
                if success:
                    logger.info(f"Successfully processed: {file_url}")
                else:
                    logger.error(f"Failed to process {file_url}: {message}")

    except Exception as e:
        logger.error(f"Error processing request: {e}")


if __name__ == "__main__":
    process_request()
