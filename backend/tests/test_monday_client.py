"""
Comprehensive tests for Monday.com API client
Tests all CRUD operations, error handling, and data parsing
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.monday_client import MondayClient

class TestMondayClient:
    """Test suite for Monday.com API client"""
    
    def setup_method(self):
        """Setup test environment"""
        self.api_token = "test_token"
        self.client = MondayClient(api_token=self.api_token)
        self.test_board_id = "2001047343"
        self.test_item_id = "2001047776"
    
    def test_client_initialization(self):
        """Test client initialization"""
        assert self.client.api_token == self.api_token
        assert self.client.api_url == "https://api.monday.com/v2"
        assert "Authorization" in self.client.headers
        assert self.client.headers["Authorization"] == f"Bearer {self.api_token}"
    
    def test_client_initialization_no_token(self):
        """Test client initialization without token raises exception"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="Monday.com API token not provided"):
                MondayClient()
    
    @patch('tools.monday_client.requests.post')
    def test_execute_query_success(self, mock_post):
        """Test successful query execution"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"test": "success"}}
        mock_post.return_value = mock_response
        
        result = self.client.execute_query("query { test }")
        
        assert result == {"test": "success"}
        mock_post.assert_called_once()
    
    @patch('tools.monday_client.requests.post')
    def test_execute_query_http_error(self, mock_post):
        """Test HTTP error handling"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="Monday.com API error: 400"):
            self.client.execute_query("query { test }")
    
    @patch('tools.monday_client.requests.post')
    def test_execute_query_graphql_error(self, mock_post):
        """Test GraphQL error handling"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"message": "Field not found"}]
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="GraphQL errors"):
            self.client.execute_query("query { test }")
    
    @patch.object(MondayClient, 'execute_query')
    def test_get_all_leads_success(self, mock_execute):
        """Test successful lead fetching"""
        mock_execute.return_value = {
            "boards": [{
                "items_page": {
                    "items": [
                        {
                            "id": "123",
                            "name": "Test Lead",
                            "column_values": [
                                {"id": "lead_company", "text": "Test Company", "value": "Test Company"},
                                {"id": "lead_status", "text": "New", "value": '{"text": "New Lead"}'},
                                {"id": "text", "text": "CEO", "value": "CEO"},
                                {"id": "lead_email", "text": "test@test.com", "value": '{"email": "test@test.com"}'},
                                {"id": "lead_phone", "text": "+1234567890", "value": '{"phone": "+1234567890"}'}
                            ]
                        }
                    ]
                }
            }]
        }
        
        leads = self.client.get_all_leads()
        
        assert len(leads) == 1
        assert leads[0]["monday_id"] == "123"
        assert leads[0]["name"] == "Test Lead"
        assert leads[0]["company"] == "Test Company"
        assert leads[0]["status"] == "New Lead"
        assert leads[0]["title"] == "CEO"
        assert leads[0]["email"] == "test@test.com"
        assert leads[0]["phone"] == "+1234567890"
    
    @patch.object(MondayClient, 'execute_query')
    def test_get_all_leads_empty_board(self, mock_execute):
        """Test handling of empty board"""
        mock_execute.return_value = {"boards": []}
        
        leads = self.client.get_all_leads()
        
        assert leads == []
    
    @patch.object(MondayClient, 'execute_query')
    def test_get_lead_details_success(self, mock_execute):
        """Test successful lead detail fetching"""
        mock_execute.return_value = {
            "items": [{
                "id": "123",
                "name": "Test Lead",
                "column_values": [
                    {"id": "lead_company", "text": "Test Company", "value": "Test Company"},
                    {"id": "lead_email", "text": "test@test.com", "value": '{"email": "test@test.com"}'},
                    {"id": "lead_phone", "text": "+1234567890", "value": '{"phone": "+1234567890"}'}
                ]
            }]
        }
        
        details = self.client.get_lead_details("123")
        
        assert details["monday_id"] == "123"
        assert details["name"] == "Test Lead"
        assert details["company"] == "Test Company"
        assert details["email"] == "test@test.com"
        assert details["phone"] == "+1234567890"
    
    @patch.object(MondayClient, 'execute_query')
    def test_get_lead_details_not_found(self, mock_execute):
        """Test handling of lead not found"""
        mock_execute.return_value = {"items": []}
        
        with pytest.raises(Exception, match="Lead not found: 123"):
            self.client.get_lead_details("123")
    
    def test_parse_status_value(self):
        """Test status value parsing"""
        # Valid JSON status
        status_json = '{"text": "New Lead", "color": "#037f4c"}'
        result = self.client.parse_status_value(status_json)
        assert result == "New Lead"
        
        # Empty value
        result = self.client.parse_status_value("")
        assert result == ""
        
        # Invalid JSON
        result = self.client.parse_status_value("invalid json")
        assert result == ""
    
    def test_parse_email_value(self):
        """Test email value parsing"""
        # Valid JSON email
        email_json = '{"email": "test@example.com", "text": "test@example.com"}'
        result = self.client.parse_email_value(email_json)
        assert result == "test@example.com"
        
        # Empty value
        result = self.client.parse_email_value("")
        assert result == ""
        
        # Invalid JSON
        result = self.client.parse_email_value("invalid json")
        assert result == ""
    
    def test_parse_phone_value(self):
        """Test phone value parsing"""
        # Valid JSON phone
        phone_json = '{"phone": "+1234567890", "countryShortName": "US"}'
        result = self.client.parse_phone_value(phone_json)
        assert result == "+1234567890"
        
        # Empty value
        result = self.client.parse_phone_value("")
        assert result == ""
        
        # Invalid JSON
        result = self.client.parse_phone_value("invalid json")
        assert result == ""
    
    @patch.object(MondayClient, 'execute_query')
    def test_update_lead_status_success(self, mock_execute):
        """Test successful status update"""
        mock_execute.return_value = {"change_column_value": {"id": "123"}}
        
        result = self.client.update_lead_status("123", "lead_status", "Contacted")
        
        assert result is True
        mock_execute.assert_called_once()
    
    @patch.object(MondayClient, 'execute_query')
    def test_update_lead_status_failure(self, mock_execute):
        """Test status update failure"""
        mock_execute.side_effect = Exception("API Error")
        
        result = self.client.update_lead_status("123", "lead_status", "Contacted")
        
        assert result is False
    
    @patch.object(MondayClient, 'get_all_leads')
    def test_search_leads_by_name(self, mock_get_all):
        """Test lead search functionality"""
        mock_get_all.return_value = [
            {"name": "John Smith - TechCorp", "company": "TechCorp Solutions"},
            {"name": "Jane Doe - HealthCare", "company": "HealthCare Inc"},
            {"name": "Bob Wilson - TechStart", "company": "TechStart LLC"}
        ]
        
        # Search by name
        results = self.client.search_leads_by_name(search_term="Tech")
        assert len(results) == 2
        
        # Search by company
        results = self.client.search_leads_by_name(search_term="HealthCare")
        assert len(results) == 1
        
        # Case insensitive search
        results = self.client.search_leads_by_name(search_term="tech")
        assert len(results) == 2
        
        # Empty search term returns all
        results = self.client.search_leads_by_name(search_term="")
        assert len(results) == 3

def run_integration_tests():
    """Run integration tests with real API (if token available)"""
    try:
        # Only run if we have a real API token
        api_token = os.getenv("MONDAY_API_TOKEN")
        if not api_token or api_token == "your_monday_api_token_here":
            print("⚠️  Skipping integration tests - no API token configured")
            return True
        
        print("🔧 Running Monday.com integration tests...")
        
        client = MondayClient()
        
        # Test 1: Get all leads
        print("📋 Testing get_all_leads...")
        leads = client.get_all_leads()
        print(f"✅ Found {len(leads)} leads")
        
        if leads:
            # Test 2: Get lead details
            first_lead = leads[0]
            print(f"🔍 Testing get_lead_details for: {first_lead['name']}")
            details = client.get_lead_details(first_lead['monday_id'])
            print(f"✅ Retrieved details for lead: {details['name']}")
            
            # Test 3: Search functionality
            print("🔎 Testing search functionality...")
            search_results = client.search_leads_by_name(search_term="Tech")
            print(f"✅ Search found {len(search_results)} results")
        
        print("🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    # Run integration tests
    success = run_integration_tests()
    exit(0 if success else 1)
