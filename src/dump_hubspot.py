from dotenv import load_dotenv
import os
import requests
from .shared import CrmState, CrmStateEngagements

load_dotenv()

# 🔧 CONFIGURATION
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
    "Content-Type": "application/json"
}
BASE_URL = "https://api.hubapi.com"

properties_map = {
    "contacts": ["email", "firstname", "lastname", "phone", "lifecyclestage", "hs_lead_status"],
    "companies": ["name", "domain", "industry", "numberofemployees", "annualrevenue"],
    "deals": [
        "dealname", "amount", "dealstage", "pipeline", "closedate", 
        "createdate", "hs_forecast_amount", "hs_projected_amount_in_home_currency", 
        "hs_deal_stage_probability", "hs_closed_amount_in_home_currency"
    ],
    "emails": ["hs_email_direction", "hs_email_status", "hs_email_subject", "hs_email_from", "hs_email_to"],
    "notes": ["hs_note_body", "hs_createdate", "hs_lastmodifieddate"],
    "calls": ["hs_call_status", "hs_call_duration", "hs_call_start_time", "hs_call_end_time", "hs_call_direction"],
    "meetings": ["hs_meeting_title", "hs_meeting_start_time", "hs_meeting_end_time", "hs_meeting_outcome"],
    "tasks": ["hs_task_status", "hs_body_preview", "hs_task_priority", "hs_task_due_date", "hs_task_assigned_to"],
}

associations_map = {
    "contacts": ["deals", "companies"],
    "companies": ["contacts", "deals"],
    "deals": ["contacts", "companies"],
}

def dump_hubspot():
    """
    Dumps the current state of HubSpot data into list of HubSpotState class
    """

    # Get all contacts
    contacts = get_all_objects("contacts")
    # Get all companies
    companies = get_all_objects("companies")
    # Get all deals
    deals = get_all_objects("deals")
    # Get all engagements
    engagements = CrmStateEngagements(
        emails=get_all_objects("emails"),
        notes=get_all_objects("notes"),
        calls=get_all_objects("calls"),
        meetings=get_all_objects("meetings"),
        tasks=get_all_objects("tasks"),
    )

    hubspot_state = CrmState(
        contacts=contacts,
        companies=companies,
        deals=deals,
        engagements=engagements,
    )

    return hubspot_state

def get(endpoint, params=None):
    """
    Perform a GET request to the HubSpot API and handle errors.
    """
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return {}

def get_all_objects(object_type):
    """
    Get all objects for the given object type
    """
    endpoint = f"/crm/v3/objects/{object_type}"
    objects = []
    after = None
    properties = properties_map.get(object_type, [])
    associations = associations_map.get(object_type, [])
    while True:
        params = {
            "limit": 100,
            "properties": properties,
            "associations": associations
        }

        if after:
            params["after"] = after

        data = get(endpoint, params)
        objects.extend(data.get("results", []))
        if not data.get("paging") or not data["paging"].get("next"):
            break
        after = data["paging"]["next"]["after"]

    return objects

def get_properties(object_type):
    """
    Get properties for the given object type and object ID
    """
    endpoint = f"/crm/v3/objects/{object_type}"
    params = {
        "limit": 500
    }
    data = get(endpoint, params)
    return data

def get_associations(object_type, object_id, to_object_type):
    """
    Get associations for the given object type and object ID
    """
    endpoint = f"/crm/v4/objects/{object_type}/{object_id}/associations/{to_object_type}"
    params = {
        "limit": 500,
    }
    data = get(endpoint, params)
    return data 

if __name__ == "__main__":
    print("Dumping HubSpot state...")
    state = dump_hubspot()
    print(state)