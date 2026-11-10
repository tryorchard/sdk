"""List sandboxes. Usage: python quickstart.py"""
from orchard_sdk import Orchard

with Orchard.from_env() as orchard:
    me = orchard.me()
    print("authenticated as", me.get("username"), "in", me.get("active", {}).get("name"))

    for s in orchard.sandboxes.list()["instances"]:
        print(f"  {s['name']:<18} {s['state']:<9} tag={s.get('tag') or '-'}")
