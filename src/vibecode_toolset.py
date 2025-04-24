"""
PROMPT TO GENERATE THIS FILE:

Create a Python module that defines a toolset for interacting with the HubSpot API. The module should include the following:

## Environment Setup

- **Base URL**: `https://api.hubapi.com`
- **Access Token**: Retrieved from the `HUBSPOT_API_KEY` environment variable. If not set, an `EnvironmentError` is raised.

## Toolset Definition

- The `create_vibecode_toolset` function defines a `Toolset` containing tools for various HubSpot operations. Each tool is intance of `Tool` class
- Tool handler can't raise an exception, it must return a JSON object with `error` key if an error occurs
- Tool handler gets args as string

### Tools
- **Contacts**: Create, search, and manage contact objects.
- **Companies**: Create, search, and manage company objects.
- **Deals**: Create, search, and manage deal objects.
- **Engagements**: Create, search, and manage engagements.
- **Properties**: Read property groups for object types.
- **Associations**: List and manage association types.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from .shared import Tool, Toolset

HUBSPOT_BASE_URL = "https://api.hubapi.com"

def get_hubspot_token() -> str:
    """Get HubSpot API token from environment variable."""
    token = os.getenv("HUBSPOT_API_KEY")
    if not token:
        raise EnvironmentError("HUBSPOT_API_KEY environment variable is not set")
    return token

def make_hubspot_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a request to HubSpot API with error handling."""
    try:
        headers = {
            "Authorization": f"Bearer {get_hubspot_token()}",
            "Content-Type": "application/json"
        }
        url = f"{HUBSPOT_BASE_URL}{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def create_vibecode_toolset() -> Toolset:
    """Create a toolset for HubSpot API operations."""
    
    def handle_contacts(args: str) -> Dict[str, Any]:
        """Handle contact operations."""
        try:
            args_dict = json.loads(args)
            operation = args_dict.get("operation", "search")
            
            if operation == "create":
                return make_hubspot_request("POST", "/crm/v3/objects/contacts", args_dict.get("data"))
            elif operation == "search":
                return make_hubspot_request("GET", "/crm/v3/objects/contacts/search", args_dict.get("data"))
            elif operation == "update":
                contact_id = args_dict.get("contact_id")
                return make_hubspot_request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", args_dict.get("data"))
            else:
                return {"error": f"Unknown operation: {operation}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON arguments"}

    def handle_companies(args: str) -> Dict[str, Any]:
        """Handle company operations."""
        try:
            args_dict = json.loads(args)
            operation = args_dict.get("operation", "search")
            
            if operation == "create":
                return make_hubspot_request("POST", "/crm/v3/objects/companies", args_dict.get("data"))
            elif operation == "search":
                return make_hubspot_request("GET", "/crm/v3/objects/companies/search", args_dict.get("data"))
            elif operation == "update":
                company_id = args_dict.get("company_id")
                return make_hubspot_request("PATCH", f"/crm/v3/objects/companies/{company_id}", args_dict.get("data"))
            else:
                return {"error": f"Unknown operation: {operation}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON arguments"}

    def handle_deals(args: str) -> Dict[str, Any]:
        """Handle deal operations."""
        try:
            args_dict = json.loads(args)
            operation = args_dict.get("operation", "search")
            
            if operation == "create":
                return make_hubspot_request("POST", "/crm/v3/objects/deals", args_dict.get("data"))
            elif operation == "search":
                return make_hubspot_request("GET", "/crm/v3/objects/deals/search", args_dict.get("data"))
            elif operation == "update":
                deal_id = args_dict.get("deal_id")
                return make_hubspot_request("PATCH", f"/crm/v3/objects/deals/{deal_id}", args_dict.get("data"))
            else:
                return {"error": f"Unknown operation: {operation}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON arguments"}

    def handle_engagements(args: str) -> Dict[str, Any]:
        """Handle engagement operations."""
        try:
            args_dict = json.loads(args)
            operation = args_dict.get("operation", "search")
            
            if operation == "create":
                return make_hubspot_request("POST", "/crm/v3/objects/engagements", args_dict.get("data"))
            elif operation == "search":
                return make_hubspot_request("GET", "/crm/v3/objects/engagements/search", args_dict.get("data"))
            elif operation == "update":
                engagement_id = args_dict.get("engagement_id")
                return make_hubspot_request("PATCH", f"/crm/v3/objects/engagements/{engagement_id}", args_dict.get("data"))
            else:
                return {"error": f"Unknown operation: {operation}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON arguments"}

    def handle_properties(args: str) -> Dict[str, Any]:
        """Handle property operations."""
        try:
            args_dict = json.loads(args)
            object_type = args_dict.get("object_type", "contacts")
            return make_hubspot_request("GET", f"/crm/v3/properties/{object_type}")
        except json.JSONDecodeError:
            return {"error": "Invalid JSON arguments"}

    def handle_associations(args: str) -> Dict[str, Any]:
        """Handle association operations."""
        try:
            args_dict = json.loads(args)
            operation = args_dict.get("operation", "list")
            
            if operation == "list":
                from_object_type = args_dict.get("from_object_type")
                to_object_type = args_dict.get("to_object_type")
                return make_hubspot_request("GET", f"/crm/v3/associations/{from_object_type}/{to_object_type}")
            elif operation == "create":
                from_object_type = args_dict.get("from_object_type")
                from_object_id = args_dict.get("from_object_id")
                to_object_type = args_dict.get("to_object_type")
                to_object_id = args_dict.get("to_object_id")
                return make_hubspot_request("PUT", f"/crm/v3/associations/{from_object_type}/{from_object_id}/to/{to_object_type}/{to_object_id}")
            else:
                return {"error": f"Unknown operation: {operation}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON arguments"}

    tools = [
        Tool(
            name="contacts",
            description="Create, search, and manage contact objects in HubSpot",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["create", "search", "update"],
                        "description": "The operation to perform"
                    },
                    "data": {
                        "type": "object",
                        "description": "The data for the operation"
                    },
                    "contact_id": {
                        "type": "string",
                        "description": "The contact ID for update operations"
                    }
                },
                "required": ["operation"]
            },
            handler=handle_contacts
        ),
        Tool(
            name="companies",
            description="Create, search, and manage company objects in HubSpot",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["create", "search", "update"],
                        "description": "The operation to perform"
                    },
                    "data": {
                        "type": "object",
                        "description": "The data for the operation"
                    },
                    "company_id": {
                        "type": "string",
                        "description": "The company ID for update operations"
                    }
                },
                "required": ["operation"]
            },
            handler=handle_companies
        ),
        Tool(
            name="deals",
            description="Create, search, and manage deal objects in HubSpot",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["create", "search", "update"],
                        "description": "The operation to perform"
                    },
                    "data": {
                        "type": "object",
                        "description": "The data for the operation"
                    },
                    "deal_id": {
                        "type": "string",
                        "description": "The deal ID for update operations"
                    }
                },
                "required": ["operation"]
            },
            handler=handle_deals
        ),
        Tool(
            name="engagements",
            description="Create, search, and manage engagements in HubSpot",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["create", "search", "update"],
                        "description": "The operation to perform"
                    },
                    "data": {
                        "type": "object",
                        "description": "The data for the operation"
                    },
                    "engagement_id": {
                        "type": "string",
                        "description": "The engagement ID for update operations"
                    }
                },
                "required": ["operation"]
            },
            handler=handle_engagements
        ),
        Tool(
            name="properties",
            description="Read property groups for object types in HubSpot",
            parameters={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "enum": ["contacts", "companies", "deals", "engagements"],
                        "description": "The type of object to get properties for"
                    }
                },
                "required": ["object_type"]
            },
            handler=handle_properties
        ),
        Tool(
            name="associations",
            description="List and manage association types in HubSpot",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["list", "create"],
                        "description": "The operation to perform"
                    },
                    "from_object_type": {
                        "type": "string",
                        "enum": ["contacts", "companies", "deals", "engagements"],
                        "description": "The source object type"
                    },
                    "to_object_type": {
                        "type": "string",
                        "enum": ["contacts", "companies", "deals", "engagements"],
                        "description": "The target object type"
                    },
                    "from_object_id": {
                        "type": "string",
                        "description": "The source object ID for create operations"
                    },
                    "to_object_id": {
                        "type": "string",
                        "description": "The target object ID for create operations"
                    }
                },
                "required": ["operation", "from_object_type", "to_object_type"]
            },
            handler=handle_associations
        )
    ]

    return Toolset(name="Vibecode Toolset", tools=tools)
