#!/usr/bin/env python3

# netbox_ip_fetcher.py
import requests
import warnings

# Suppress InsecureRequestWarning
warnings.filterwarnings(
    "ignore", message="Unverified HTTPS request is being made to host"
)


class NetBoxIPFetcher:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
        self.devices = {
            "r1": {"device_id": 1, "interface_id": 2},
            "r2": {"device_id": 2, "interface_id": 22},
            "r3": {"device_id": 3, "interface_id": 36},
            "r4": {"device_id": 4, "interface_id": 41},
            "sw1": {"device_id": 5, "interface_id": 48},
            "sw2": {"device_id": 6, "interface_id": 55},
            "sw3": {"device_id": 7, "interface_id": 61},
            "sw4": {"device_id": 8, "interface_id": 66},
        }
        self.ip_addresses = {}

    def fetch_ips(self):
        for device_name, info in self.devices.items():
            ip_address = self.get_ip(
                device_name, info["device_id"], info["interface_id"]
            )
            if ip_address:
                self.ip_addresses[device_name] = ip_address

    def get_ip(self, device_name, device_id, interface_id):
        params = {"device_id": device_id, "interface_id": interface_id}

        response = requests.get(
            self.api_url, headers=self.headers, params=params, verify=False
        )

        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                # Get the IP address and remove the /24 suffix
                ip_address = data["results"][0]["address"].split("/")[0]
                return ip_address
            else:
                print(f"{device_name}: No IP address found.")
                return None
        else:
            print(
                f"Failed to get IP for {device_name}. Status code: {response.status_code}"
            )
            return None

    def get_ip_address(self, device_name):
        return self.ip_addresses.get(device_name, None)
