import json
import requests
import time
from typing import Optional, Dict, Any

API_URL = "http://49.205.180.247:3007"
PRODUCTS_URL = "/api/products"
PAGE_SIZE = 25


def fetch_products(page: int) -> Optional[Dict[str, Any]]:
    """
    Fetch products that do not have SEO set.

    Args:
        page: Page number to fetch
    Returns:
        JSON response or None if request fails
    """
    try:
        params = {
            "pagination[page]": page,
            "pagination[pageSize]": PAGE_SIZE,
            "filters[product_categories][documentId][$in]": "rn2yfgzt2qu2jx6y0ja4xebt",
            "filters[seo][$null]": "true",
            "populate": "product_categories",
        }

        response_search = requests.get(
            f"{API_URL}{PRODUCTS_URL}",
            params=params,
            timeout=30
        )
        response_search.raise_for_status()
        return response_search.json()
    except requests.exceptions.RequestException as req_err:
        print(f"❌ Error fetching products: {req_err}")
        return None


def generate_seo_metadata(product: Dict[str, Any]) -> tuple[str, str]:
    """
    Generate SEO metadata from product information.

    Args:
        product: Product dictionary containing details
    Returns:
        Tuple of (metaTitle, metaDescription)
    """
    product_category = [pc for pc in product.get("product_categories", [])
                        if pc is not None]
    product_category.sort(key=lambda x: x.get("level", float("inf")))

    components = [
        x.get("Name", "").strip() for x in product_category
        if x.get("Name")
    ] + [
        item for item in [
            product.get("Name", "").strip(),
            product.get("model_code", "").strip()
        ] if item
    ]

    metaTitle = " | ".join(filter(None, components))
    metaDescription = f"Discover {product.get(
        'Name', '')} - {' '.join(x.get('Name', '') for x in product_category)}"

    return metaTitle, metaDescription


def update_product(product: Dict[str, Any]) -> bool:
    """
    Update product page data with SEO metadata.

    Args:
        product: Product dictionary containing details
    Returns:
        Boolean indicating success
    """
    product_id = product.get("documentId")
    if not product_id:
        print(f"⚠️ Skipping update: Missing 'documentId' for product {
              product.get('model_code', 'Unknown')}")
        return False

    try:
        metaTitle, metaDescription = generate_seo_metadata(product)

        product_page_data = {
            "data": {
                "seo": {
                    "metaTitle": metaTitle,
                    "metaDescription": metaDescription,
                }
            }
        }

        response_update = requests.put(
            f"{API_URL}{PRODUCTS_URL}/{product_id}",
            json=product_page_data,
            timeout=30
        )
        response_update.raise_for_status()

        print(f"✅ Product page updated for {
              product.get('model_code', 'Unknown')}")
        return True

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Request error updating product page for {
              product.get('model_code', 'Unknown')}: {req_err}")
    except Exception as e:
        print(f"❌ Unexpected error updating product page for {
              product.get('model_code', 'Unknown')}: {e}")

    return False


def main():
    page = 1
    successful_updates = 0
    total_products = 0
    has_more_pages = True

    try:
        while has_more_pages:
            print(f"\n📄 Processing page {page}...")
            products_data = fetch_products(page)

            if not products_data:
                print("❌ Failed to fetch products data")
                break

            # Extract pagination metadata
            pagination = products_data.get("meta", {}).get("pagination", {})
            current_page = pagination.get("page", 0)
            total_pages = pagination.get("pageCount", 0)
            total_items = pagination.get("total", 0)

            print(f"📊 Page {current_page} of {
                  total_pages} (Total items: {total_items})")

            if not products_data.get("data"):
                print("⚠️ No products found on this page")
                break

            batch_products = products_data["data"]
            batch_count = len(batch_products)
            total_products += batch_count

            print(f"🔄 Processing {batch_count} products on this page...")

            for idx, product in enumerate(batch_products, 1):
                print(f"📦 Product {idx}/{batch_count} on page {page}...")
                if update_product(product):
                    successful_updates += 1
                time.sleep(0.5)  # 500ms delay between products

            # Check if we've reached the last page
            has_more_pages = current_page < total_pages
            page += 1

            if has_more_pages:
                print(f"⏳ Waiting before processing next page...")
                time.sleep(1)  # 1 second delay between pages

    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted by user")
    finally:
        print(f"\n✅ Final Summary:")
        print(f"Total products processed: {total_products}")
        print(f"Successful updates: {successful_updates}")
        print(f"Failed updates: {total_products - successful_updates}")


if __name__ == "__main__":
    main()
