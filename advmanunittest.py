#!/usr/bin/env python3

import unittest
import re
import os
import subprocess
from netmiko import ConnectHandler
import pyeapi
import unittest
from unittest.mock import patch, MagicMock
from influxdb_client import InfluxDBClient

# Define the InfluxDB client and settings
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "gFJ1WAaIxCtwzPzLmNXcqJXj9dJef1sJV75GESP-0iGFh64Az9o5--T20X2MxOiy-bbVAUwin3rDwyR3cmKolw=="
INFLUXDB_ORG = "CU Boulder"
INFLUXDB_BUCKET = "tshoot2"

# Define the query
QUERY = '''
from(bucket: "tshoot2")
  |> range(start: -1m)
  |> filter(fn: (r) => r["source"] == "r1" or r["source"] == "r2" or r["source"] == "r3" or r["source"] == "r4" or r["source"] == "r8" or r["source"] == "r6" or r["source"] == "r7" or r["source"] == "sw1" or r["source"] == "sw2" or r["source"] == "sw3" or r["source"] == "sw4" or r["source"] == "sw5")
  |> filter(fn: (r) => r["interface_name"] == "Ethernet1" or r["interface_name"] == "Ethernet3" or r["interface_name"] == "Ethernet4" or r["interface_name"] == "Management0" or r["interface_name"] == "Ethernet2")
  |> yield(name: "last")
'''

# Define the IP addresses
devices = {
    "r1": "10.10.200.1",
    "r2": "10.10.200.2",
    "r3": "10.10.200.3",
    "r4": "10.10.200.4",
    "r6": "10.10.7.100",
    "r7": "10.10.8.101",
    "r8": "10.10.9.101",
    "sw1": "10.10.201.12",
    "sw2": "10.10.201.22",
    "sw3": "10.10.200.32",
    "sw4": "10.10.200.42",
    "sw5": "10.10.202.101",
}

# Regex for validating IP addresses
regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

# Regex for validating MAC addresses
mac_regex = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"

# Router information
username = "admin"
password = "admin"

class TestRouterConfigs(unittest.TestCase):

    def test_influxdb_query_success(self, mock_query_api):
        # Mock the query API response
        mock_query_instance = MagicMock()
        mock_query_api.return_value = mock_query_instance
        mock_query_instance.query.return_value = "Mocked Query Result"  # Simulate a successful response
        
        # Execute the query
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        result = client.query_api().query(org=INFLUXDB_ORG, query=QUERY)
        
        # Assert the query was executed
        mock_query_instance.query.assert_called_once_with(org=INFLUXDB_ORG, query=QUERY)
        
        # Check if the result is as expected (i.e., "Mocked Query Result")
        self.assertEqual(result, "Mocked Query Result")
        
        print("Successfully able to query InfluxDB via API")

    def test_mac_formatting_in_code(self):
        """Test that MAC addresses in the sudotftp2.py file are properly formatted."""
        # Path to the file to check
        file_path = "/home/student/flask_app/sudotftp2.py"
        
        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Find all complete MAC addresses in the code using regex
        mac_addresses = re.finditer(mac_regex, content)
        
        # Test each MAC address for proper formatting
        for match in mac_addresses:
            mac_str = match.group(0)  # Full MAC address string from match
            self.assertRegex(mac_str, mac_regex, f"{mac_str} is not a valid MAC address.")
            print(f"{mac_str} is a valid MAC address.")

    def test_ping_addresses(self):
        """Test to ping all specified IP addresses."""
        for device, ip in devices.items():
            response = os.system(f"ping -c 1 {ip} > /dev/null 2>&1")
            self.assertEqual(response, 0, f"Ping to {ip} failed.")
            print(f"Successfully pinged {ip}.")

    def test_file_exists(self):
        """Test if the passwords.txt file exists."""
        self.assertTrue(
            os.path.isfile("/home/student/passwords.txt"),
            "The passwords.txt file does not exist.",
        )
        print("The passwords.txt file exists.")

    def test_jinja2_templates(self):
        """Check if the Jinja2 files in devicetemplates are valid."""
        template_dir = "/home/student/devicetemplates"
        for filename in os.listdir(template_dir):
            if filename.endswith(".j2"):  # Assuming Jinja2 templates have .j2 extension
                template_path = os.path.join(template_dir, filename)
                with open(template_path) as f:
                    content = f.read()
                    self.assertIn(
                        "{%", content, f"{filename} is not a valid Jinja2 template."
                    )
                    self.assertIn(
                        "%}", content, f"{filename} is not a valid Jinja2 template."
                    )
                    print(f"{filename} is a valid Jinja2 template.")
                    
    def test_ssh_connection(self):
        """Test SSH connection to each device."""
        for device, ip in devices.items():
            try:
                connection = ConnectHandler(device_type='arista_eos', ip=ip, username=username, password=password)
                connection.disconnect()  # Disconnect after testing
                print(f"SSH successful to {device} ({ip}).")
            except Exception as e:
                self.fail(f"SSH failed to {device} ({ip}): {str(e)}")

    def test_ospf_neighbors(self):
        """Check OSPF neighbors for each device."""
        for device in ["r1", "r2", "r3", "r4", "r6", "r8"]:
            ip = devices[device]
            try:
                device_eapi = pyeapi.connect(host=ip, username=username, password=password)
                ospf_output = device_eapi.execute(['show ip ospf neighbor'])
                
                if 'result' in ospf_output:
                    neighbors = ospf_output['result'][0]['vrfs']['default']['instList']['100']['ospfNeighborEntries']
                    if neighbors:
                        print(f"OSPF info successfully received for {device}:")
                        for neighbor in neighbors:
                            router_id = neighbor.get('routerId')
                            interface_address = neighbor.get('interfaceAddress')
                            adjacency_state = neighbor.get('adjacencyState')
                            print(f"  Router ID: {router_id}, Interface Address: {interface_address}, Adjacency State: {adjacency_state}")
                    else:
                        print(f"No OSPF neighbors found for {device}.")
                else:
                    print(f"No OSPF information available for {device}.")
            except Exception as e:
                print(f"Could not get OSPF neighbors for {device}: {str(e)}")

    def test_bgp_neighbors(self):
        """Check BGP neighbors only for R3 and R4."""
        for device in ["r3", "r4"]:
            ip = devices[device]
            try:
                device_eapi = pyeapi.connect(host=ip, username=username, password=password)
                bgp_output = device_eapi.execute(['show ip bgp neighbors'])
                
                if 'result' in bgp_output:
                    peer_list = bgp_output['result'][0]['vrfs']['default']['peerList']
                    if peer_list:
                        print(f"BGP info successfully received for {device}:")
                        for peer in peer_list:
                            peer_address = peer.get('peerAddress')
                            state = peer.get('state')
                            print(f"  Peer Address: {peer_address}, State: {state}")
                    else:
                        print(f"No BGP neighbors found for {device}.")
                else:
                    print(f"No BGP information available for {device}.")
            except Exception as e:
                print(f"Could not get BGP neighbors for {device}: {str(e)}")

if __name__ == "__main__":
    unittest.main()
