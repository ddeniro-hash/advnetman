#!/usr/bin/env python3

from netmiko import ConnectHandler


def read_passwords_from_file(filename="/home/student/passwords.txt"):
    """Read passwords from a specified file and return as a dictionary."""
    passwords = {}
    try:
        with open(filename, "r") as file:
            for line in file:
                device, password = line.strip().split(": ")
                passwords[device] = password
        print("Passwords loaded successfully.")
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return passwords


if __name__ == "__main__":
    # Read passwords into a dictionary
    passwords = read_passwords_from_file()

    # Device information (update with your actual device IPs)
    devices = {
        "R1": "10.10.200.1",
        "R2": "10.10.200.2",
        "R3": "10.10.200.3",
        "R4": "10.10.200.4",
        "SW1": "10.10.201.12",
        "SW2": "10.10.201.22",
        "SW3": "10.10.200.32",
        "SW4": "10.10.200.42",
    }

    # User details
    username = "netuser"

    # Connect and configure each device
    for device_name, host in devices.items():
        device = {
            "device_type": "arista_eos",  # Change this to your device type as needed
            "host": host,
            "username": "admin",  # Admin username
            "password": "admin",  # Admin password
        }

        # Get the password for the new user from the passwords dictionary
        new_user_password = passwords.get(device_name, "")
        if not new_user_password:
            print(f"No password found for {device_name}. Skipping...")
            continue  # Skip this device if no password is found

        try:
            # Establishing the SSH connection
            connection = ConnectHandler(**device)
            connection.enable()

            # Constructing the command to create a new user
            command = f"username {username} privilege 15 role network-admin secret {new_user_password}"

            # Sending the command
            output = connection.send_config_set(command)

            # Print the output
            print(f"Output from {device_name} ({host}):\n{output}\n")

            # Closing the connection
            connection.disconnect()

        except Exception as e:
            print(f"An error occurred while connecting to {device_name}: {e}")
