"""
Monday.com Board Setup and Configuration
Following exact specifications from docs/05-MONDAY-INTEGRATION.md
"""

import os
import requests
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MondayBoardSetup:
    """Setup and configure Monday.com board according to specifications"""
    
    def __init__(self):
        self.api_token = os.getenv("MONDAY_API_TOKEN")
        self.board_id = os.getenv("MONDAY_LEADS_BOARD_ID", "2001047343")
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def execute_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute GraphQL query against Monday.com API"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        response = requests.post(
            self.api_url, 
            json=payload, 
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Monday.com API error: {response.status_code} - {response.text}")
            
        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
            
        return result["data"]
    
    def get_board_info(self) -> Dict:
        """Get current board information and columns"""
        query = """
        query GetBoardInfo($board_id: [ID!]!) {
            boards(ids: $board_id) {
                id
                name
                columns {
                    id
                    title
                    type
                    settings_str
                }
            }
        }
        """
        
        variables = {"board_id": [self.board_id]}
        result = self.execute_query(query, variables)
        
        if not result["boards"]:
            raise Exception(f"Board not found: {self.board_id}")
            
        return result["boards"][0]
    
    def add_sample_leads(self) -> List[str]:
        """Add 10 sample leads for testing"""
        sample_leads = [
            {
                "name": "John Smith - TechCorp",
                "company": "TechCorp Solutions",
                "email": "john.smith@techcorp.com",
                "phone": "+1-555-0101",
                "title": "VP of Engineering"
            },
            {
                "name": "Sarah Johnson - DataFlow",
                "company": "DataFlow Analytics", 
                "email": "sarah.j@dataflow.io",
                "phone": "+1-555-0102",
                "title": "Chief Technology Officer"
            },
            {
                "name": "Michael Chen - CloudScale",
                "company": "CloudScale Systems",
                "email": "m.chen@cloudscale.com",
                "phone": "+1-555-0103", 
                "title": "Head of Product"
            },
            {
                "name": "Emily Rodriguez - AI Ventures",
                "company": "AI Ventures Inc",
                "email": "emily.r@aiventures.com",
                "phone": "+1-555-0104",
                "title": "Director of Innovation"
            },
            {
                "name": "David Kim - SecureNet",
                "company": "SecureNet Technologies",
                "email": "david.kim@securenet.com",
                "phone": "+1-555-0105",
                "title": "Security Architect"
            },
            {
                "name": "Lisa Wang - GrowthLab",
                "company": "GrowthLab Marketing",
                "email": "lisa.wang@growthlab.com", 
                "phone": "+1-555-0106",
                "title": "Marketing Director"
            },
            {
                "name": "Robert Taylor - FinTech Pro",
                "company": "FinTech Pro Solutions",
                "email": "r.taylor@fintechpro.com",
                "phone": "+1-555-0107",
                "title": "Product Manager"
            },
            {
                "name": "Amanda Foster - HealthTech",
                "company": "HealthTech Innovations",
                "email": "amanda.f@healthtech.com",
                "phone": "+1-555-0108", 
                "title": "VP of Operations"
            },
            {
                "name": "James Wilson - EduPlatform",
                "company": "EduPlatform Solutions",
                "email": "james.w@eduplatform.com",
                "phone": "+1-555-0109",
                "title": "Chief Learning Officer"
            },
            {
                "name": "Maria Garcia - GreenEnergy",
                "company": "GreenEnergy Systems",
                "email": "maria.g@greenenergy.com",
                "phone": "+1-555-0110",
                "title": "Sustainability Director"
            }
        ]
        
        created_items = []
        
        for lead in sample_leads:
            try:
                item_id = self.create_lead_item(lead)
                created_items.append(item_id)
                print(f"✅ Created lead: {lead['name']}")
            except Exception as e:
                print(f"❌ Failed to create lead {lead['name']}: {e}")
        
        return created_items
    
    def create_lead_item(self, lead_data: Dict) -> str:
        """Create a single lead item on the board"""
        mutation = """
        mutation CreateLeadItem($board_id: ID!, $item_name: String!, $column_values: JSON!) {
            create_item(
                board_id: $board_id,
                item_name: $item_name,
                column_values: $column_values
            ) {
                id
            }
        }
        """
        
        # Prepare column values based on available columns
        column_values = {}
        
        # Add basic text fields
        if "company" in lead_data:
            column_values["text_company"] = lead_data["company"]
        if "email" in lead_data:
            column_values["email"] = {"email": lead_data["email"], "text": lead_data["email"]}
        if "phone" in lead_data:
            column_values["phone"] = {"phone": lead_data["phone"], "countryShortName": "US"}
        if "title" in lead_data:
            column_values["text_title"] = lead_data["title"]
        
        # Set default status values
        column_values["status_lead"] = {"label": "New Lead"}
        column_values["status_agent"] = {"label": "Pending Research"}
        column_values["status_whatsapp"] = {"label": "Not Sent"}
        column_values["priority"] = {"label": "Medium"}
        
        variables = {
            "board_id": self.board_id,
            "item_name": lead_data["name"],
            "column_values": json.dumps(column_values)
        }
        
        result = self.execute_query(mutation, variables)
        return result["create_item"]["id"]
    
    def setup_board_complete(self) -> Dict:
        """Complete board setup process"""
        print("🔧 Setting up Monday.com board...")
        print(f"Board ID: {self.board_id}")
        
        # Get current board info
        board_info = self.get_board_info()
        print(f"✅ Board found: {board_info['name']}")
        print(f"📊 Current columns: {len(board_info['columns'])}")
        
        # List current columns
        print("\n📋 Current Board Columns:")
        for col in board_info['columns']:
            print(f"  - {col['title']} ({col['type']}) - ID: {col['id']}")
        
        # Add sample leads
        print(f"\n🔄 Adding 10 sample leads...")
        created_items = self.add_sample_leads()
        
        return {
            "success": True,
            "board_id": self.board_id,
            "board_name": board_info['name'],
            "columns_count": len(board_info['columns']),
            "sample_leads_created": len(created_items),
            "created_item_ids": created_items
        }

if __name__ == "__main__":
    try:
        setup = MondayBoardSetup()
        result = setup.setup_board_complete()
        
        print("\n" + "="*50)
        if result["success"]:
            print("🎉 MONDAY.COM BOARD SETUP COMPLETE!")
            print(f"✅ Board: {result['board_name']} (ID: {result['board_id']})")
            print(f"✅ Columns: {result['columns_count']}")
            print(f"✅ Sample leads created: {result['sample_leads_created']}")
            print("✅ Ready for agent processing!")
        else:
            print("❌ Board setup failed!")
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        exit(1)
