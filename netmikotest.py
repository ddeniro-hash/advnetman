#!/usr/bin/env python3

from netmiko import ConnectHandler

# Device information
device = {
    "device_type": "arista_eos",  # Change this to your device type (e.g., 'arista_eos', 'juniper', etc.)
    "host": "10.10.200.1",  # Replace with the device IP address or hostname
    "username": "netuser",  # Replace with your username
    "password": "KrnxaS1NaCOP",  # Secure password input
}

try:
    # Establishing the SSH connection
    connection = ConnectHandler(**device)
    connection.enable()

    # Sending the command and storing the output
    output = connection.send_command("show running-config")

    # Print the output
    print(output)

    # Closing the connection
    connection.disconnect()

except Exception as e:
    print(f"An error occurred: {e}")
