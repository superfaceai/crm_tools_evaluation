import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce
from .shared import CrmState, CrmStateEngagements

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

# Property mappings for Salesforce objects
properties_map = {
    "leads": ["Id", "FirstName", "LastName", "Email", "Phone", "Company", "Status", "LeadSource"],
    "contacts": ["Id", "FirstName", "LastName", "Email", "Phone", "AccountId", "Title", "LeadSource"],
    "accounts": ["Id", "Name", "Industry", "NumberOfEmployees", "AnnualRevenue", "Website"],
    "opportunities": ["Id", "Name", "Amount", "StageName", "CloseDate", "AccountId", "LeadSource", "Probability"],
    "tasks": ["Id", "Subject", "Status", "Priority", "ActivityDate", "OwnerId", "WhatId", "WhoId"],
    "calls": ["Id", "Subject", "Status", "Priority", "ActivityDate", "CallType", "CallDurationInSeconds", "Description", "OwnerId", "WhatId", "WhoId"],
    "notes": ["Id", "Title", "Body", "OwnerId", "ParentId", "CreatedDate", "LastModifiedDate"],
    "meetings": ["Id", "Subject", "StartDateTime", "EndDateTime", "Location", "OwnerId", "WhatId", "WhoId"],
}

def dump_salesforce():
    """
    Dumps the current state of Salesforce data into list of CrmState class
    """
    leads = get_all_objects("leads")
    contacts = get_all_objects("contacts")
    accounts = get_all_objects("accounts")
    opportunities = get_all_objects("opportunities")
    tasks = get_all_objects("tasks")
    calls = get_all_objects("calls")
    notes = get_all_objects("notes")
    meetings = get_all_objects("meetings")

    engagements = CrmStateEngagements(
        emails=[],  # Salesforce does not have a direct Email object in standard REST API
        notes=notes,
        calls=calls,
        meetings=meetings,
        tasks=tasks,
    )

    salesforce_state = CrmState(
        leads=leads,
        contacts=contacts,
        companies=accounts,
        deals=opportunities,
        engagements=engagements,
    )

    return salesforce_state

def get_all_objects(object_type):
    """
    Get all objects for the given Salesforce object type
    """
    if object_type == "leads":
        soql = f"SELECT {', '.join(properties_map['leads'])} FROM Lead"
        records = sf.query_all(soql)["records"]
    elif object_type == "contacts":
        soql = f"SELECT {', '.join(properties_map['contacts'])} FROM Contact"
        records = sf.query_all(soql)["records"]
    elif object_type == "accounts":
        soql = f"SELECT {', '.join(properties_map['accounts'])} FROM Account"
        records = sf.query_all(soql)["records"]
    elif object_type == "opportunities":
        soql = f"SELECT {', '.join(properties_map['opportunities'])} FROM Opportunity"
        records = sf.query_all(soql)["records"]
    elif object_type == "tasks":
        # Print all unique TaskSubtype values
        subtype_query = "SELECT TaskSubtype FROM Task GROUP BY TaskSubtype"
        subtype_records = sf.query_all(subtype_query)["records"]
        unique_subtypes = [rec["TaskSubtype"] for rec in subtype_records]
        soql = f"SELECT {', '.join(properties_map['tasks'])} FROM Task"
        records = sf.query_all(soql)["records"]
    elif object_type == "calls":
        soql = f"SELECT {', '.join(properties_map['calls'])} FROM Task WHERE TaskSubtype = 'Call'"
        records = sf.query_all(soql)["records"]
    elif object_type == "notes":
        # Notes are stored in ContentNote or Note, depending on Salesforce org
        try:
            soql = f"SELECT {', '.join(properties_map['notes'])} FROM Note"
            records = sf.query_all(soql)["records"]
        except Exception:
            records = []
    elif object_type == "meetings":
        # Meetings are Event objects with Subject contains 'Meeting'
        soql = f"SELECT {', '.join(properties_map['meetings'])} FROM Event WHERE Subject LIKE '%Meeting%'"
        records = sf.query_all(soql)["records"]
    else:
        records = []

    print(f"Found {len(records)} {object_type} in Salesforce")
    
    return records

if __name__ == "__main__":
    dump_salesforce()