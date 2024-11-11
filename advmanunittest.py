#!/usr/bin/env python3

import unittest
import re
import os
import subprocess
from netmiko import ConnectHandler
import pyeapi

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

    def test_ip_formatting(self):
        """Test that the IP addresses are properly formatted."""
        for device, ip in devices.items():
            self.assertRegex(ip, regex, f"{device} IP {ip} is not properly formatted.")
            print(f"{device} IP {ip} is properly formatted.")
            
    def test_mac_formatting_in_code(self):
        """Test that MAC addresses in the sudotftp2.py file are properly formatted."""
        # Path to the file to check
        file_path = "/home/student/flask_app/sudotftp2.py"
        
        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Find all MAC addresses in the code using regex
        mac_addresses = re.findall(mac_regex, content)
        
        # Test each MAC address for proper formatting
        for mac in mac_addresses:
            mac_str = "".join(mac)  # Convert tuple to MAC string
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
