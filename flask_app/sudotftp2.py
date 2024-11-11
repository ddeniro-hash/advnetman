import pyeapi
from netmiko import ConnectHandler
import time

# Dictionary to keep track of which MAC addresses have received the configuration
sent_configs = {'aa:c1:ab:c0:24:9e': False, 'aa:c1:ab:88:f6:a2': False, 'aa:c1:ab:37:23:34': False, '00:1c:73:4c:07:17': False} 

def get_dhcp_binding(dhcpserver, mac_address):
    username = 'admin'
    password = 'admin'

    # Connect to the Arista device using pyeapi
    device_eapi = pyeapi.connect(host=dhcpserver, username=username, password=password)

    # Execute the command to get DHCP server information
    dhcp_output = device_eapi.execute(['show dhcp server leases'])

    # Extract DHCP lease information
    leases = dhcp_output['result'][0]['vrfs']['default']['ipv4ActiveLeases']
    for lease in leases:
        if lease['macAddress'] == mac_address:
            ip_address = lease['ipAddress']
            print(f"IP address for MAC {mac_address}: {ip_address}")
            return ip_address

    print(f"No IP address found for MAC {mac_address}")
    return None

def send_config_to_device(ip_address, config_file):
    # Define Netmiko connection details
    device = {
        'device_type': 'arista_eos',
        'ip': ip_address,
        'username': 'admin',
        'password': 'admin',
    }

    # Establish SSH connection using Netmiko
    try:
        with ConnectHandler(**device) as net_connect:
            print(f"Connected to {ip_address}")
            
            # Send configuration file
            net_connect.enable()
            output = net_connect.send_config_from_file(config_file)
            print(f"Configuration sent successfully to {ip_address}.")
    except Exception as e:
        print(f"Failed to connect or send configuration to {ip_address}: {e}")

def monitor_dhcp_and_configure():
    dhcpserver = '10.10.200.2'
    mac_addresses = {
        'aa:c1:ab:c0:24:9e': '/home/student/ztpconfigs/r6d1.txt',
        'aa:c1:ab:88:f6:a2': '/home/student/ztpconfigs/r7d1.txt',
        'aa:c1:ab:37:23:34': '/home/student/ztpconfigs/r8d1.txt',
        '00:1c:73:4c:07:17': '/home/student/ztpconfigs/sw5d1.txt'
    }

    while True:
        print("Checking DHCP binding...")
        for mac, config_file in mac_addresses.items():
            # Only send configuration if it hasn't been sent before
            if not sent_configs[mac]:
                ip_address = get_dhcp_binding(dhcpserver, mac)
                if ip_address:
                    send_config_to_device(ip_address, config_file)
                    sent_configs[mac] = True  # Mark this MAC as configured
                else:
                    print(f"No IP found for MAC {mac}, continuing check...")

            else:
                print(f"Configuration for MAC {mac} was already sent.")

        time.sleep(30)  # Wait 30 seconds before checking again

if __name__ == '__main__':
    monitor_dhcp_and_configure()
