from dotenv import load_dotenv
import os
import json
import time
from simple_salesforce import Salesforce
import base64

load_dotenv(override=True)

# 🔧 CONFIGURATION
SF_USERNAME = os.getenv("SALESFORCE_USERNAME")
SF_PASSWORD = os.getenv("SALESFORCE_PASSWORD")
SF_SECURITY_TOKEN = os.getenv("SALESFORCE_SECURITY_TOKEN")
SF_DOMAIN = os.getenv("SALESFORCE_DOMAIN", "login")

sf = Salesforce(
    username=SF_USERNAME,
    password=SF_PASSWORD,
    security_token=SF_SECURITY_TOKEN,
    domain=SF_DOMAIN
)

# === Utility Functions ===
def get_all_ids(object_name):
    soql = f"SELECT Id FROM {object_name}"
    return [item['Id'] for item in sf.query_all(soql)['records']]

def delete_objects(object_name):
    ids = get_all_ids(object_name)
    for object_id in ids:
        getattr(sf, object_name).delete(object_id)
        time.sleep(0.1)  # avoid rate limits

# === Reset Steps ===
def delete_all_cases():
    delete_objects('Case')

def delete_all_leads():
    delete_objects('Lead')

def delete_all_contacts():
    delete_objects('Contact')

def delete_all_accounts():
    delete_objects('Account')

def delete_all_opportunities():
    delete_objects('Opportunity')

def delete_all_entitlements():
    delete_objects('Entitlement')

def create_account(name, domain):
    data = {"Name": name, "Website": domain}
    result = sf.Account.create(data)
    return result.get("id")

def create_contact(name, email, lead_source, account_id=None, title=None):
    first, last = name.split(" ", 1) if " " in name else (name, "")
    data = {
        "FirstName": first,
        "LastName": last,
        "Email": email,
        "LeadSource": lead_source,
    }
    if account_id:
        data["AccountId"] = account_id
    if title:
        data["Title"] = title
    result = sf.Contact.create(data)
    return result.get("id")

def create_lead(name, email, lead_status, company):
    first, last = name.split(" ", 1) if " " in name else (name, "")
    data = {
        "FirstName": first,
        "LastName": last,
        "Email": email,
        "Status": lead_status,
        "Company": company
    }
    result = sf.Lead.create(data)
    return result.get("id")

def create_opportunity(name, amount, stage, account_id=None):
    # Build data dictionary with all required fields and fixed picklist values
    data = {
        "Name": name,
        "Amount": amount,
        "StageName": "Prospecting",
        "Type": "CSPSellOut",
        "LeadSource": "Web",
        "DeliveryInstallationStatus__c": "In progress",
        "Primary_Competitor_Line_of_Business__c": "Commercial Client",
        "Primary_Competitor__c": "Alibaba",
        "Implementation_Type__c": "Distribuce",
        "Pre_sales_partner_activities__c": "EligibleBusinessCase",
        "Solution_Domain__c": "BasicHardwareSoftwareSale",
        "Solution_Type__c": "APOS",
        "Solution_Name__c": "ExpansionOrGrowth",
        "APEX_Opportunity__c": "No",
        "ISG_Tech_Refresh_Oppty__c": "No",
        "Solution_Scope__c": "ProfessionalServicesOnly",
        "Sales_Service_Delivery_Type__c": "DellServicesResell",
        "CloseDate": "2025-01-01",
        "AccountId": account_id
    }

    if account_id:
        data["AccountId"] = account_id

    try:
        result = sf.Opportunity.create(data)
        return result.get("id")
    except Exception as e:
        print(f"Error creating opportunity {name}: {e}")
        print(f"Data used: {data}")
        raise

# === Main ===
def reset_salesforce(quiet=True):
    if not quiet:
        print("🚨 Deleting existing Salesforce data...")
    delete_all_cases()
    delete_all_leads()
    delete_all_contacts()
    delete_all_opportunities()
    delete_all_entitlements()
    delete_all_accounts()

    if not quiet:
        print("📤 Loading initial data...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    companies_file = os.path.join(base_dir, "../data/companies.jsonl")
    contacts_file = os.path.join(base_dir, "../data/contacts.jsonl")
    leads_file = os.path.join(base_dir, "../data/leads.jsonl")
    deals_file = os.path.join(base_dir, "../data/deals.jsonl")

    with open(companies_file, "r") as f:
        companies_data = [json.loads(line) for line in f.readlines()]
    with open(contacts_file, "r") as f:
        contacts_data = [json.loads(line) for line in f.readlines()]
    with open(leads_file, "r") as f:
        leads_data = [json.loads(line) for line in f.readlines()]
    with open(deals_file, "r") as f:
        deals_data = [json.loads(line) for line in f.readlines()]

    if not quiet:
        print("🏢 Creating accounts...")
    account_map = {}
    for c in companies_data:
        account_id = create_account(c["name"], c.get("domain", ""))
        account_map[c["company_id"]] = account_id

    if not quiet:
        print("👤 Creating contacts and linking...")
    for contact in contacts_data:
        account_id = account_map.get(contact.get("company_id"))
        create_contact(contact["name"], contact["email"], contact.get("lead_source", ""), account_id, contact.get("title"))

    if not quiet:
        print("🧑‍💼 Creating leads...")
    for lead in leads_data:
        create_lead(lead["name"], lead["email"], lead["lead_status"], lead["company"])

    if not quiet:
        print("💼 Creating opportunities and linking...")
    for deal in deals_data:
        account_id = account_map.get(deal.get("company_id"))
        create_opportunity(deal["name"], deal["amount"], deal["stage"], account_id)

    if not quiet:
        print("✔️ Salesforce reset complete!")

if __name__ == "__main__":
    reset_salesforce()