import schedule
import time
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
from netmiko import ConnectHandler, logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configure logging
logging.basicConfig(filename="/home/student/gitrepo/advnetman/netmiko_session.log", level=logging.DEBUG)

# InfluxDB settings
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "gFJ1WAaIxCtwzPzLmNXcqJXj9dJef1sJV75GESP-0iGFh64Az9o5--T20X2MxOiy-bbVAUwin3rDwyR3cmKolw=="
INFLUXDB_ORG = "CU Boulder"
INFLUXDB_BUCKET = "tshoot2"

# Device credentials
TARGETS = {
    "r1": {"address": "10.10.200.1", "username": "admin", "password": "admin"},
    "r2": {"address": "10.10.200.2", "username": "admin", "password": "admin"},
    "r3": {"address": "10.10.200.3", "username": "admin", "password": "admin"},
    "r4": {"address": "10.10.200.4", "username": "admin", "password": "admin"},
    "r6": {"address": "10.10.7.100", "username": "admin", "password": "admin"},
    "r7": {"address": "10.10.8.101", "username": "admin", "password": "admin"},
    "r8": {"address": "10.10.9.101", "username": "admin", "password": "admin"},
    "sw4": {"address": "10.10.200.42", "username": "admin", "password": "admin"},
    "sw3": {"address": "10.10.200.32", "username": "admin", "password": "admin"},
    "sw1": {"address": "10.10.201.12", "username": "admin", "password": "admin"},
    "sw2": {"address": "10.10.201.22", "username": "admin", "password": "admin"},
    "sw5": {"address": "10.10.202.101", "username": "admin", "password": "admin"},
}

# Email settings
SENDER_EMAIL = "dantedeniro@gmail.com"
# Read the sender password from the file
def read_sender_password(file_path="/home/student/gitrepo/advnetman/email_credentials.txt"):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()  # Read the password and remove any extra whitespace
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except Exception as e:
        print(f"Error reading the password file: {e}")
        return None

# Get the sender password from the file
SENDER_PASSWORD = read_sender_password()

# Check if the password was successfully loaded
RECIPIENT_EMAIL = "dantedeniro@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Cooldown tracker
last_action = {}

# Cooldown duration (in seconds)
COOLDOWN = 60

# Create the InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)

# Define the InfluxDB query
QUERY = '''
from(bucket: "tshoot2")
  |> range(start: -1m)
  |> filter(fn: (r) => r["source"] == "r1" or r["source"] == "r2" or r["source"] == "r3" or r["source"] == "r4" or r["source"] == "r8" or r["source"] == "r6" or r["source"] == "r7" or r["source"] == "sw1" or r["source"] == "sw2" or r["source"] == "sw3" or r["source"] == "sw4" or r["source"] == "sw5")
  |> filter(fn: (r) => r["interface_name"] == "Ethernet1" or r["interface_name"] == "Ethernet3" or r["interface_name"] == "Ethernet4" or r["interface_name"] == "Management0" or r["interface_name"] == "Ethernet2")
  |> yield(name: "last")
'''

# Execute the query
query_api = client.query_api()
result = query_api.query(org=INFLUXDB_ORG, query=QUERY)

# Print the results
print("\n--- Query Results ---")
for table in result:
    for record in table.records:
        print(
            f"Source: {record['source']:<6} | "
            f"Interface: {record['interface_name']:<12} | "
            f"Status: {record['_value']:<5} | "
            f"Time: {record['_time']}"
        )
print("\n")

# Close the InfluxDB client connection
client.close()

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            text = msg.as_string()
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, text)

        print(f"[INFO] Email sent to {RECIPIENT_EMAIL}.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

def troubleshoot_device(device_name, device_info, interface):
    device = {
        "device_type": "arista_eos",
        "ip": device_info["address"],
        "username": device_info["username"],
        "password": device_info["password"],
    }
    try:
        connection = ConnectHandler(**device)
        connection.enable()
        print(f"\n[INFO] Connected to {device_name} ({device_info['address']})")

        commands = [
            f"show interface {interface}",
            f"show ip interface {interface}",
            f"ping 10.10.200.100",
            f"interface {interface}",
            "shut",
            "no shut",
        ]

        output_str = f"Troubleshooting steps for {device_name} on interface {interface}:\n"
        print(f"\n[COMMANDS EXECUTED FOR {device_name.upper()} ON {interface.upper()}]:")
        for idx, command in enumerate(commands, start=1):
            if command.startswith("show") or command.startswith("ping"):
                output = connection.send_command(command)
            elif command.startswith("interface") or command in ["shut", "no shut"]:
                if command.startswith("interface"):
                    output = connection.send_config_set([command])
                else:
                    output = connection.send_config_set([f"interface {interface}", command])
            else:
                output = connection.send_config_set([command])

            output_str += f"[{idx}] Command: {command}\n{output.strip()}\n\n"

        print(output_str)
        send_email(f"Interface {interface} on {device_name} is DOWN", output_str)

        print("\n[INFO] Finished executing commands.\n")
        connection.disconnect()

        last_action[(device_name, interface)] = datetime.now()

    except Exception as e:
        print(f"[ERROR] Unable to connect to {device_name} ({device_info['address']}): {e}")

def main():
    global last_action
    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        query_api = client.query_api()

        print("\n[INFO] Executing InfluxDB Query...")
        result = query_api.query(org=INFLUXDB_ORG, query=QUERY)

        if not result or all(len(table.records) == 0 for table in result):
            print("[INFO] No links are down.\n")
            return

        for table in result:
            for record in table.records:
                device_name = record["source"]
                interface = record["interface_name"]

                if device_name in TARGETS:
                    status = record["_value"]
                    if status == "DOWN":
                        last_time = last_action.get((device_name, interface))
                        if last_time and datetime.now() - last_time < timedelta(seconds=COOLDOWN):
                            print(f"[INFO] Cooldown in effect for {device_name} {interface}. Skipping.\n")
                            continue

                        print(f"[ALERT] Interface {interface} on {device_name} is DOWN.")
                        troubleshoot_device(device_name, TARGETS[device_name], interface)
                    else:
                        print(f"[INFO] Interface {interface} on {device_name} is UP.")
                else:
                    print(f"[WARNING] Device {device_name} not found in TARGETS.\n")

# Schedule the script
schedule.every(5).seconds.do(main)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)
