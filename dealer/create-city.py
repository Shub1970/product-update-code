import json
import requests
import os
import csv
from datetime import datetime

API_URL = "http://49.205.180.247:3007"
CITY_URL = "/api/cities"
STATE_URL = "/api/states"


def create_csv(city_data_list, output_dir="exports"):
    """Create a CSV file with city names and document IDs"""
    # Create exports directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"city_document_ids_{timestamp}.csv")

    # Write data to CSV
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['City Name', 'Document ID'])
        # Write data
        writer.writerows(city_data_list)

    return filename


def strapi_post(states_city_relations):
    city_data_list = []  # List to store city names and document IDs

    try:
        for relation in states_city_relations:
            try:
                state_name = relation["state"]
                response_search = requests.get(
                    f"{API_URL}{STATE_URL}?filters[name][$eq]={state_name}")
                response_search.raise_for_status()
                search_data = response_search.json()

                # Check if state exists
                if not search_data.get("data"):
                    print(f"State {state_name} not found")
                    continue

                state_documentid = search_data["data"][0]["documentId"]

                # Create city
                city_data = {
                    "data": {
                        "name": relation["city"],
                        "state": {
                            "connect": [state_documentid]
                        }
                    }
                }

                response = requests.post(
                    f"{API_URL}{CITY_URL}",
                    json=city_data,
                    timeout=10
                )
                response.raise_for_status()

                if response.status_code in [200, 201]:
                    print(f"City {relation['city']} created successfully.")
                    # Extract the document ID from the response
                    city_response_data = response.json()
                    if city_response_data.get("data", {}).get("documentId"):
                        city_data_list.append([
                            relation['city'],
                            city_response_data["data"]["documentId"]
                        ])
                else:
                    print(f"Failed to create city {
                          relation['city']}. Status code: {response.status_code}")
                    print(response.text)

            except requests.RequestException as e:
                print(f"Error processing {relation}: {e}")
                continue
            except KeyError as e:
                print(f"Missing required field in data: {e}")
                continue

        # Create CSV file if we have data
        if city_data_list:
            csv_file = create_csv(city_data_list)
            print(f"CSV file created successfully: {csv_file}")
        else:
            print("No city data was collected to create CSV file")

    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    try:
        state_relation = "/Users/shubhamk/Developer/office_work/century-product-work/dealer/state-city-relation.json"

        with open(state_relation, "r") as f:
            states_city_relation = json.load(f)

        strapi_post(states_city_relation)

    except Exception as e:
        print(f"Error loading files: {e}")
        return


if __name__ == "__main__":
    main()
