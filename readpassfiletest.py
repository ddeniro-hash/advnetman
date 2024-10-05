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


# Read the passwords from the file
passwords = read_passwords_from_file()

# Assign passwords to variables for each device
r1pass = passwords.get(
    "R1", "default_password"
)  # Replace 'default_password' with a suitable fallback
r2pass = passwords.get("R2", "default_password")
r3pass = passwords.get("R3", "default_password")
r4pass = passwords.get("R4", "default_password")
sw1pass = passwords.get("SW1", "default_password")
sw2pass = passwords.get("SW2", "default_password")
sw3pass = passwords.get("SW3", "default_password")
sw4pass = passwords.get("SW4", "default_password")

print(r1pass)
print(r2pass)
print(r3pass)
print(r4pass)
print(sw1pass)
print(sw2pass)
print(sw3pass)
print(sw4pass)
