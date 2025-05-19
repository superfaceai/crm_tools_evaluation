from dotenv import load_dotenv
import requests
import json
import time
import os

load_dotenv()

# 🔧 CONFIGURATION
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
    "Content-Type": "application/json"
}
BASE_URL = "https://api.hubapi.com"

# === Utility Functions ===

def get_all_ids(endpoint):
    url = f"{BASE_URL}{endpoint}"
    ids = []
    after = None
    while True:
        params = {"limit": 100}
        if after:
            params["after"] = after
        response = requests.get(url, headers=HEADERS, params=params).json()
        ids.extend([item["id"] for item in response.get("results", [])])
        if not response.get("paging") or not response["paging"].get("next"):
            break
        after = response["paging"]["next"]["after"]
    return ids

def delete_objects(endpoint, ids):
    for object_id in ids:
        del_url = f"{BASE_URL}{endpoint}/{object_id}"
        requests.delete(del_url, headers=HEADERS)

# === Reset Steps ===

def delete_all_contacts():
    contact_ids = get_all_ids("/crm/v3/objects/contacts")
    delete_objects("/crm/v3/objects/contacts", contact_ids)

def delete_all_companies():
    company_ids = get_all_ids("/crm/v3/objects/companies")
    delete_objects("/crm/v3/objects/companies", company_ids)

def delete_all_deals():
    deal_ids = get_all_ids("/crm/v3/objects/deals")
    delete_objects("/crm/v3/objects/deals", deal_ids)

def delete_tasks():
    tasks_ids = get_all_ids("/crm/v3/objects/tasks")
    delete_objects("/crm/v3/objects/tasks", tasks_ids)

def create_company(name, domain):
    data = {"properties": {"name": name, "domain": domain}}
    response = requests.post(f"{BASE_URL}/crm/v3/objects/companies", headers=HEADERS, json=data).json()
    return response.get("id")

def create_contact(name, email, lead_status):
    first, last = name.split(" ", 1)
    data = {
        "properties": {
            "firstname": first,
            "lastname": last,
            "email": email,
            "hs_lead_status": lead_status
        }
    }
    response = requests.post(f"{BASE_URL}/crm/v3/objects/contacts", headers=HEADERS, json=data).json()
    return response.get("id")

def create_deal(name, amount, stage):
    data = {
        "properties": {
            "dealname": name,
            "amount": amount,
            "dealstage": stage
        }
    }
    response = requests.post(f"{BASE_URL}/crm/v3/objects/deals", headers=HEADERS, json=data).json()
    return response.get("id")

def associate_contact_to_company(contact_id, company_id):
    url = f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}/associations/companies/{company_id}/contact_to_company"
    requests.put(url, headers=HEADERS)

def associate_deal_to_company(deal_id, company_id):
    url = f"{BASE_URL}/crm/v3/objects/deals/{deal_id}/associations/companies/{company_id}/deal_to_company"
    requests.put(url, headers=HEADERS)

def associate_deal_to_contact(deal_id, contact_id):
    url = f"{BASE_URL}/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}/deal_to_contact"
    requests.put(url, headers=HEADERS)

# === Main ===

def reset_hubspot(quiet=True):
    if not quiet:
        print("🚨 Deleting existing data...")

    if not quiet:
        print("🗑️ Deleting contacts...")
    delete_all_contacts()
    if not quiet:
        print("🗑️ Deleting companies...")
    delete_all_companies()
    if not quiet:
        print("🗑️ Deleting deals...")
    delete_all_deals()
    if not quiet:
        print("🗑️ Deleting tasks...")
    delete_tasks()

    if not quiet:
        print("📤 Loading initial data...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    companies_file = os.path.join(base_dir, "../data/companies.jsonl")
    contacts_file = os.path.join(base_dir, "../data/contacts.jsonl")
    deals_file = os.path.join(base_dir, "../data/deals.jsonl")

    with open(companies_file, "r") as f:
        companies_data = [json.loads(line) for line in f.readlines()]
    with open(contacts_file, "r") as f:
        contacts_data = [json.loads(line) for line in f.readlines()]
    with open(deals_file, "r") as f:
        deals_data = [json.loads(line) for line in f.readlines()]

    if not quiet:
        print("🏢 Creating companies...")

    company_map = {}
    for c in companies_data:
        company_id = create_company(c["name"], c["domain"])
        company_map[c["company_id"]] = company_id

    if not quiet:
        print("👤 Creating contacts and linking...")

    for contact in contacts_data:
        contact_id = create_contact(contact["name"], contact["email"], contact["lead_status"])
        hs_company_id = company_map[contact["company_id"]]
        associate_contact_to_company(contact_id, hs_company_id)

    for deal in deals_data:
        deal_id = create_deal(deal["name"], deal["amount"], deal["stage"])
        hs_company_id = company_map[deal["company_id"]]
        associate_deal_to_company(deal_id, hs_company_id)
        associate_deal_to_contact(deal_id, contact_id)

    if not quiet:
        print("✔️ Reset complete!")

if __name__ == "__main__":
    reset_hubspot(quiet=False)