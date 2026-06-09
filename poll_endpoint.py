import argparse
from time import sleep

from requests.exceptions import ConnectionError, HTTPError

from acceptance_tests.utilities.iap_requests import make_request


def poll_endpoint(url: str, max_retries: int, sleep_interval: int):
    for _attempts in range(max_retries):
        try:
            response = make_request(url=url)
            response.raise_for_status()
            print(f"Able to poll {url} endpoint. Exiting script")
            return
        except (ConnectionError, HTTPError):
            print(f"{url} is not available. Sleeping for {sleep_interval} second(s)")
            sleep(sleep_interval)
    print(f"Reached maximum number of retries on {url}. Stopping script")
    exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="This script polls an endpoint to check if it's available for the"
                    " Acceptance Tests to start running")
    parser.add_argument('--url', help='The url you want to poll', type=str, required=True)
    parser.add_argument('--max_retries', help='Maximum number of retries we want to check URL is up', type=int,
                        required=True)
    parser.add_argument('--sleep_interval', help='OPTIONAL: How long we want to sleep between retries in seconds',
                        type=int,
                        default=60)

    return parser.parse_args()


def main():
    args = parse_arguments()
    poll_endpoint(url=args.url, max_retries=args.max_retries, sleep_interval=args.sleep_interval)


if __name__ == "__main__":
    main()
