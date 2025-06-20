import json

import requests

URL = "https://api.tfl.gov.uk/BikePoint"


def main() -> None:
    # get the BikePoint feed and print the first station's JSON, nicely formatted
    data = requests.get(URL, timeout=30).json()
    print(json.dumps(data[:1], indent=2))


if __name__ == "__main__":
    main()
