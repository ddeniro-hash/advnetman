#!/usr/bin/env python3

from netmiko import ConnectHandler

# List of devices with their details
devices = [
    {'name': 'R1', 'ip': '10.10.200.1', 'device_type': 'arista_eos'},
    {'name': 'R2', 'ip': '10.10.200.2', 'device_type': 'arista_eos'},
    {'name': 'R3', 'ip': '10.10.200.3', 'device_type': 'arista_eos'},
    {'name': 'R4', 'ip': '10.10.200.4', 'device_type': 'arista_eos'},
    {'name': 'SW1', 'ip': '10.10.201.12', 'device_type': 'arista_eos'},
    {'name': 'SW2', 'ip': '10.10.201.22', 'device_type': 'arista_eos'},
    {'name': 'SW3', 'ip': '10.10.200.32', 'device_type': 'arista_eos'},
    {'name': 'SW4', 'ip': '10.10.200.42', 'device_type': 'arista_eos'},
]

# Device credentials (replace with actual credentials)
username = 'admin'
password = 'admin'

# Loop through each device and perform the command
for device in devices:
    try:
        print(f"Connecting to {device['name']} at {device['ip']}...")

        # Establish connection to the device
        connection = ConnectHandler(
            device_type=device['device_type'],
            host=device['ip'],
            username=username,
            password=password
        )
        
        # Enter enable mode if necessary
        connection.enable()

        # Execute the command and retrieve the output
        output = connection.send_command("show running-config")
        
        # Print the output
        print(f"--- Output from {device['name']} ---")
        print(output)
        print("\n" + "-" * 50 + "\n")
        
        # Disconnect from the device
        connection.disconnect()
        
    except Exception as e:
        print(f"Failed to connect to {device['name']} at {device['ip']}: {e}")
