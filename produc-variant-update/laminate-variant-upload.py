from collections import defaultdict
import json
import requests

# Configuration
API_URL = "http://49.205.180.247:3007/api"  # Replace with your Strapi base URL

# Load JSON data


def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def main(json_file, document_mapping):
    price_data = load_json(json_file)

    # Track status
    status = {
        'total': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'errors': defaultdict(list)
    }

    for product in price_data:
        product_id = product.get("product_id")
        if not product_id:
            print("No product_id found for the entry. Skipping...")
            status['skipped'] += 1
            continue

        for city, price in product.items():
            if city == "product_id":
                continue

            status['total'] += 1

            city_mapping = document_mapping.get(city)
            if not city_mapping:
                print(
                    f"City '{city}' not found in the document_mapping. Skipping...")
                status['skipped'] += 1
                status['errors']['missing_mapping'].append(city)
                continue

            state_id = city_mapping["state_id"]
            city_id = city_mapping["city_id"] if city_mapping["city_id"] else None

            payload = {
                "data": {
                    "tickness": 1,
                    "width": 1220,
                    "height": 2440,
                    "product": {"connect": [product_id]},
                    "state": {"connect": [state_id]},
                    "city": {"connect": [city_id]} if city_id else None,
                    "price": price,
                }
            }

            # Remove None values from the payload
            payload["data"] = {k: v for k,
                               v in payload["data"].items() if v is not None}

            url = f"{API_URL}/product-variants"

            print("Payload being sent:", json.dumps(payload, indent=4))
            print("URL:", url)

            try:
                response = requests.post(url, json=payload)
                print("Response status code:", response.status_code)
                print("Response text:", response.text)

                if response.status_code not in (200, 201):
                    print(
                        f"Failed to create product for city {city}: {response.status_code}, {response.text}")
                    status['failed'] += 1
                    status['errors']['api_errors'].append(
                        f"{city}: {response.status_code}")
                else:
                    print(
                        f"Product created successfully for {city}. Response: {response.text}")
                    status['successful'] += 1

            except requests.exceptions.RequestException as e:
                print(f"Request failed for city {city}: {e}")
                status['failed'] += 1
                status['errors']['request_errors'].append(f"{city}: {str(e)}")

    # Print final status report
    print("\n" + "="*50)
    print("FINAL STATUS REPORT")
    print("="*50)
    print(f"Total operations attempted: {status['total']}")
    print(f"Successful operations: {status['successful']}")
    print(f"Failed operations: {status['failed']}")
    print(f"Skipped operations: {status['skipped']}")

    if status['errors']:
        print("\nError Details:")
        for error_type, errors in status['errors'].items():
            if errors:
                print(f"\n{error_type.replace('_', ' ').title()}:")
                for error in errors:
                    print(f"- {error}")

    print("="*50)


if __name__ == "__main__":
    # Replace with the path to your JSON file
    json_file_path = "/Users/shubhamk/Developer/office_work/century-product-work/produc-variant-update/laminate-variant-data.json"
    # Replace with the document mapping
    document_mapping = {
        "Kolkata": {"state_id": "d6s4jrgh54b9hnih195ytey3", "city_id": "t2jtc97k15q8rmdtf8r5ax4r"},
        "Bhubaneswar": {"state_id": "ay9qibiat1o49awc50hqcvi0", "city_id": "bc0frxyes3sdo9ht3t1ukdu7"},
        "Guwahati": {"state_id": "mjrnp3xl3jt7cj3d4tyfbp2v", "city_id": "hi8k1mymduu9m860ilwylokl"},
        "Mumbai": {"state_id": "ovhhwugrqp35xqou86kot42j", "city_id": "x96mxx3r7qvfjvo3nqqq7i94"},
        "Patna": {"state_id": "i0czi43fje0vw9ewufiycxlh", "city_id": "lh3hr6zb7thewa2bx6d11p89"},
        "Ranchi": {"state_id": "gjvwezxb801bs6smab9ukse8", "city_id": "kff8heh6rmi3xogfsbhf0qri"},
        "Raipur": {"state_id": "wgfcodn8u6hc74hk3jpoeex8", "city_id": "msd324rumx2qv5vslm4o64wl"},
        "Lucknow": {"state_id": "xavsspxxllf5ffmdbfefhogn", "city_id": "rcpcut32ak0y5xh682hzzurs"},
        "Indore": {"state_id": "rxlad1jra43e5m8afq439i1j", "city_id": "vu8xd94wp8r35yfg8gseufl8"},
        "Nagpur": {"state_id": "ovhhwugrqp35xqou86kot42j", "city_id": "vn01xpzxu4icnspqonlyk97i"},
        "Pune": {"state_id": "ovhhwugrqp35xqou86kot42j", "city_id": "mmsguh2uvh9fe44z4bvzsn9c"},
        "Bangalore": {"state_id": "c37mostb25wv2y1gla7gk1ep", "city_id": "u9j4srq7c1ksc1k3zdvp13ro"},
        "Hubli": {"state_id": "c37mostb25wv2y1gla7gk1ep", "city_id": "yw5u0rfy5jna35lo7qrve1zm"},
        "Goa": {"state_id": "vve1p90o2nbl4rdwpaeazvg5", "city_id": None},
        "Hyderabad": {"state_id": "v4q72ukaz5mnoibi04mig983", "city_id": "pp424s4aggw9i7gfc2rjztku"},
        "Gujarat": {"state_id": "gbaba6v0fdpxdor33idi4b7k", "city_id": None},
        "Chennai": {"state_id": "ylgwnbiuuig4fjfcdrbricuw", "city_id": "xghyrueg2lqku5mu21jhx7u3"},
        "Coimbatore": {"state_id": "ylgwnbiuuig4fjfcdrbricuw", "city_id": "s9fy2tqawyxtnqsmv1oqsju2"},
        "Kochi": {"state_id": "ij5h3gu68ws930k3h4rw5rhg", "city_id": "zac39z4bvni9gfk36q2ghst1"},
        "Delhi": {"state_id": "tcj7jpgyv7u10g9ehvoukkn9", "city_id": "a6thqxzokmycosptpsg1apxf"},
        "Gurgaon": {"state_id": "tgmp83wdxtzpwhi9ct04dx78", "city_id": "wkj9m1hm5k3k7kmcytcpx7ni"},
        "Ghaziabad": {"state_id": "xavsspxxllf5ffmdbfefhogn", "city_id": "tmcu82c5h9q191nt7a2b9zze"},
        "Ludhiana": {"state_id": "ohu0agqyqak53av22sh7b8dv", "city_id": "rtj6duujmvl4u19w9viv5cph"},
        "Rajasthan": {"state_id": "xuzluw9vmvanj1x68j0e8kim", "city_id": None},
        "Uttarakhand": {"state_id": "bvyudpqr6kag97dc372zwjaf", "city_id": None},
        "Haryana": {"state_id": "tgmp83wdxtzpwhi9ct04dx78", "city_id": None},
    }

    main(json_file_path, document_mapping)
