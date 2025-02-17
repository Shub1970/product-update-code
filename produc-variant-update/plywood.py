import json
import requests

# Configuration
API_URL = "http://49.205.180.247:3007/api"  # Replace with your Strapi base URL
# Base URL for images
IMAGE_BASE_URL = "https://www.centuryply.com/centuryveneers/image/big/"

# Load JSON data


def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def main(json_file):
    products = load_json(json_file)

    for product in products:
        product_state = product.get("document_id")
        product_city = product.get("city_document_id")
        product_id = product.get("product")
        width = product.get("Width")
        length = product.get("Length")
        thickness = product.get("Thickness")
        new_price = product.get("new_price")

        if new_price:
            # Remove commas and convert to an integer
            new_price = int(new_price.replace(",", ""))

        print("product_state", product_state)
        url = f"{API_URL}/product-variants"
        payload = {
            "data": {
                "state": {"connect": [product_state]} if product_state else None,
                'city': {"connect": [product_city]} if product_city else None,
                # "product": {"connect": [product_id]} if product_id else None,
                "product": {"connect": ["iwu63x1ilvswhnn5c9e9doba"]},
                "width": width if width else None,
                "height": length if length else None,
                "tickness": thickness if thickness else None,
                "price": new_price if new_price else None
            }
        }
        # Remove None values from the payload
        payload["data"] = {k: v for k,
                           v in payload["data"].items() if v is not None}

        print("Payload being sent:", json.dumps(payload, indent=4))
        print("URL:", url)

        response = requests.post(url, json=payload)
        print("Response status code:", response.status_code)
        print("Response text:", response.text)

        if response.status_code not in (200, 201):
            raise Exception(
                f"Failed to create product: {response.status_code}, {response.text}")
        else:
            print(
                f"Product created successfully for {product_id}. Response: {response.text}")


if __name__ == "__main__":
    # Replace with the path to your JSON file
    json_file_path = "/Users/shubhamk/Developer/office_work/century-product-work/produc-variant-update/club-prime-dore.json"
    main(json_file_path)
