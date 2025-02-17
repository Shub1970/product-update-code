import json
import requests
from collections import defaultdict

API_URL = "http://49.205.180.247:3007"
PRODUCTS_URL = "/api/product-variants"
PAGE_SIZE = 100


class StatusTracker:
    def __init__(self):
        self.total_products = 0
        self.successful_updates = 0
        self.failed_updates = 0
        self.errors = defaultdict(list)

    def print_status(self):
        print("\n" + "="*50)
        print("FINAL STATUS REPORT")
        print("="*50)
        print(f"Total products processed: {self.total_products}")
        print(f"Successful updates: {self.successful_updates}")
        print(f"Failed updates: {self.failed_updates}")

        if self.errors:
            print("\nError Details:")
            for error_type, errors in self.errors.items():
                if errors:
                    print(f"\n{error_type.replace('_', ' ').title()}:")
                    for error in errors:
                        print(f"- {error}")
        print("="*50)


def fetch_products_variants(page, status_tracker):
    """
    Fetch products from the API with pagination.
    """
    try:
        url = f"{API_URL}{PRODUCTS_URL}?pagination[page]={page}&pagination[pageSize]={PAGE_SIZE}&filters[alias][$null]=true&populate[0]=state&populate[1]=city"
        response_search = requests.get(url)
        response_search.raise_for_status()
        return response_search.json()
    except requests.exceptions.RequestException as req_err:
        status_tracker.errors['fetch_errors'].append(
            f"Page {page}: {str(req_err)}")
        print(f"Error fetching products: {req_err}")
        return None


def update_product_variants(product, status_tracker):
    """
    Update product variant with alias.
    """
    try:
        # Check if required data exists
        if not product.get('state'):
            error_msg = f"Missing state data for product {product.get('documentId', 'Unknown ID')}"
            status_tracker.errors['data_errors'].append(error_msg)
            status_tracker.failed_updates += 1
            print(error_msg)
            return

        # Create alias
        alias = ''
        if product.get('city'):
            alias = f"{product['city']['name']}-{product['state']['name']}-{product['height']}x{product['width']}x{product['tickness']}"
        else:
            alias = f"{product['state']['name']}-{product['height']}x{product['width']}x{product['tickness']}"

        # Update product
        product_update_data = {
            "data": {
                "alias": alias
            }
        }

        response_update = requests.put(
            f"{API_URL}{PRODUCTS_URL}/{product['documentId']}",
            json=product_update_data
        )
        response_update.raise_for_status()

        status_tracker.successful_updates += 1
        print(
            f"Successfully updated product {product['documentId']} with alias: {alias}")

    except requests.exceptions.RequestException as req_err:
        error_msg = f"Request error updating product {product.get('documentId', 'Unknown ID')}: {str(req_err)}"
        status_tracker.errors['api_errors'].append(error_msg)
        status_tracker.failed_updates += 1
        print(error_msg)

    except KeyError as key_err:
        error_msg = f"Missing key {key_err} for product {product.get('documentId', 'Unknown ID')}"
        status_tracker.errors['data_errors'].append(error_msg)
        status_tracker.failed_updates += 1
        print(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error for product {product.get('documentId', 'Unknown ID')}: {str(e)}"
        status_tracker.errors['unexpected_errors'].append(error_msg)
        status_tracker.failed_updates += 1
        print(error_msg)


def main():
    status_tracker = StatusTracker()
    page = 1

    while True:
        print(f"\nProcessing page {page}...")
        products_data_variants = fetch_products_variants(page, status_tracker)

        if not products_data_variants or not products_data_variants.get("data"):
            break

        products = products_data_variants["data"]
        status_tracker.total_products += len(products)

        for product in products:
            update_product_variants(product, status_tracker)

        # Check if we've processed all pages
        total_pages = products_data_variants.get(
            "meta", {}).get("pagination", {}).get("pageCount", 0)
        if page >= total_pages:
            break

        page += 1

    status_tracker.print_status()


if __name__ == "__main__":
    main()
