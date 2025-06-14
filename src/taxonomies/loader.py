import json
from pathlib import Path

def get_taxonomy_map():
    raw = json.loads(Path("data/taxonomies.json").read_text())
    return {
        t["taxonomy_name"]: [
            elem["label"]["value"] for elem in t["elements"]
        ]
        for t in raw["aiod_taxonomies"]
    }