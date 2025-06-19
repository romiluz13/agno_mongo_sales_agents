"""
Monday.com API Client Implementation
Following exact specifications from docs/05-MONDAY-INTEGRATION.md
"""

import os
import sys
import requests
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.monday_board_config import MONDAY_BOARD_CONFIG, AGENT_COLUMN_MAPPING, MONDAY_TO_AGENT_MAPPING

# Load environment variables from parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class MondayClient:
    """Monday.com API client following documentation specifications"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.getenv("MONDAY_API_TOKEN")
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        # IMPROVED: Remove hardcoded default, use consistent env var name
        self.board_id = os.getenv("MONDAY_BOARD_ID") or os.getenv("MONDAY_LEADS_BOARD_ID")
        if not self.board_id:
            raise Exception("Monday.com board ID not configured. Set MONDAY_BOARD_ID environment variable.")
        
        if not self.api_token:
            raise Exception("Monday.com API token not provided")
    
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
    
    def get_all_leads(self, board_id: str = None) -> List[Dict]:
        """Fetch all leads with essential information for UI display"""
        board_id = board_id or self.board_id
        
        query = """
        query GetAllLeads($board_id: [ID!]!) {
            boards(ids: $board_id) {
                items_page {
                    items {
                        id
                        name
                        column_values(ids: ["lead_company", "lead_status", "text", "lead_email", "lead_phone"]) {
                            id
                            text
                            value
                        }
                    }
                }
            }
        }
        """
        
        variables = {"board_id": [board_id]}
        result = self.execute_query(query, variables)
        
        if not result["boards"]:
            return []

        return self.parse_leads_response(result["boards"][0]["items_page"]["items"])
    
    def parse_leads_response(self, items: List[Dict]) -> List[Dict]:
        """Parse Monday.com response into clean lead objects"""
        leads = []
        
        for item in items:
            lead = {
                "monday_id": item["id"],
                "name": item["name"],
                "company": "",
                "status": "",
                "title": "",
                "email": "",
                "phone": ""
            }
            
            for column in item["column_values"]:
                if column["id"] == "lead_company":
                    lead["company"] = column["text"] or ""
                elif column["id"] == "lead_status":
                    lead["status"] = self.parse_status_value(column["value"])
                elif column["id"] == "text":
                    lead["title"] = column["text"] or ""
                elif column["id"] == "lead_email":
                    lead["email"] = self.parse_email_value(column["value"])
                elif column["id"] == "lead_phone":
                    lead["phone"] = self.parse_phone_value(column["value"])
                    
            leads.append(lead)
        
        return leads
    
    def get_timeline_data(self, item_id: str) -> List[Dict]:
        """Fetch timeline items from Emails & Activities app"""
        query = """
        query GetTimeline($item_id: ID!) {
            timeline(id: $item_id) {
                timeline_items_page {
                    cursor
                    timeline_items {
                        id
                        title
                        content
                        created_at
                        type
                        user {
                            name
                            email
                        }
                    }
                }
            }
        }
        """

        variables = {"item_id": item_id}

        try:
            result = self.execute_query(query, variables)

            if result.get("timeline") and result["timeline"].get("timeline_items_page"):
                timeline_items = result["timeline"]["timeline_items_page"].get("timeline_items", [])
                logger.info(f"🔍 Found {len(timeline_items)} timeline items for {item_id}")
                return timeline_items
            else:
                logger.info(f"🔍 No timeline data found for {item_id}")
                return []

        except Exception as e:
            logger.warning(f"⚠️ Could not fetch timeline data for {item_id}: {e}")
            return []

    def get_lead_details(self, item_id: str) -> Dict:
        """Fetch complete lead information for processing"""
        query = """
        query GetLeadDetails($item_id: [ID!]!) {
            items(ids: $item_id) {
                id
                name
                column_values {
                    id
                    text
                    value
                }
                updates {
                    id
                    body
                    text_body
                    created_at
                    creator {
                        name
                        email
                    }
                }
                assets {
                    id
                    name
                    url
                    file_extension
                }
            }
        }
        """

        variables = {"item_id": [item_id]}
        result = self.execute_query(query, variables)

        if not result["items"]:
            raise Exception(f"Lead not found: {item_id}")

        # DEBUG: Log raw response for troubleshooting
        raw_item = result["items"][0]
        logger.info(f"🔍 DEBUG - Raw API response for {item_id}:")
        logger.info(f"   - Name: {raw_item.get('name', 'N/A')}")
        logger.info(f"   - Updates count: {len(raw_item.get('updates', []))}")
        logger.info(f"   - Column values count: {len(raw_item.get('column_values', []))}")

        # Log any long text fields that might contain notes
        for col in raw_item.get('column_values', []):
            if col.get('text') and len(str(col.get('text', ''))) > 50:
                logger.info(f"   - Long text in {col['id']}: {col['text'][:100]}...")

        # Fetch timeline data (E&A app data)
        timeline_items = self.get_timeline_data(item_id)

        return self.parse_lead_details_enhanced(result["items"][0], timeline_items)
    
    def parse_lead_details(self, item: Dict) -> Dict:
        """Parse complete lead information"""
        lead = {
            "monday_id": item["id"],
            "name": item["name"]
        }
        
        for column in item["column_values"]:
            column_id = column["id"]
            
            # Map Monday.com column IDs to our field names
            if column_id in MONDAY_TO_AGENT_MAPPING:
                field_name = MONDAY_TO_AGENT_MAPPING[column_id]
                lead[field_name] = self.parse_column_value(column)
            else:
                # Store unmapped columns with their original ID
                lead[column_id] = self.parse_column_value(column)
        
        return lead

    def parse_lead_details_enhanced(self, item: Dict, timeline_items: List[Dict] = None) -> Dict:
        """Parse complete lead information with ALL available data for hyper-personalization"""
        lead = {
            "monday_id": item["id"],
            "name": item["name"],
            "all_column_data": {},  # Store ALL column data
            "notes_and_updates": [],  # All updates/notes
            "interaction_history": [],  # Timeline of interactions
            "attachments": [],  # Any files/assets
            "crm_insights": {}  # Processed insights for AI
        }

        # Extract ALL column values
        for column in item["column_values"]:
            column_id = column["id"]

            # Map known columns to our field names
            if column_id in MONDAY_TO_AGENT_MAPPING:
                field_name = MONDAY_TO_AGENT_MAPPING[column_id]
                lead[field_name] = self.parse_column_value(column)

            # Store ALL columns in raw format for AI analysis
            lead["all_column_data"][column_id] = {
                "text": column["text"] or "",
                "value": column["value"] or "",
                "parsed": self.parse_column_value(column)
            }

        # Extract notes and updates (conversation history)
        if "updates" in item and item["updates"]:
            for update in item["updates"]:
                # CRITICAL FIX: Use text_body for full content, fallback to body if not available
                full_content = update.get("text_body") or update.get("body", "")

                note_entry = {
                    "id": update["id"],
                    "content": full_content,
                    "created_at": update["created_at"],
                    "creator_name": update["creator"]["name"] if update["creator"] else "Unknown",
                    "creator_email": update["creator"]["email"] if update["creator"] else ""
                }
                lead["notes_and_updates"].append(note_entry)

                # Add to interaction history
                lead["interaction_history"].append({
                    "type": "note",
                    "timestamp": update["created_at"],
                    "content": full_content,
                    "creator": update["creator"]["name"] if update["creator"] else "Unknown"
                })

        # Extract attachments/assets
        if "assets" in item and item["assets"]:
            for asset in item["assets"]:
                attachment = {
                    "id": asset["id"],
                    "name": asset["name"],
                    "url": asset["url"],
                    "file_type": asset["file_extension"]
                }
                lead["attachments"].append(attachment)

        # Extract timeline items (E&A app data like meeting summaries)
        if timeline_items:
            for timeline_item in timeline_items:
                # Add timeline items to notes_and_updates
                timeline_entry = {
                    "id": timeline_item.get("id", ""),
                    "content": timeline_item.get("content", ""),
                    "title": timeline_item.get("title", ""),
                    "created_at": timeline_item.get("created_at", ""),
                    "creator_name": timeline_item.get("user", {}).get("name", "Unknown") if timeline_item.get("user") else "Unknown",
                    "creator_email": timeline_item.get("user", {}).get("email", "") if timeline_item.get("user") else "",
                    "type": "timeline_item"  # Mark as timeline item vs regular update
                }
                lead["notes_and_updates"].append(timeline_entry)

                # Add to interaction history
                lead["interaction_history"].append({
                    "type": "timeline_item",
                    "timestamp": timeline_item.get("created_at", ""),
                    "content": f"{timeline_item.get('title', '')}: {timeline_item.get('content', '')}",
                    "creator": timeline_item.get("user", {}).get("name", "Unknown") if timeline_item.get("user") else "Unknown"
                })

        # Generate CRM insights for AI analysis
        lead["crm_insights"] = self.generate_crm_insights(lead)

        return lead

    def generate_crm_insights(self, lead: Dict) -> Dict:
        """Generate insights from CRM data for AI hyper-personalization"""
        insights = {
            "data_richness_score": 0.0,
            "interaction_frequency": 0,
            "last_interaction_days": None,
            "key_topics": [],
            "relationship_strength": "unknown",
            "mongodb_relevance_signals": []
        }

        # Calculate data richness (how much info we have)
        data_points = 0
        total_possible = 10  # Adjust based on important fields

        if lead.get("company"): data_points += 1
        if lead.get("title"): data_points += 1
        if lead.get("email"): data_points += 1
        if lead.get("phone"): data_points += 1
        if lead.get("notes_and_updates"): data_points += len(lead["notes_and_updates"])
        if lead.get("attachments"): data_points += 1

        insights["data_richness_score"] = min(data_points / total_possible, 1.0)

        # Analyze interaction history
        insights["interaction_frequency"] = len(lead.get("notes_and_updates", []))

        # Look for MongoDB/database-related signals in notes
        mongodb_keywords = ["database", "mongodb", "scaling", "data", "analytics", "ai", "ml", "vector", "search"]
        all_text = " ".join([note["content"].lower() for note in lead.get("notes_and_updates", [])])

        for keyword in mongodb_keywords:
            if keyword in all_text:
                insights["mongodb_relevance_signals"].append(keyword)

        # Extract key topics from notes
        if lead.get("notes_and_updates"):
            # Simple keyword extraction (could be enhanced with NLP)
            common_words = ["meeting", "demo", "interested", "budget", "timeline", "decision", "technical", "requirements"]
            for word in common_words:
                if word in all_text:
                    insights["key_topics"].append(word)

        return insights

    def get_lead_comprehensive_data(self, item_id: str) -> Dict:
        """
        NEW METHOD for Task 11.4: Get ALL available CRM data for hyper-personalization
        This method extracts everything possible from Monday.com for AI analysis
        """
        return self.get_lead_details(item_id)  # Uses enhanced version

    def get_all_leads_with_comprehensive_data(self, board_id: str = None, limit: int = None) -> List[Dict]:
        """
        NEW METHOD for Task 11.4: Get all leads with comprehensive data
        Use with caution - this makes many API calls
        """
        board_id = board_id or self.board_id

        # First get basic lead list
        basic_leads = self.get_all_leads(board_id)

        if limit:
            basic_leads = basic_leads[:limit]

        comprehensive_leads = []

        for lead in basic_leads:
            try:
                # Get comprehensive data for each lead
                comprehensive_data = self.get_lead_comprehensive_data(lead["monday_id"])
                comprehensive_leads.append(comprehensive_data)

                logger.info(f"✅ Enhanced data extracted for: {lead['name']}")

            except Exception as e:
                logger.error(f"❌ Failed to get comprehensive data for {lead['name']}: {e}")
                # Fallback to basic data
                comprehensive_leads.append(lead)

        return comprehensive_leads
    
    def parse_column_value(self, column: Dict) -> str:
        """Parse different column types appropriately"""
        column_id = column["id"]
        
        if column_id == "lead_status":
            return self.parse_status_value(column["value"])
        elif column_id == "date__1":
            return self.parse_date_value(column["value"])
        elif column_id == "lead_email":
            return self.parse_email_value(column["value"])
        elif column_id == "lead_phone":
            return self.parse_phone_value(column["value"])
        else:
            return column["text"] or ""
    
    def parse_status_value(self, value: str) -> str:
        """Parse Monday.com status column value"""
        if not value:
            return ""
        
        try:
            status_data = json.loads(value)
            return status_data.get("text", "")
        except:
            return ""
    
    def parse_date_value(self, value: str) -> str:
        """Parse Monday.com date column value"""
        if not value:
            return ""
        
        try:
            date_data = json.loads(value)
            return date_data.get("date", "")
        except:
            return ""
    
    def parse_email_value(self, value: str) -> str:
        """Parse Monday.com email column value"""
        if not value:
            return ""
        
        try:
            email_data = json.loads(value)
            return email_data.get("email", "")
        except:
            return ""
    
    def parse_phone_value(self, value: str) -> str:
        """Parse Monday.com phone column value"""
        if not value:
            return ""
        
        try:
            phone_data = json.loads(value)
            return phone_data.get("phone", "")
        except:
            return ""
    
    def update_lead_status(self, item_id: str, column_id: str, status_text: str) -> bool:
        """Update lead status column"""
        mutation = """
        mutation UpdateLeadStatus($item_id: ID!, $column_id: String!, $value: JSON!) {
            change_column_value(
                item_id: $item_id, 
                column_id: $column_id, 
                value: $value
            ) {
                id
            }
        }
        """
        
        variables = {
            "item_id": item_id,
            "column_id": column_id,
            "value": json.dumps({"label": status_text})
        }
        
        try:
            self.execute_query(mutation, variables)
            logger.info(f"Updated status for item {item_id}: {column_id} = {status_text}")
            return True
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return False
    
    def update_research_notes(self, item_id: str, notes: str) -> bool:
        """Update research notes column"""
        # Note: This board doesn't have research notes column yet
        # This is a placeholder for future implementation
        logger.warning(f"Research notes update not implemented for current board structure")
        return True

    def add_note_to_item(self, item_id: str, note_text: str) -> bool:
        """
        Add a note/update to a Monday.com item

        Args:
            item_id: Monday.com item ID
            note_text: Note content to add

        Returns:
            Success status
        """
        try:
            logger.info(f"Adding note to item {item_id}: {note_text[:100]}...")

            # GraphQL mutation to add update to item
            query = """
            mutation ($item_id: ID!, $body: String!) {
                create_update(
                    item_id: $item_id,
                    body: $body
                ) {
                    id
                    body
                    created_at
                }
            }
            """

            variables = {
                "item_id": item_id,
                "body": note_text
            }

            response = requests.post(
                self.api_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                logger.error(f"Monday.com API error adding note: {result['errors']}")
                return False

            update_data = result.get("data", {}).get("create_update", {})
            if update_data:
                logger.info(f"✅ Successfully added note to item {item_id} (update ID: {update_data.get('id')})")
                return True
            else:
                logger.error(f"❌ Failed to add note - no update data returned")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to add note to item {item_id}: {e}")
            return False

    def add_message_documentation(self, item_id: str, message_text: str, whatsapp_message_id: str = None, delivery_status: str = "sent") -> bool:
        """
        Add comprehensive message documentation as ACTIVITY in Monday.com Emails & Activities timeline

        Args:
            item_id: Monday.com item ID
            message_text: The message that was sent
            whatsapp_message_id: WhatsApp message ID for tracking
            delivery_status: Message delivery status

        Returns:
            Success status
        """
        try:
            timestamp = datetime.now().isoformat() + "Z"

            # First, get or create a custom activity for WhatsApp messages
            custom_activity_id = self._get_or_create_whatsapp_activity()

            if not custom_activity_id:
                logger.error("❌ Failed to get/create WhatsApp custom activity")
                return False

            # Create timeline item (activity) using Emails & Activities API
            mutation = """
            mutation ($item_id: ID!, $custom_activity_id: String!, $title: String!, $summary: String!, $content: String!, $timestamp: ISO8601DateTime!) {
                create_timeline_item(
                    item_id: $item_id,
                    custom_activity_id: $custom_activity_id,
                    title: $title,
                    summary: $summary,
                    content: $content,
                    timestamp: $timestamp
                ) {
                    id
                    title
                    created_at
                }
            }
            """

            # Prepare activity data
            title = f"WhatsApp Message Sent"
            summary = f"Outbound WhatsApp message - {delivery_status}"
            content = f"""<strong>WhatsApp Message Sent</strong><br><br>
<strong>💬 Message Content:</strong><br>
{message_text.replace(chr(10), '<br>')}<br><br>
<strong>📊 Message Details:</strong><br>
• Platform: WhatsApp<br>
• Status: {delivery_status.title()}<br>
• WhatsApp ID: {whatsapp_message_id or 'N/A'}<br>
• Sent via: Agno Sales Agent<br>
• Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br><br>
🤖 Generated by MongoDB-powered AI sales agent with hyper-personalization"""

            variables = {
                "item_id": item_id,
                "custom_activity_id": custom_activity_id,
                "title": title,
                "summary": summary,
                "content": content,
                "timestamp": timestamp
            }

            response = self.execute_query(mutation, variables)

            if response and response.get('create_timeline_item'):
                activity_id = response['create_timeline_item']['id']
                logger.info(f"✅ Successfully created WhatsApp activity {activity_id} for item {item_id}")
                return True
            else:
                logger.error(f"❌ Failed to create WhatsApp activity for item {item_id}: {response}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to add message documentation: {e}")
            return False

    def _get_or_create_whatsapp_activity(self) -> str:
        """Get or create a custom activity for WhatsApp messages"""
        try:
            # First, check if WhatsApp activity already exists
            query = """
            query {
                custom_activity {
                    id
                    name
                    type
                }
            }
            """

            response = self.execute_query(query)

            if response and response.get('custom_activity'):
                # Look for existing WhatsApp activity
                for activity in response['custom_activity']:
                    if 'WhatsApp' in activity['name']:
                        logger.info(f"✅ Found existing WhatsApp activity: {activity['id']}")
                        return activity['id']

            # Create new WhatsApp custom activity
            mutation = """
            mutation {
                create_custom_activity(
                    name: "WhatsApp Message",
                    color: MAYA_BLUE,
                    icon_id: PAPERPLANE
                ) {
                    id
                    name
                }
            }
            """

            response = self.execute_query(mutation)

            if response and response.get('create_custom_activity'):
                activity_id = response['create_custom_activity']['id']
                logger.info(f"✅ Created new WhatsApp custom activity: {activity_id}")
                return activity_id
            else:
                logger.error(f"❌ Failed to create WhatsApp custom activity: {response}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting/creating WhatsApp activity: {str(e)}")
            return None

    def search_leads_by_name(self, board_id: str = None, search_term: str = "") -> List[Dict]:
        """Search for leads by name (client-side filtering for speed)"""
        all_leads = self.get_all_leads(board_id)
        
        if not search_term:
            return all_leads
        
        search_term_lower = search_term.lower()
        matching_leads = [
            lead for lead in all_leads 
            if search_term_lower in lead["name"].lower() or 
               search_term_lower in lead["company"].lower()
        ]
        
        return matching_leads

if __name__ == "__main__":
    # Test the Monday.com client
    logging.basicConfig(level=logging.INFO)
    
    try:
        client = MondayClient()
        
        print("🔧 Testing Monday.com API Client...")
        
        # Test get_all_leads
        print("\n📋 Fetching all leads...")
        leads = client.get_all_leads()
        print(f"✅ Found {len(leads)} leads")
        
        if leads:
            # Test enhanced lead details (Task 11.4)
            first_lead = leads[0]
            print(f"\n🔍 Getting COMPREHENSIVE details for: {first_lead['name']}")
            comprehensive_details = client.get_lead_comprehensive_data(first_lead['monday_id'])

            print(f"✅ Enhanced lead data extracted:")
            print(f"   - Data richness score: {comprehensive_details['crm_insights']['data_richness_score']:.2f}")
            print(f"   - Notes/updates: {len(comprehensive_details['notes_and_updates'])}")
            print(f"   - All columns: {len(comprehensive_details['all_column_data'])}")
            print(f"   - MongoDB signals: {comprehensive_details['crm_insights']['mongodb_relevance_signals']}")

            # Test search
            print(f"\n🔎 Searching for leads containing 'Tech'...")
            search_results = client.search_leads_by_name(search_term="Tech")
            print(f"✅ Found {len(search_results)} matching leads")

            # Test comprehensive data for first 2 leads (limited for testing)
            print(f"\n📊 Testing comprehensive data extraction (first 2 leads)...")
            comprehensive_leads = client.get_all_leads_with_comprehensive_data(limit=2)
            print(f"✅ Extracted comprehensive data for {len(comprehensive_leads)} leads")
        
        print("\n🎉 Monday.com API Client test complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)
