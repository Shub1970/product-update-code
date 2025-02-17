import json
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Constants
API_URL = "http://49.205.180.247:3007"
DEALER_URL = "/api/dealers"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            f'dealer_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validate_dealer_data(dealer: Dict) -> List[str]:
    """
    Validate required dealer fields and return list of validation errors.
    """
    errors = []
    # Removed email as it might be optional based on your data
    required_fields = ['name']

    return errors


def convert_to_string(value) -> str:
    """
    Convert value to string format if it's not None or '#N/A'.
    """
    if value not in [None, "#N/A", ""]:
        return str(value)
    return ""


def prepare_payload(dealer: Dict) -> Dict:
    """
    Prepare the API payload from dealer data with proper type conversions.
    """
    return {
        "data": {
            "name": dealer.get('name', ''),
            "email": dealer.get('email') if dealer.get('email') else 'test@gmail.com',
            "address": dealer.get('address', ''),
            "company_name": dealer.get('company', ''),
            "state": {
                "connect": [dealer["stateDocumentid"]]
            },
            "city": {
                "connect": [dealer["city_documentid"]]
            },
            "phone": convert_to_string(dealer.get('mobile')),
            "landline": convert_to_string(dealer.get('landline')),
            "latitude": convert_to_string(dealer.get('latitude')),
            "longitude": convert_to_string(dealer.get('longitude')),
            "delar_type": dealer.get('dealer_type', ''),
        }
    }


def post_dealers_data(dealers: List[Dict]) -> Dict[str, int]:
    """
    Post dealers data to the API and return statistics.
    """
    stats = {"total": len(dealers), "success": 0, "failed": 0, "skipped": 0}

    for dealer in dealers[0:50]:
        try:
            # Validate dealer data
            validation_errors = validate_dealer_data(dealer)
            if validation_errors:
                logger.warning(f"Skipping dealer {dealer.get(
                    'name', 'Unknown')}: {validation_errors}")
                stats["skipped"] += 1
                continue

            payload = prepare_payload(dealer)
            print("prepare_payload", prepare_payload)

            # Determine the API endpoint based on status
            url = f"{API_URL}{DEALER_URL}"
            if dealer.get("status") == 2:
                url += "?status=draft"

            # Make the API request
            response = requests.post(url, json=payload, timeout=30)

            if response.status_code in [200, 201]:
                logger.info(f"Successfully uploaded dealer: {dealer['name']}")
                stats["success"] += 1
            else:
                logger.error(f"API error for dealer {dealer.get('name', 'Unknown')}: {
                             response.status_code} - {response.text}")
                stats["failed"] += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"API error for dealer {
                         dealer.get('name', 'Unknown')}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"API Response: {e.response.text}")
            stats["failed"] += 1
        except Exception as e:
            logger.error(f"Unexpected error processing dealer {
                         dealer.get('name', 'Unknown')}: {str(e)}")
            stats["failed"] += 1

    return stats


def main():
    """Main execution function."""
    try:
        logger.info("Starting dealer data upload process")

        # Load dealer data
        file_path = '/Users/shubhamk/Developer/office_work/century-product-work/dealer/dealer-to-push.json'
        with open(file_path, "r") as f:
            dealers = json.load(f)

        logger.info(f"Loaded {len(dealers)} dealers from file")

        # Process dealers
        stats = post_dealers_data(dealers)

        # Log final statistics
        logger.info("Upload process completed")
        logger.info(f"Total dealers processed: {stats['total']}")
        logger.info(f"Successfully uploaded: {stats['success']}")
        logger.info(f"Failed to upload: {stats['failed']}")
        logger.info(f"Skipped due to validation: {stats['skipped']}")

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {str(e)}")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in main execution: {str(e)}")


if __name__ == "__main__":
    main()
