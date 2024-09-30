#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request
from netmiko import ConnectHandler
from datetime import datetime
import os
import glob
import yaml
import re
import jinja2

app = Flask(__name__)

devices = [
    {'name': 'R1', 'ip': '10.10.200.1', 'device_type': 'cisco_ios'},
    {'name': 'R2', 'ip': '10.10.200.2', 'device_type': 'cisco_ios'},
    {'name': 'R3', 'ip': '10.10.200.3', 'device_type': 'cisco_ios'},
    {'name': 'R4', 'ip': '10.10.200.4', 'device_type': 'cisco_ios'},
    {'name': 'SW1', 'ip': '10.10.201.12', 'device_type': 'cisco_ios'},
    {'name': 'SW2', 'ip': '10.10.201.22', 'device_type': 'cisco_ios'},
    {'name': 'SW3', 'ip': '10.10.200.32', 'device_type': 'cisco_ios'},
    {'name': 'SW4', 'ip': '10.10.200.42', 'device_type': 'cisco_ios'},
]
username = 'admin'
password = 'admin'

# Route for home page
@app.route('/')
def home():
    return render_template('home.html')

# Route for monitoring page
@app.route('/monitoring')
def monitoring():
    return render_template('monitoring.html')

@app.route('/devices')
def device_list():
    return render_template('device_list.html', devices=devices)

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    if request.method == 'POST':
        device_name = request.form['device_name']
        interface = request.form['interface']
        new_ip_address = request.form.get('ip_address')  # New IP for the interface
        interface_status = request.form.get('interface_status')  # 'on' or 'off'
        routing_protocol = request.form.get('routing_protocol')  # Make this optional

        # Find the device based on the selected device name
        device = next((dev for dev in devices if dev['name'].lower() == device_name.lower()), None)

        if device:
            # Establish SSH connection using Netmiko
            connection = ConnectHandler(
                device_type=device['device_type'],
                host=device['ip'],
                username=username,
                password=password
            )

            # Prepare the commands to send to the device
            connection.enable()
            commands = []
            commands.append("configure terminal")
            commands.append(f"interface {interface}")

            # Set the IP address of the interface if provided
            if new_ip_address:
                commands.append(f"ip address {new_ip_address} 255.255.255.0")  # Example subnet mask

            # Change interface status if provided
            if interface_status:
                if interface_status == 'on':
                    commands.append("no shutdown")
                else:
                    commands.append("shutdown")

            # Handle routing protocol configurations only if selected
            if routing_protocol == 'ospf':
                ospf_area = request.form.get('ospf_area')
                ospf_network = request.form.get('ospf_network')  # Retrieve OSPF network
                ospf_mask = request.form.get('ospf_mask')
                if ospf_area and ospf_network and ospf_mask:  # Ensure area and network are provided
                    commands.append("router ospf 100")
                    commands.append(f"network {ospf_network} {ospf_mask} area {ospf_area}")  # Using example subnet
            elif routing_protocol == 'rip':
                rip_network = request.form.get('rip_network')  # Retrieve RIP network
                if rip_network:  # Ensure RIP network is provided
                    commands.append("router rip")
                    commands.append(f"network {rip_network}")
            elif routing_protocol == 'bgp':
                bgp_neighbor = request.form.get('bgp_neighbor')  # Retrieve BGP neighbor IP
                bgp_remote_as = request.form.get('bgp_remote_as')  # Retrieve BGP remote AS
                if bgp_neighbor and bgp_remote_as:  # Ensure both fields are provided
                    commands.append("router bgp 65000")  # Replace with actual AS number
                    commands.append(f"neighbor {bgp_neighbor} remote-as {bgp_remote_as}")

            # Send commands to the device
            output = connection.send_config_set(commands)
            connection.disconnect()

            return f"Configured {device_name} interface {interface} with IP {new_ip_address or 'N/A'}, status turned {interface_status or 'N/A'}, using {routing_protocol or 'N/A'} protocol.<br><pre>{output}</pre>"

    return render_template('configure.html')


@app.route('/save_config/<device_name>')
def save_config(device_name):
    # Find the device in the list
    device = next((d for d in devices if d['name'] == device_name), None)
    if not device:
        return f"Device {device_name} not found!", 404

    # Prepare the connection parameters, excluding 'name'
    connection_params = {
        'device_type': device['device_type'],
        'host': device['ip'],
        'username': username,  # Use the correct username here
        'password': password   # Use the correct password here
    }

    # Connect to the device and save the running config
    try:
        connection = ConnectHandler(**connection_params)
        connection.enable()
        output = connection.send_command("show running-config")
        
        # Save the running config to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_filename = f"/home/student/goldenconfigs/{device_name}_running_config_{timestamp}.txt"
        with open(config_filename, 'w') as f:
            f.write(output)

        connection.disconnect()
        return f"Running configuration for {device_name} saved as {config_filename}."

    except Exception as e:
        return str(e), 500

def convert_config_to_yaml(input_file):
    config_dict = {
        'hostname': None,
        'ospf': {},
        'rip': {},
        'bgp': {},  # Added BGP section
        'interfaces': {}
    }
    current_section = None

    with open(input_file, 'r') as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith('!'):
                continue

            if line.startswith('hostname'):
                config_dict['hostname'] = line.split()[1]
                continue

            elif line.startswith('router ospf'):
                current_section = 'ospf'
                ospf_id = line.split()[2]
                config_dict['ospf'][ospf_id] = {}

            elif line.startswith('router rip'):
                current_section = 'rip'
                config_dict['rip'] = {}

            elif line.startswith('router bgp'):
                current_section = 'bgp'
                bgp_as = line.split()[2]
                config_dict['bgp'] = {'as_number': bgp_as, 'neighbors': {}}

            elif current_section == 'ospf' and re.match(r'^\s*[\w-]+\s+.*', line):
                key_value = line.split(maxsplit=1)
                key = key_value[0].strip()
                value = key_value[1].strip() if len(key_value) > 1 else ''
                config_dict['ospf'][ospf_id][key] = value

            elif current_section == 'rip' and re.match(r'^\s*[\w-]+\s+.*', line):
                key_value = line.split(maxsplit=1)
                key = key_value[0].strip()
                value = key_value[1].strip() if len(key_value) > 1 else ''
                config_dict['rip'][key] = value

            elif current_section == 'bgp' and re.match(r'^\s*neighbor', line):
                parts = line.split()
                neighbor_ip = parts[1]
                config_dict['bgp']['neighbors'][neighbor_ip] = {}

            elif current_section == 'bgp' and re.match(r'^\s*[\w-]+\s+.*', line):
                key_value = line.split(maxsplit=1)
                key = key_value[0].strip()
                value = key_value[1].strip() if len(key_value) > 1 else ''
                if neighbor_ip in config_dict['bgp']['neighbors']:
                    config_dict['bgp']['neighbors'][neighbor_ip][key] = value

            elif line.startswith('interface'):
                interface_name = line.split()[1]
                current_section = f'interface_{interface_name}'
                config_dict['interfaces'][current_section] = {}

            elif re.match(r'^\s*[\w-]+\s+.*', line):
                if current_section in config_dict['interfaces']:
                    key_value = line.split(maxsplit=1)
                    key = key_value[0].strip()
                    value = key_value[1].strip() if len(key_value) > 1 else ''
                    config_dict['interfaces'][current_section][key] = value

    yaml_output = yaml.dump(config_dict, default_flow_style=False)

    hostname = config_dict['hostname']
    if hostname:
        output_file_path = f"/home/student/configtoyaml/{hostname}.yaml"
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, 'w') as yaml_file:
            yaml_file.write(yaml_output)
        print(f"YAML configuration saved to {output_file_path}")
    else:
        print("Error: Hostname is not set, not saving the YAML file.")

    return yaml_output

@app.route('/templatize')
def templatize():
    device_names = [device['name'] for device in devices]
    return render_template('templatize.html', device_names=device_names)

@app.route('/templatize_device', methods=['POST'])
def templatize_device():
    device_name = request.form['device_name']
    configs_path = f"/home/student/goldenconfigs/{device_name}_running_config_*.txt"
    
    files = glob.glob(configs_path)
    if not files:
        return f"No configuration files found for {device_name}.", 404

    latest_file = max(files, key=os.path.getmtime)

    try:
        yaml_content = convert_config_to_yaml(latest_file)
        # Redirect to a new page to offer templatizing option
        return render_template('templatize.html', result=device_name, templatize_option=True)
    except Exception as e:
        return f"Error converting configuration to YAML: {str(e)}", 500

def create_jinja2_template_from_yaml(yaml_file, template_name):
    with open(yaml_file, 'r') as f:
        config_data = yaml.safe_load(f)

    # Start the template content
    template_content = "hostname {{ hostname }}\n\n"

    # Add Interfaces section
    template_content += "{% if interfaces %}\n"
    template_content += "# Interface configurations\n"
    template_content += "{% for interface, settings in interfaces.items() %}\n"
    template_content += "interface {{ interface.split('_')[1] }}\n"
    template_content += "{% for key, value in settings.items() %}\n"
    template_content += "  {{ key }} {{ value }}\n"
    template_content += "{% endfor %}\n"
    template_content += "!\n"
    template_content += "{% endfor %}\n"
    template_content += "{% endif %}\n\n"

    # Add OSPF section if present
    template_content += "{% if ospf %}\n"
    template_content += "# OSPF configuration\n"
    template_content += "router ospf {{ ospf.keys() | first }}\n"
    template_content += "{% for key, value in ospf[ospf.keys() | first].items() %}\n"
    template_content += "  {{ key }} {{ value }}\n"
    template_content += "{% endfor %}\n"
    template_content += "!\n"
    template_content += "{% endif %}\n\n"

    # Add RIP section if present
    template_content += "{% if rip %}\n"
    template_content += "# RIP configuration\n"
    template_content += "router rip\n"
    template_content += "{% for key, value in rip.items() %}\n"
    template_content += "  {{ key }} {{ value }}\n"
    template_content += "{% endfor %}\n"
    template_content += "!\n"
    template_content += "{% endif %}\n\n"

    # Add BGP section if present
    template_content += "{% if bgp %}\n"
    template_content += "# BGP configuration (if any)\n"
    template_content += "router bgp {{ bgp.get('as_number', '') }}\n"
    template_content += "{% if bgp.neighbors %}\n"
    template_content += "  # BGP neighbors\n"
    template_content += "  {% for neighbor, neighbor_settings in bgp.neighbors.items() %}\n"
    template_content += "  neighbor {{ neighbor }}\n"
    template_content += "  {% for key, value in neighbor_settings.items() %}\n"
    template_content += "    {{ key }} {{ value }}\n"
    template_content += "  {% endfor %}\n"
    template_content += "  {% endfor %}\n"
    template_content += "{% endif %}\n"
    template_content += "!\n"
    template_content += "{% endif %}\n"

    # Save the generated template file
    template_path = f"/home/student/devicetemplates/{template_name}.j2"
    os.makedirs(os.path.dirname(template_path), exist_ok=True)

    with open(template_path, 'w') as template_file:
        template_file.write(template_content)

    print(f"Template saved to {template_path}")

@app.route('/generate_template', methods=['POST'])
def generate_template():
    device_name = request.form['device_name'].lower()  # Convert to lowercase

    # Define the template name based on device selection
    if device_name in ['r1', 'r2']:
        template_name = f"{device_name}_template"
    elif device_name in ['sw1', 'sw2']:
        template_name = f"{device_name}_template"
    elif device_name in ['sw3', 'sw4']:
        template_name = f"{device_name}_template"
    elif device_name in ['r3', 'r4']:
        template_name = f"{device_name}_template"
    else:
        return f"Unknown device: {device_name}", 400

    # Load the YAML configuration file
    yaml_file = f"/home/student/configtoyaml/{device_name}.yaml"
    if not os.path.exists(yaml_file):
        return f"No YAML file found for {device_name}.", 404

    # Call the function to create the Jinja2 template
    create_jinja2_template_from_yaml(yaml_file, template_name)

    return "Template created successfully.", 200


if __name__ == '__main__':
    app.run(debug=True)
