#!/usr/bin/env python3

import ast

# List of target functions to check for code coverage
target_functions = [
    "test_bgp_neighbors",
    "test_file_exists",
    "test_ip_formatting",
    "test_jinja2_templates",
    "test_ospf_neighbors",
    "test_ping_addresses",
    "test_ssh_connection",
    "test_mac_formatting_in_code",
    "test_yaml_to_jinja",
    "test_file_exists_goldenconfig",
    "test_check_netboxapi",
]

def get_coverage(file_path):
    # Parse the Python file and extract its Abstract Syntax Tree (AST)
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    # Initialize coverage and track found functions
    coverage = 0
    found_functions = []

    # Look for function definitions within TestRouterConfigs class
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "TestRouterConfigs":
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    func_name = child.name
                    if func_name in target_functions:
                        found_functions.append(func_name)
                        coverage += 10

    # Output results
    print(f"Found functions: {found_functions}")
    print(f"Total Code Coverage: {coverage}%")

# Run the coverage check on pyappsunittest.py
get_coverage("advmanunittest.py")
