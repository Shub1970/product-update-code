import json
import requests

API_URL = "http://49.205.180.247:3007/api"


def fetch_products_with_pagination():
    """Fetch all products from the API with pagination."""
    page = 1
    page_size = 25  # Adjust based on your API's pagination limit
    all_products = []

    while True:
        response = requests.get(
            f"{API_URL}/products",
            params={
                # Correct filtering
                "filters[product_categories][documentId][$in]": "zecun6qorwujm7ojcstf3ox2",
                "pagination[page]": page,
                "pagination[pageSize]": page_size,
                # Ensure we get category details
                "populate[0]": "product_categories"
            }
        )
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", [])
            all_products.extend(products)
            total_pages = data.get("meta", {}).get(
                "pagination", {}).get("pageCount", 1)

            if page >= total_pages:  # Stop when last page is reached
                break

            page += 1
        else:
            print(f"Failed to fetch products: {response.text}")
            break

    return all_products


def update_veneer_product_specifications():
    """Update product specifications if they are missing."""
    products = fetch_products_with_pagination()
    print(f"Fetched {len(products)} products.")

    for product in products:
        # Use "id" instead of "documentId"
        product_document_id = product.get("documentId")

        payload = {
            "data": {
                "specification": [
                    {
                        "width": "1220mm",
                        "length": "2440mm",
                        "thickness": "3.5mm"
                    }
                ]
            }
        }
        response = requests.put(
            f"{API_URL}/products/{product_document_id}", json=payload)
        if response.status_code == 200:
            print(f"Updated product {
                  product_document_id} with new specifications")
        else:
            print(f"Failed to update product {
                  product_document_id}: {response.text}")


def main():
    update_veneer_product_specifications()


if __name__ == "__main__":
    main()
