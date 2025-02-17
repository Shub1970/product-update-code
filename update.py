import requests
import json
from urllib.parse import quote
import re

# Main API details
file_name = "./csvjson_update.json"
main_url = "http://49.205.180.247:3007/api/product-categories"
product_post_url = "http://49.205.180.247:3007/api/products"


# Helper function to generate a slug
def slug(name, parent_name=None):
    sanitized_name = re.sub(r"[^A-Za-z0-9-_.~]+", "", name.replace(" ", "-"))
    if parent_name:
        sanitized_parent = re.sub(
            r"[^A-Za-z0-9-_.~]+", "", parent_name.replace(" ", "-"))
        return f"{sanitized_parent}-{sanitized_name}".lower()
    return sanitized_name.lower()


def get_or_create_category(name, level, parent_id=None, parent_name=None):
    encoded_name = quote(name)
    category_slug = slug(name, parent_name)
    response = requests.get(f"{main_url}?filters[slug][$eq]={category_slug}")
    if response.status_code == 200 and response.json().get("data"):
        return response.json()["data"][0].get("documentId")
    else:
        payload = {
            "data": {
                "Name": name,
                "level": level,
                "show_on_eshop": True,
                "slug": category_slug,
                "parent_category": {"connect": [parent_id]} if parent_id else None
            }
        }
        post_response = requests.post(main_url, json=payload)
        if post_response.status_code in [200, 201]:
            return post_response.json()["data"].get("documentId")
        else:
            print(f"Failed to create category {name}: {post_response.text}")
            return None


# Load data
data = json.load(open(file_name))

# Process each product
for item in data:
    parent_id = get_or_create_category(item["ancaster_category"], level=1)
    child_id = get_or_create_category(
        item["child_category"], level=2, parent_id=parent_id, parent_name=item["parent_category"]
    )
    sub_child_id = None
    if item["sub_child_category"]:
        sub_child_id = get_or_create_category(
            item["sub_child_category"], level=3, parent_id=child_id, parent_name=item["child_category"]
        )

    if sub_child_id or child_id:
        product_payload = {
            "data": {
                "Name": item["name"],
                "model_code": item["model_code"],
                "short_description": item["short_description"],
                "Description": item["description"],
                "display_on_eshop": item["display_on_eshop"] == "YES",
                "specs": item["specs"],
                "attributes": item["attributes"],
                "alias": slug(item["name"]),
                "display_on_eshop": item["new"] == "Y",
                "product_categories": {
                    "connect": [
                        {"documentId": parent_id},
                        {"documentId": child_id},
                        {"documentId": sub_child_id} if sub_child_id else None
                    ]
                }
            }
        }
        # this is the change line on branch1

        product_response = requests.post(
            # this is another change
            product_post_url, json=product_payload)
        # this is the change in branch1
        if product_response.status_code in [200, 201]:
            print(f"Product {item['name']} created successfully.")
        else:
            print(f"Failed to create product {
                  item['name']}: {product_response.text}")
