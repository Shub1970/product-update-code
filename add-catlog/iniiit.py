import json
import requests

API_URL = "http://49.205.180.247:3007/api"
# post_structure ={
#   "data": {
#     "Name": "string",
#     "short_description": "string",
#     "Description": "string",
#     "Multiple_Image": [
#       "string or id",
#       "string or id"
#     ],
#     "new": true,
#     "specs": "string",
#     "product_categories": [
#       "string or id",
#       "string or id"
#     ],
#     "product_variants": [
#       "string or id",
#       "string or id"
#     ],
#     "alias": "string",
#     "model_code": "string",
#     "attributes": "string",
#     "show_on_eshop": true,
#     "icon": "string or id",
#     "product_range": "string or id",
#     "application_image": "string or id",
#     "specification": [
#       {
#         "id": 0,
#         "width": "string",
#         "length": "string",
#         "thickness": "string"
#       }
#     ],
#     "locale": "string",
#     "localizations": [
#       "string or id",
#       "string or id"
#     ]
#   }
# }


def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []


def add_category_in_product_category(datas):
    """Update product categories and specifications."""
    for data in datas:
        try:
            # Fetch product by model_code
            response = requests.get(
                f"{API_URL}/products?filters[model_code][$eq]={
                    data['model_code']}"
            )
            if response.status_code == 200:
                product_data = response.json().get("data", [])
                if product_data:
                    product_document_id = product_data[0].get("documentId")
                    post_url = f"{API_URL}/products/{product_document_id}"

                    # Construct the payload
                    payload = {
                        "data": {
                            "product_categories": {
                                "connect": [
                                    {
                                        "documentId": data["child_category"],
                                        "position": {
                                            "after": data["parent_category"]
                                        }
                                    }
                                ]
                            },
                            "specification": [
                                {
                                    "width": data["width"],
                                    "length": data["length"],
                                    "thickness": data["thickness"]
                                }
                            ],
                            "new": 'true' if data["new"] == "Y" else 'false',
                        }
                    }

                    # Log the PUT request details
                    print("PUT URL:", post_url)
                    print("PUT Payload:", json.dumps(payload, indent=4))

                    # Send the PUT request
                    headers = {"Content-Type": "application/json"}
                    update_response = requests.put(
                        post_url, data=json.dumps(payload), headers=headers
                    )

                    if update_response.status_code == 200:
                        print(
                            f"Successfully updated product {
                                data['model_code']}."
                        )
                    else:
                        print(
                            f"Failed to update product {data['model_code']}. "
                            f"Error: {update_response.text}"
                        )
                else:
                    print(f"No product found for model_code: {
                          data['model_code']}")
            else:
                print(
                    f"Failed to fetch product for model_code: {
                        data['model_code']}. "
                    f"Status code: {response.status_code}"
                )
        except Exception as e:
            print(f"An error occurred: {e}")


def main():
    """Main execution function."""
    file_url = "/Users/shubhamk/Developer/office_work/century-product-work/add-catlog/csvjson.json"  # Update this path
    datas = load_json(file_url)
    if datas:
        add_category_in_product_category(datas)


if __name__ == "__main__":
    main()
