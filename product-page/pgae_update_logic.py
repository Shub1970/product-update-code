import json
import requests
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            f'product_updates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

# API Configuration
API_URL = "http://49.205.180.247:3007"
PRODUCTS_URL = "/api/products"
PAGE_SIZE = 100


class ProductUpdateStatus:
    def __init__(self):
        self.total_products = 0
        self.successful_updates = 0
        self.failed_updates = 0
        self.skipped_products = 0
        self.errors: List[Dict[str, str]] = []

    def add_success(self):
        self.successful_updates += 1

    def add_failure(self, product_id: str, error: str):
        self.failed_updates += 1
        self.errors.append({"product_id": product_id, "error": str(error)})

    def add_skip(self):
        self.skipped_products += 1

    def get_summary(self) -> Dict:
        return {
            "total_processed": self.total_products,
            "successful_updates": self.successful_updates,
            "failed_updates": self.failed_updates,
            "skipped_products": self.skipped_products,
            "success_rate": f"{(self.successful_updates / self.total_products * 100):.2f}%" if self.total_products > 0 else "0%",
            "errors": self.errors
        }


def fetch_products(page: int) -> Optional[Dict[str, Any]]:
    """
    Fetch products from the API with pagination.

    Args:
        page: Page number to fetch

    Returns:
        Dictionary containing API response or None if request fails
    """
    try:
        url = f"{API_URL}{PRODUCTS_URL}?pagination[page]={page}&pagination[pageSize]={PAGE_SIZE}&filters[product_categories][documentId][$in]=vrurel0uce9n73vp0l7q32y4"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch products from page {page}: {str(e)}")
        return None


def update_product(product: Dict, status: ProductUpdateStatus) -> None:
    """
    Create new product page data in the database.

    Args:
        product: Product data dictionary
        status: ProductUpdateStatus instance to track updates
    """
    try:
        model_code = product.get('model_code', 'Unknown')
        alias = product.get('alias')

        if not alias:
            error_msg = f"Missing alias for product {model_code}"
            status.add_failure(model_code, error_msg)
            logging.error(error_msg)
            return

        product_page_data = {
            "data": {
                "Name": product.get("Name"),
                "alias": f'igl-{alias}',
                "model_code": f'IGL {model_code}',
                "product_categories": {
                    "connect": ["no2skytmcc1rx2epbj2ckva3"]
                },
                "Description": product.get("Description"),
                "size": [
                    {
                        "width": "8ft",
                        "length": "4ft",
                        "thickness": [
                            {"thickness": thickness}
                            for thickness in ["4mm", "5mm", "6mm", "8mm", "10mm", "12mm", "15mm", "18mm"]
                        ]
                    }
                ]
            },
            "Ordering": product.get('id')
        }

        response = requests.post(
            f"{API_URL}{PRODUCTS_URL}",
            json=product_page_data,
            timeout=30
        )
        response.raise_for_status()

        if not hasattr(response, 'data') or not response.data:
            raise ValueError("Invalid response format from API")

        product_id = response.data[0].get('documentId')
        if not product_id:
            raise ValueError("No product ID in response")

        status.add_success()
        logging.info(
            f"Successfully created product: {model_code} (ID: {product_id})")

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error updating product {model_code}: {str(e)}"
        status.add_failure(model_code, error_msg)
        logging.error(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error updating product {model_code}: {str(e)}"
        status.add_failure(model_code, error_msg)
        logging.error(error_msg)


def main():
    """
    Main function to coordinate product updates with status tracking.
    """
    status = ProductUpdateStatus()
    page = 1

    try:
        while True:
            logging.info(f"Fetching page {page}...")
            products_data = fetch_products(page)
            if not products_data or not products_data.get("data"):
                break

            products = products_data["data"]
            total_products = products_data.get("meta", {}).get(
                "pagination", {}).get("total", 0)

            if total_products == 0:
                logging.warning("No products found in the response")
                break

            logging.info(
                f"Processing {len(products)} products from page {page}")

            for product in products:
                status.total_products += 1
                update_product(product, status)

            if len(products) < PAGE_SIZE:
                break

            page += 1

        # Log final summary
        summary = status.get_summary()
        logging.info("Update process completed. Summary:")
        logging.info(json.dumps(summary, indent=2))

        # Save summary to file
        summary_filename = f'update_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(summary_filename, 'w') as f:
            json.dump(summary, f, indent=2)
        logging.info(f"Summary saved to {summary_filename}")

    except Exception as e:
        logging.error(f"Main process error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
