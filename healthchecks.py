#!/usr/bin/env python3

import requests
import warnings
from netmiko import ConnectHandler

# Suppress InsecureRequestWarning
warnings.filterwarnings(
    "ignore", message="Unverified HTTPS request is being made to host"
)


def read_passwords_from_file(filename="/home/student/passwords.txt"):
    """Read passwords from a specified file and return as a dictionary."""
    passwords = {}
    try:
        with open(filename, "r") as file:
            for line in file:
                if ": " in line:
                    device, password = line.strip().split(": ")
                    # Convert device names to lowercase
                    passwords[device.lower()] = password
                else:
                    print(f"Skipping invalid line: {line.strip()}")
        print("Passwords loaded successfully.")
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return passwords


# NetBox IP Fetcher Class
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
                ip_address = data["results"][0]["address"].split("/")[
                    0
                ]  # Get the IP without suffix
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


# Network Automation Health Check Class
class NetworkHealthCheck:
    def __init__(self, device_params):
        self.device_params = device_params

    def check_route_table(self):
        """Check the routing table for routers only."""
        device_name = self.device_params.get("device_name")

        if device_name == "r1" or "r2" or "r3" or "r4":
            try:
                net_connect = ConnectHandler(**self.device_params)
                net_connect.enable()
                return net_connect.send_command("show ip route")
            except Exception as e:
                print(f"Failed to check routing table for {device_name}. Error: {e}")
                return None
        elif device_name == "sw1" or "sw2" or "sw3" or "sw4":
            print(f"Routing table check skipped for {device_name}. Not a router.")
            return None

    def check_ospf_neighbors(self):
        """Check OSPF neighbors for routers only."""
        device_name = self.device_params.get("device_name")

        if device_name == "r1" or "r2" or "r3" or "r4":
            try:
                net_connect = ConnectHandler(**self.device_params)
                net_connect.enable()
                return net_connect.send_command("show ip ospf neighbor")
            except Exception as e:
                print(f"Failed to check OSPF neighbors for {device_name}. Error: {e}")
                return None
        elif device_name == "sw1" or "sw2" or "sw3" or "sw4":
            print(f"OSPF neighbor check skipped for {device_name}. Not a router.")
            return None

    def check_bgp_neighbors(self):
        """Check BGP neighbors for devices R3 and R4 only."""
        device_name = self.device_params.get("device_name")

        if device_name == "r3" or "r4":
            try:
                net_connect = ConnectHandler(**self.device_params)
                net_connect.enable()
                return net_connect.send_command("show ip bgp summary")
            except Exception as e:
                print(f"Failed to check BGP neighbors for {device_name}. Error: {e}")
                return None
        elif device_name == "sw1" or "sw2" or "sw3" or "sw4":
            print(
                f"BGP neighbor check skipped for {device_name}. Only R3 and R4 are supported."
            )
            return None

    def check_cpu_utilization(self):
        """Check CPU utilization of the device."""
        net_connect = ConnectHandler(**self.device_params)
        net_connect.enable()
        return net_connect.send_command("show snmp mib walk .1.3.6.1.2.1.25.3.3.1.2")

    def check_ip_connectivity(self, target_ip):
        """Check IP connectivity to a target IP."""
        net_connect = ConnectHandler(**self.device_params)
        net_connect.enable()
        return net_connect.send_command(f"ping {target_ip}")


# Main Function
def main():
    # Define NetBox API details
    api_url = "https://127.0.0.1/api/ipam/ip-addresses/"
    token = "f204e7a30dd20be312d033f4ec4e0096ddd1aaa5"

    # Fetch IPs from NetBox
    ip_fetcher = NetBoxIPFetcher(api_url, token)
    ip_fetcher.fetch_ips()

    # Read SSH passwords from file
    passwords = read_passwords_from_file()

    for device_name, ip_address in ip_fetcher.ip_addresses.items():
        print(f"Device: {device_name}, IP: {ip_address}")

        password = passwords.get(device_name)

        # Define the device parameters for Netmiko based on the fetched IP
        device_params = {
            "device_type": "arista_eos",  # Change as per device type
            "ip": ip_address,
            "username": "netuser",  # Add username logic if needed
            "password": password,
            "use_keys": False,
            "allow_agent": False,
        }

        # Create NetworkHealthCheck instance
        health_check = NetworkHealthCheck(device_params)

        # Perform health checks
        if device_name.lower() in ["r3", "r4"]:
            print(f"Checking BGP neighbors for {device_name}...")
            print(health_check.check_bgp_neighbors())

        print(f"Checking route table for {device_name}...")
        print(health_check.check_route_table())

        print(f"Checking OSPF neighbors for {device_name}...")
        print(health_check.check_ospf_neighbors())

        print(f"Checking CPU utilization for {device_name}...")
        print(health_check.check_cpu_utilization())

        print(f"Checking IP connectivity to 10.10.200.100 for {device_name}...")
        print(health_check.check_ip_connectivity("10.10.200.100"))


if __name__ == "__main__":
    main()
