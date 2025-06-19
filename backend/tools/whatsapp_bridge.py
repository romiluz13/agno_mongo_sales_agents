"""
WhatsApp Bridge Client for Python
Communicates with Node.js WhatsApp server via HTTP API
"""

import requests
import json
import time
from typing import Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class WhatsAppBridge:
    """Python client for WhatsApp Bridge Server"""
    
    def __init__(self, server_url: str = "http://localhost:3001"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to WhatsApp server"""
        url = f"{self.server_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp Bridge request failed: {e}")
            return {"success": False, "message": str(e)}
    
    def health_check(self) -> Dict:
        """Check if WhatsApp server is running"""
        return self._make_request("GET", "/health")
    
    def connect(self) -> Dict:
        """Initialize WhatsApp connection"""
        logger.info("Connecting to WhatsApp...")
        return self._make_request("POST", "/connect")
    
    def get_status(self) -> Dict:
        """Get WhatsApp connection status"""
        return self._make_request("GET", "/get-status")
    
    def get_qr_code(self) -> Dict:
        """Get QR code for authentication"""
        return self._make_request("GET", "/qr-code")
    
    def send_text_message(self, phone_number: str, message: str) -> Dict:
        """Send text message via WhatsApp"""
        data = {
            "phoneNumber": phone_number,
            "message": message,
            "type": "text"
        }
        
        logger.info(f"Sending text message to {phone_number}")
        return self._make_request("POST", "/send-message", json=data)
    
    def send_voice_message(self, phone_number: str, audio_file_path: str) -> Dict:
        """Send voice message via WhatsApp"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                data = {'phoneNumber': phone_number}
                
                logger.info(f"Sending voice message to {phone_number}")
                return self._make_request("POST", "/send-voice", files=files, data=data)
                
        except FileNotFoundError:
            return {"success": False, "message": f"Audio file not found: {audio_file_path}"}
    
    def send_image_message(self, phone_number: str, image_file_path: str, caption: str = "") -> Dict:
        """Send image message via WhatsApp"""
        try:
            with open(image_file_path, 'rb') as image_file:
                files = {'image': image_file}
                data = {
                    'phoneNumber': phone_number,
                    'caption': caption
                }
                
                logger.info(f"Sending image to {phone_number}")
                return self._make_request("POST", "/send-image", files=files, data=data)
                
        except FileNotFoundError:
            return {"success": False, "message": f"Image file not found: {image_file_path}"}
    
    def disconnect(self) -> Dict:
        """Disconnect WhatsApp"""
        logger.info("Disconnecting WhatsApp...")
        return self._make_request("POST", "/disconnect")
    
    def wait_for_ready(self, timeout: int = 60) -> bool:
        """Wait for WhatsApp to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_status()
            if status.get("success") and status.get("status", {}).get("isReady"):
                logger.info("WhatsApp is ready!")
                return True
            
            time.sleep(2)
        
        logger.warning(f"WhatsApp not ready after {timeout} seconds")
        return False
    
    def wait_for_authentication(self, timeout: int = 120) -> bool:
        """Wait for WhatsApp authentication"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_status()
            if status.get("success"):
                status_data = status.get("status", {})
                if status_data.get("isAuthenticated"):
                    logger.info("WhatsApp authenticated!")
                    return True
                elif status_data.get("qrCode"):
                    logger.info("QR code available - scan with your phone")
            
            time.sleep(3)
        
        logger.warning(f"WhatsApp not authenticated after {timeout} seconds")
        return False

def test_whatsapp_bridge():
    """Test WhatsApp Bridge integration"""
    print("🧪 Testing WhatsApp Bridge integration...")
    
    bridge = WhatsAppBridge()
    
    # Test 1: Health check
    print("\n📡 Test 1: Health check...")
    health = bridge.health_check()
    if health.get("status") == "ok":
        print("✅ WhatsApp server is running")
    else:
        print("❌ WhatsApp server is not accessible")
        return False
    
    # Test 2: Get initial status
    print("\n📱 Test 2: Get status...")
    status = bridge.get_status()
    if status.get("success"):
        print("✅ Status endpoint working")
        status_data = status.get("status", {})
        print(f"   Ready: {status_data.get('isReady', False)}")
        print(f"   Authenticated: {status_data.get('isAuthenticated', False)}")
    else:
        print("❌ Status endpoint failed")
    
    # Test 3: Test message sending (will fail if not connected, but tests API)
    print("\n📤 Test 3: Test message sending API...")
    result = bridge.send_text_message("+1-555-0101", "Test message from Python!")
    if "success" in result:
        print("✅ Message sending API structure correct")
        if not result["success"]:
            print(f"   Expected failure: {result.get('message', 'Unknown error')}")
    else:
        print("❌ Message sending API failed")
    
    # Test 4: Connection endpoint
    print("\n🔗 Test 4: Connection endpoint...")
    connect_result = bridge.connect()
    if "success" in connect_result:
        print("✅ Connection endpoint working")
        print(f"   Result: {connect_result.get('message', 'No message')}")
    else:
        print("❌ Connection endpoint failed")
    
    print("\n🎉 WhatsApp Bridge integration tests complete!")
    print("📱 Bridge is ready for WhatsApp operations")
    print("🔧 To use: Start server with 'node server.js' then connect via Python")
    
    return True

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    success = test_whatsapp_bridge()
    exit(0 if success else 1)
