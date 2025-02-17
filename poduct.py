import requests
import json

file_name = "./csvjson.json"
# file data
# [
#   {
#     "parent_category": "test_laminate",
#     "child_category": "STONE VENEER",
#     "sub_child_category": "Slate",
#     "new": "Y",
#     "name": "Calacatta Marble",
#     "model_code": "5847 SL",
#     "short_description": "short_description text write",
#     "description": "description text  write",
#     "display_on_eshop": "YES",
#     "specs": "1.00mm",
#     "attributes": "",
#     "alias": "",
#     "created_by_id": "",
#     "updated_by_id": ""
#   },
#   {
#     "parent_category": "test_laminate",
#     "child_category": "STONE VENEER",
#     "sub_child_category": "Slate",
#     "new": "Y",
#     "name": "Onyx",
#     "model_code": "5891 SL",
#     "short_description": "short_description text write",
#     "description": "description text  write",
#     "display_on_eshop": "YES",
#     "specs": "1.00mm",
#     "attributes": "",
#     "alias": "",
#     "created_by_id": "",
#     "updated_by_id": ""
#   }]

# Main URL for API calls
main_url = "http://49.205.180.247:3007/api/product-categories"
product_post_url = "http://49.205.180.247:3007/api/products"
# Check for the parent category

for data in json.load(open(file_name)):
    response = requests.get(
        # Fix URL formatting
        f"{main_url}?filters[Name][$eq]={data['parent_category']}")
    print("GET Response:", response.json())

    # Extract the parent category if it exists
    parent_category_document_id = None
    if response.status_code == 200 and response.json().get("data"):
        # Adjusted to match typical Strapi response structure
        parent_category_document_id = response.json()[
            "data"][0].get("documentId")
    else:
        # Create the parent category if it doesn't exist
        payload = {
            "data": {
                "Name": data["parent_category"],
                "level": "1",
                "show_on_eshop": "true",
            }
        }
        # Use `json` to send payload as JSON
        post_response = requests.post(main_url, json=payload)
        if post_response.status_code == 200 or post_response.status_code == 201:
            parent_category_document_id = post_response.json().get("documentId")
        else:
            print("Failed to create Parent Category:", post_response.text)

    # Check for the child category
    child_category_document_id = None
    if parent_category_document_id:
        response = requests.get(
            f"{main_url}?filters[Name][$eq]={data['child_category']}")

        # Extract the child category if it exists
        if response.status_code == 200 and response.json().get("data"):
            # Adjusted to match typical Strapi response structure
            child_category_document_id = response.json()[
                "data"][0].get("documentId")
        else:
            # Create the child category if it doesn't exist
            payload = {
                "data": {
                    "Name": data["child_category"],
                    "level": "2",
                    "show_on_eshop": "true",
                    "parent_category": {
                        "connect": parent_category_document_id
                    },
                }
            }
            post_response = requests.post(main_url, json=payload)
            if post_response.status_code == 200 or post_response.status_code == 201:
                child_category_document_id = post_response.json().get("documentId")
            else:
                print("Failed to create Child Category:", post_response.text)

        # Check for the sub-child category
        sub_child_category_document_id = None
        if child_category_document_id:
            response = requests.get(
                f"{main_url}?filters[Name][$eq]={data['sub_child_category']}")

            # Extract the sub-child category if it exists
            if response.status_code == 200 and response.json().get("data"):
                # Adjusted to match typical Strapi response structure
                sub_child_category_document_id = response.json()[
                    "data"][0].get("documentId")
            else:
                # Create the sub-child category if it doesn't exist
                payload = {
                    "data": {
                        "Name": data["sub_child_category"],
                        "level": "3",
                        "show_on_eshop": "true",
                        "parent_category": {
                            "connect": child_category_document_id
                        },
                    }
                }
                post_response = requests.post(main_url, json=payload)
                if post_response.status_code == 200 or post_response.status_code == 201:
                    sub_child_category_document_id = post_response.json().get("documentId")
                else:
                    print("Failed to create Sub-Child Category:",
                          post_response.text)

            # Create the product
            if sub_child_category_document_id:
                payload = {
                    "data": {
                        "Name": data["name"],
                        "model_code": data["model_code"],
                        "short_description": data["short_description"],
                        "description": data["description"],
                        "display_on_eshop": data["display_on_eshop"],
                        "specs": data["specs"],
                        "attributes": data["attributes"],
                        "alias": slug(data["name"]),
                        "product_categories": {
                            "connect": [parent_category_document_id, child_category_document_id, sub_child_category_document_id]
                        },
                    }
                }
                post_response = requests.post(product_post_url, json=payload)
                if post_response.status_code == 200 or post_response.status_code == 201:
                    print("Product Created Successfully")
                else:
                    print("Failed to create Product:", post_response.text)
            else:
                print("Failed to create Sub-Child Category")
        else:
            print("Failed to create Child Category")
