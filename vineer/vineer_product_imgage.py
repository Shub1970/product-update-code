# vineers image put logic

import json
import requests
import re

# Configuration
API_URL = "http://49.205.180.247:3007/api"  # Replace with your Strapi base URL
# Base URL for images
IMAGE_BASE_URL = "https://www.centuryply.com/centuryveneers/image/big/"

# Load JSON data


def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def sanitize_file_name(file_name):
    # Replace invalid characters with underscores
    sanitized_name = re.sub(r"[^a-zA-Z0-9_.]", "_", file_name)
    return sanitized_name


def get_all_category_in_hierarchy_document_id(category):
    try:
        url = (
            f"{API_URL}/product-categories?filters[Name][$eq]={category}"
            "&populate[0]=parent_category"
            "&populate[1]=parent_category.parent_category"
            "&populate[2]=parent_category.parent_category.parent_category"
        )
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            raise ValueError(f"No category found with name {category}")

        all_category_document_id = []

        def extract_document_ids(category_data):
            if not category_data:
                return
            document_id = category_data.get("documentId")
            if document_id:
                all_category_document_id.append(document_id)
            parent_category = category_data.get("parent_category")
            if parent_category:
                extract_document_ids(parent_category)

        for category_item in data:
            extract_document_ids(category_item)

        return all_category_document_id

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch category details: {e}")


def download_image(image_url):
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to download image from {image_url}: {
                        response.status_code}, {response.text}")


def upload_image(image_data, ref_id, file_name):
    url = f"{API_URL}/upload"

    # Sanitize the file name
    sanitized_name = sanitize_file_name(file_name)

    files = {
        # Replace "image/jpeg" with the correct MIME type if needed
        "files": (sanitized_name, image_data, "image/jpeg")
    }
    data = {
        "refId": ref_id,
        "ref": "api::product.product",  # Replace with the appropriate reference type
        "field": "Multiple_Image"   # Replace with the appropriate field in your model
    }
    print("payload-image", data)
    response = requests.post(url, files=files, data=data)

    # Check for a successful response (201 or 200)
    if response.status_code in (200, 201):
        try:
            response_data = response.json()
            print(f"Image upload successful. Response: {response_data}")
            return response_data
        except ValueError:
            raise Exception(
                f"Image upload succeeded, but response is not JSON: {response.text}")
    else:
        # Raise an exception for non-successful responses
        raise Exception(f"Image upload failed: {
                        response.status_code}, {response.text}")


def main(json_file):

    products = load_json(json_file)

    for product in products:
        product_name = product.get("name")
        model_code = product.get("model_code")
        image_name = product.get("image")
        specs = product.get("specs")
        alias = product.get("alias")
        model_code = product.get("model_code")
        sub_category = product.get("category")

        category = get_all_category_in_hierarchy_document_id(sub_category)
        print(f"Processing {product_name} with model_code {model_code}...")

        # create product
        url = f"{API_URL}/products"
        payload = {
            "data": {
                "Name": product_name,
                "model_code": model_code,
                "specs": specs,
                "alias": alias,
                "product_categories": {
                    "connect": category
                }
            }
        }

        response = requests.post(url, json=payload)
        if response.status_code not in (200, 201):
            raise Exception(f"Failed to create product: {
                            response.status_code}, {response.text}")
        else:
            print(f"Product created successfully for {
                  product_name}. Response: {response.text}")
            product_id = response.json().get("data", {}).get("documentId")

            if not image_name:
                print(f"No image found for {product_name}")
                continue
            draft_url = f"{API_URL}/products/{product_id}?status=draft"
            response = requests.get(draft_url)
            draft_id = response.json().get("data", {}).get("id")
            # Step 2: Download image from URL
            image_url = f"{IMAGE_BASE_URL}{image_name}"
            print(f"Downloading image from {image_url}...")
            image_data = download_image(image_url)

            # Step 3: Upload imageau
            upload_response = upload_image(image_data, draft_id, image_name)
            print(f"Image uploaded successfully for {
                  product_name}. Response: {upload_response}")


if __name__ == "__main__":
    # Replace with the path to your JSON file
    json_file_path = "./product-image-path.json"
    main(json_file_path)
