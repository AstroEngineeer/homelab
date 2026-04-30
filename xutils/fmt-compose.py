import glob
import sys
import yaml
from pathlib import Path

RECOMMENDED_ORDER = ["networks", "volumes", "secrets", "configs", "services"]

REPO_ROOT = Path(__file__).parent.parent


def convert_value(value):
    if not isinstance(value, str):
        return value
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def to_sorted_dict(section):
    if isinstance(section, list):
        result = {}
        for item in section:
            if isinstance(item, str) and "=" in item:
                key, value = item.split("=", 1)
                result[key] = convert_value(value)
            elif isinstance(item, str):
                result[item] = ""
        return dict(sorted(result.items()))
    if isinstance(section, dict):
        return dict(sorted(section.items()))
    return section


def to_expanded_volume(volume):
    if isinstance(volume, dict):
        if {"type", "source", "target"}.issubset(volume.keys()):
            return volume
        print(f"  warning: skipping malformed volume: {volume}")
        return None
    if isinstance(volume, str):
        parts = volume.split(":")
        if len(parts) == 2:
            source, target = parts
            return {"type": "bind", "source": source, "target": target, "read_only": False}
        if len(parts) == 3:
            source, target, options = parts
            return {"type": "bind", "source": source, "target": target, "read_only": "ro" in options}
    print(f"  warning: skipping unrecognised volume: {volume}")
    return None


def normalise_service(config):
    if "environment" in config:
        config["environment"] = to_sorted_dict(config["environment"])
    if "labels" in config:
        config["labels"] = to_sorted_dict(config["labels"])
    if "volumes" in config:
        expanded = [to_expanded_volume(v) for v in config["volumes"]]
        config["volumes"] = [v for v in expanded if v is not None]
    if "secrets" in config:
        config["secrets"] = sorted(config["secrets"])
    return dict(sorted(config.items()))


def reorder_compose(path):
    try:
        data = yaml.safe_load(Path(path).read_text())
        if not isinstance(data, dict):
            print(f"  skipping {path}: not a mapping")
            return

        for section in ("networks", "volumes", "secrets", "configs"):
            if section in data and isinstance(data[section], dict):
                data[section] = dict(sorted(data[section].items()))

        if "services" in data and isinstance(data["services"], dict):
            data["services"] = {
                name: normalise_service(cfg)
                for name, cfg in sorted(data["services"].items())
            }

        # Known keys first, then any unrecognised keys appended at the end
        ordered = {k: data[k] for k in RECOMMENDED_ORDER if k in data}
        ordered.update({k: v for k, v in data.items() if k not in ordered})

        with open(path, "w") as f:
            for i, (key, value) in enumerate(ordered.items()):
                yaml.dump(
                    {key: value}, f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    default_style=None,
                )
                if i < len(ordered) - 1:
                    f.write("\n")

        print(f"  formatted: {path}")
    except Exception as e:
        print(f"  error processing {path}: {e}")


def find_compose_files():
    patterns = ["**/compose.yaml", "**/docker-compose.yml", "**/docker-compose.yaml"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(str(REPO_ROOT / pattern), recursive=True))
    return sorted(f for f in files if "container_data" not in f)


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else find_compose_files()
    if not targets:
        print("No compose files found.")
        sys.exit(0)
    for path in targets:
        print(f"processing: {path}")
        reorder_compose(path)
