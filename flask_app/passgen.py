#!/usr/bin/env python3
import random
import string


def generate_random_password(length=12):
    """Generate a random password with uppercase, lowercase, and digits."""
    all_characters = string.ascii_letters + string.digits  # Only letters and digits
    password = "".join(random.choice(all_characters) for _ in range(length))
    return password


def save_passwords_to_file(passwords, filename="passwords.txt"):
    """Save the passwords to a specified file."""
    with open(filename, "w") as file:
        for device, password in passwords.items():
            file.write(f"{device}: {password}\n")
    print(f"Passwords saved to {filename}")


if __name__ == "__main__":
    devices = ["R1", "R2", "R3", "R4","R6","R7", "R8", "SW1", "SW2", "SW3", "SW4", "SW5"]  # List of devices
    password_length = 12  # Set the desired length of the password
    passwords = {
        device: generate_random_password(password_length) for device in devices
    }  # Generate passwords

    save_passwords_to_file(passwords)  # Save passwords to file
