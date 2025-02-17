import json
import requests

API_URL = "http://49.205.180.247:3007"
PRODUCTS_URL = "/api/products"

# Add pagination limit
PAGE_SIZE = 10  # Adjust based on your needs


def fetch_products(page):
    """
    Fetch products from the API with pagination.
    """
    try:
        response_search = requests.get(
            f"{API_URL}{PRODUCTS_URL}?pagination[page]={page}&pagination[pageSize]={
                PAGE_SIZE}&filters[product_categories][documentId][$in]=vrurel0uce9n73vp0l7q32y4&filters[size][$null]=true&populate[0]=product_categories"
        )
        response_search.raise_for_status()
        return response_search.json()
    except requests.exceptions.RequestException as req_err:
        print(f"Error fetching products: {req_err}")
        return None


def update_product(product):
    """
    Update product page data in the database.
    """
    try:
        # Update product page with size component
        product_page_data = {
            "data": {
                "size": [
                    {
                        "width": "8ft",
                        "length": "4ft",
                        "thickness": [
                            {"thickness": "1mm"}
                        ]
                    }
                ]
            }
        }
        response_update = requests.put(
            f"{API_URL}{PRODUCTS_URL}/{product['documentId']}",
            json=product_page_data
        )
        response_update.raise_for_status()
        print(f"Product page updated for {product['model_code']}")

    except requests.exceptions.RequestException as req_err:
        print(f"Request error updating product page for {
              product['design_code']}: {req_err}")
    except KeyError as key_err:
        print(f"KeyError: Missing expected key in response for {
              product['design_code']}: {key_err}")
    except Exception as e:
        print(f"Unexpected error updating product page for {
              product['design_code']}: {e}")


def main():
    page = 1
    no_of_products = 0
    while True:
        products_data = fetch_products(page)
        products_count = products_data.get("meta", {}).get("total", 0)
        if not products_data or not products_data.get("data"):
            break  # Exit loop if no products are returned

        for product in products_data["data"]:
            no_of_products += 1
            update_product(product)

        page += 1
    print(f"Total products updated: {no_of_products}")


if __name__ == "__main__":
    main()
