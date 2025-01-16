import yaml
import os
import glob

# Define the order for top-level keys
RECOMMENDED_ORDER = {
    "version": 0,
    "networks": 1,
    "volumes": 2,
    "secrets": 3,
    "configs": 4,
    "services": 5,
}

# Helper function to convert list-based sections to dict and sort alphabetically
def convert_to_dict_format(section_data):
    if isinstance(section_data, list):
        section_dict = {}
        for item in section_data:
            if isinstance(item, str) and '=' in item:
                key, value = item.split('=', 1)
                section_dict[key] = convert_value(value)  # Convert value to correct type
            elif isinstance(item, str):
                section_dict[item] = ''  # If no value is specified, set as empty string
        # Sort the dictionary alphabetically by key
        return dict(sorted(section_dict.items()))
    return section_data

# Function to convert volume definitions to the desired format
def convert_volumes(volumes):
    converted_volumes = []
    for volume in volumes:
        if isinstance(volume, str):
            source_target = volume.split(":")
            if len(source_target) == 2:
                source, target = source_target
                converted_volumes.append({
                    "type": "bind",
                    "source": source,
                    "target": target,
                    "read_only": False  # default to False; can adjust if needed
                })
            elif len(source_target) == 3:
                source, target, options = source_target
                read_only = 'ro' in options
                converted_volumes.append({
                    "type": "bind",
                    "source": source,
                    "target": target,
                    "read_only": read_only
                })
    return converted_volumes

# Function to convert strings to their appropriate types (e.g., bool, int)
def convert_value(value):
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    try:
        return int(value)  # Convert to integer if possible
    except ValueError:
        return value  # Return the string if it's not a recognized type

# Function to reorder and validate the structure of the compose file
def reorder_compose(compose_file):
    try:
        with open(compose_file, 'r') as file:
            data = yaml.safe_load(file)

        # Reorder the networks section
        if "networks" in data:
            ordered_networks = {key: data["networks"][key] for key in sorted(data["networks"].keys())}
            data["networks"] = ordered_networks

        # Reorder the volumes section
        if "volumes" in data:
            data["volumes"] = convert_volumes(data["volumes"])

        # Reorder the secrets section
        if "secrets" in data:
            data["secrets"] = convert_to_dict_format(data["secrets"])

        # Reorder the configs section
        if "configs" in data:
            data["configs"] = convert_to_dict_format(data["configs"])

        # Dynamically generate the SERVICE_KEYS based on the keys in the service configurations
        if "services" in data:
            for service_name, service_config in data["services"].items():
                # Generate SERVICE_KEYS dynamically from the keys in the service config
                service_keys = [key for key in service_config.keys()]
                
                # Ensure environment variables are in dict format and alphabetically ordered
                if "environment" in service_config:
                    service_config["environment"] = convert_to_dict_format(service_config["environment"])
                if "labels" in service_config:
                    service_config["labels"] = convert_to_dict_format(service_config["labels"])
                if "volumes" in service_config:
                    service_config["volumes"] = convert_volumes(service_config["volumes"])
                if "secrets" in service_config:
                    service_config["secrets"] = convert_to_dict_format(service_config["secrets"])
                if "configs" in service_config:
                    service_config["configs"] = convert_to_dict_format(service_config["configs"])
                
                # Reorder service keys based on dynamic service_keys and then sort alphabetically
                ordered_service_config = {key: service_config[key] for key in sorted(service_keys) if key in service_config}
                data["services"][service_name] = ordered_service_config

        # Reorder the top-level keys (version, volumes, secrets, configs)
        ordered_data = {}
        for key in RECOMMENDED_ORDER.keys():
            if key in data:
                ordered_data[key] = data[key]

        # Function to write the YAML with a blank line between top-level sections
        def dump_with_newlines(data, file):
            # Split the ordered data into top-level sections
            for idx, (key, value) in enumerate(ordered_data.items()):
                # Dump the section using yaml.dump with options to prevent quoting booleans and integers
                yaml.dump({key: value}, file, default_flow_style=False, sort_keys=False, allow_unicode=True, default_style=None)
                
                # Check if it’s not the last section, if not, add a new line
                if idx < len(ordered_data) - 1:
                    file.write("\n")

        # Write the reordered data back to the file
        with open(compose_file, 'w') as file:
            dump_with_newlines(ordered_data, file)

        print(f"{compose_file} has been reordered successfully.")

    except Exception as e:
        print(f"Error processing {compose_file}: {e}")

def find_compose_files():
    # Search for `compose.yaml` files, excluding the `./archive` path
    # return [file for file in glob.glob("./**/compose.yaml", recursive=True) if file.startswith("./archive/")]
    return ["./compose.yaml"]

if __name__ == "__main__":
    compose_files = find_compose_files()

    if not compose_files:
        print("No Docker Compose files found in the current folder.")
    else:
        for compose_file in compose_files:
            print(f"Reordering: {compose_file}")
            reorder_compose(compose_file)
