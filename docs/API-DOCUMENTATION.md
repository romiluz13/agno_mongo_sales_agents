# 📡 API Documentation

**Complete API reference for the Agno Sales Agent Backend**

## 🔗 Base URLs

- **Backend API**: `http://localhost:8000`
- **WhatsApp Bridge**: `http://localhost:3001`

## 🔐 Authentication

All backend API endpoints require authentication headers:

```bash
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

## 📋 Backend API Endpoints

### **Health & Status**

#### `GET /health`
Check backend API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### `GET /api/status`
Get detailed system status.

**Response:**
```json
{
  "backend": "running",
  "mongodb": "connected",
  "whatsapp": "connected",
  "api_keys": {
    "monday": "valid",
    "tavily": "valid",
    "gemini": "valid"
  }
}
```

### **Lead Processing**

#### `POST /api/process-lead`
Process a lead through the complete AI pipeline.

**Request Body:**
```json
{
  "lead_data": {
    "name": "John Smith",
    "company": "TechCorp Inc",
    "title": "CTO",
    "email": "john@techcorp.com",
    "phone": "+1234567890",
    "industry": "Technology",
    "company_size": "100-500"
  },
  "message_type": "text",
  "sender_info": {
    "name": "Rom Iluz",
    "company": "MongoDB Solutions by Rom",
    "value_prop": "MongoDB database optimization"
  }
}
```

**Response:**
```json
{
  "success": true,
  "lead_id": "lead_12345",
  "research_result": {
    "confidence_score": 0.92,
    "recent_news": "TechCorp raised $50M Series B...",
    "conversation_hooks": [
      "Recent Series B funding",
      "Scaling database challenges"
    ],
    "timing_rationale": "Perfect timing with recent funding"
  },
  "message_result": {
    "message_text": "Hi John, saw TechCorp's exciting Series B news...",
    "personalization_score": 0.98,
    "predicted_response_rate": 0.82,
    "message_voice_script": "Voice version of message...",
    "message_image_concept": "Image concept description..."
  },
  "processing_time": 12.3
}
```

#### `GET /api/lead-status/{lead_id}`
Get processing status for a specific lead.

**Response:**
```json
{
  "lead_id": "lead_12345",
  "status": "completed",
  "progress": 100,
  "last_updated": "2024-01-15T10:30:00Z",
  "results": {
    "research_completed": true,
    "message_generated": true,
    "message_sent": false
  }
}
```

### **Message Operations**

#### `POST /api/send-message`
Send a message via WhatsApp.

**Request Body:**
```json
{
  "lead_id": "lead_12345",
  "phone_number": "+1234567890",
  "message_text": "Hi John, saw TechCorp's exciting news...",
  "message_type": "text"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "msg_67890",
  "delivery_status": "sent",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /api/message-status/{message_id}`
Get delivery status for a sent message.

**Response:**
```json
{
  "message_id": "msg_67890",
  "status": "delivered",
  "sent_at": "2024-01-15T10:30:00Z",
  "delivered_at": "2024-01-15T10:30:15Z",
  "read_at": null
}
```

### **Research Operations**

#### `POST /api/research-lead`
Research a lead using AI agents.

**Request Body:**
```json
{
  "lead_name": "John Smith",
  "company": "TechCorp Inc",
  "title": "CTO",
  "industry": "Technology",
  "company_size": "100-500"
}
```

**Response:**
```json
{
  "confidence_score": 0.92,
  "recent_news": "TechCorp raised $50M Series B funding...",
  "conversation_hooks": [
    "Recent Series B funding announcement",
    "Scaling database infrastructure challenges"
  ],
  "timing_rationale": "Perfect timing with recent funding for database optimization",
  "company_intelligence": {
    "growth_signals": ["Series B funding", "Team expansion"],
    "challenges": ["Database scaling", "Performance optimization"],
    "technology_stack": "PostgreSQL, Redis, Kubernetes"
  }
}
```

### **Configuration**

#### `GET /api/config`
Get current system configuration.

**Response:**
```json
{
  "business_config": {
    "product_name": "MongoDB",
    "product_category": "database solutions",
    "expertise_domain": "database optimization",
    "main_value_prop": "Build AI applications 10x faster"
  },
  "agent_config": {
    "research_model": "gemini-2.0-flash-exp",
    "message_model": "gemini-2.0-flash-exp",
    "max_research_time": 30,
    "max_message_length": 500
  }
}
```

#### `POST /api/config`
Update system configuration.

**Request Body:**
```json
{
  "business_config": {
    "product_name": "SalesForce Pro",
    "product_category": "sales automation",
    "expertise_domain": "sales optimization"
  }
}
```

## 📱 WhatsApp Bridge API

### **Connection Management**

#### `POST /connect`
Initialize WhatsApp connection.

**Response:**
```json
{
  "status": "connecting",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "message": "Scan QR code with WhatsApp"
}
```

#### `GET /get-status`
Get WhatsApp connection status.

**Response:**
```json
{
  "status": "connected",
  "phone_number": "+1234567890",
  "connected_at": "2024-01-15T10:00:00Z",
  "last_activity": "2024-01-15T10:29:00Z"
}
```

#### `GET /qr-code`
Get QR code for authentication.

**Response:**
```json
{
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "expires_at": "2024-01-15T10:35:00Z"
}
```

### **Message Sending**

#### `POST /send-message`
Send text message via WhatsApp.

**Request Body:**
```json
{
  "phone": "1234567890",
  "message": "Hi John, saw TechCorp's exciting news..."
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "msg_67890",
  "status": "sent",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `POST /send-voice`
Send voice message via WhatsApp.

**Request Body:**
```json
{
  "phone": "1234567890",
  "voice_script": "Hi John, this is Rom from MongoDB Solutions...",
  "voice_settings": {
    "speed": 1.0,
    "pitch": 1.0
  }
}
```

#### `POST /send-image`
Send image with caption via WhatsApp.

**Request Body:**
```json
{
  "phone": "1234567890",
  "image_url": "https://example.com/image.jpg",
  "caption": "MongoDB architecture diagram for TechCorp"
}
```

## 🔧 Error Handling

### **Error Response Format**

All API errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_API_KEY",
    "message": "The provided API key is invalid or expired",
    "details": {
      "field": "api_key",
      "provided_value": "abc123..."
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### **Common Error Codes**

| Code | Description | Solution |
|------|-------------|----------|
| `INVALID_API_KEY` | API key is invalid or expired | Check and update API key |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry with backoff |
| `LEAD_NOT_FOUND` | Lead ID doesn't exist | Verify lead ID |
| `WHATSAPP_DISCONNECTED` | WhatsApp not connected | Reconnect WhatsApp |
| `MONGODB_ERROR` | Database connection issue | Check MongoDB connection |
| `RESEARCH_FAILED` | Research agent error | Check Tavily API key |
| `MESSAGE_GENERATION_FAILED` | Message agent error | Check Gemini API key |

## 📊 Rate Limits

### **Backend API Limits**
- **General endpoints**: 100 requests/minute
- **Lead processing**: 10 requests/minute
- **Research operations**: 20 requests/minute

### **WhatsApp Bridge Limits**
- **Message sending**: 30 messages/minute
- **Connection operations**: 5 requests/minute

### **Rate Limit Headers**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## 🔍 Monitoring & Analytics

### **Performance Metrics**

#### `GET /api/metrics`
Get system performance metrics.

**Response:**
```json
{
  "performance": {
    "avg_research_time": 7.4,
    "avg_message_time": 4.2,
    "avg_total_time": 12.1,
    "success_rate": 0.98
  },
  "usage": {
    "leads_processed_today": 45,
    "messages_sent_today": 38,
    "api_calls_today": 234
  },
  "quality": {
    "avg_personalization_score": 0.96,
    "avg_confidence_score": 0.89,
    "predicted_response_rate": 0.78
  }
}
```

## 🧪 Testing Endpoints

### **Development & Testing**

#### `POST /api/test-connections`
Test all external API connections.

**Response:**
```json
{
  "monday_api": "connected",
  "tavily_api": "connected",
  "gemini_api": "connected",
  "mongodb": "connected",
  "whatsapp": "connected"
}
```

#### `POST /api/test-lead`
Test lead processing with sample data.

**Response:**
```json
{
  "test_result": "success",
  "processing_time": 8.7,
  "sample_message": "Hi Test User, I noticed your company...",
  "quality_scores": {
    "research_confidence": 0.85,
    "personalization": 0.92
  }
}
```

## 📚 SDK Examples

### **JavaScript/Node.js**
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Authorization': 'Bearer YOUR_API_TOKEN',
    'Content-Type': 'application/json'
  }
});

// Process a lead
const processLead = async (leadData) => {
  try {
    const response = await api.post('/api/process-lead', {
      lead_data: leadData,
      message_type: 'text'
    });
    return response.data;
  } catch (error) {
    console.error('Error processing lead:', error.response.data);
  }
};
```

### **Python**
```python
import requests

class AgnoSalesAPI:
    def __init__(self, base_url="http://localhost:8000", api_token=None):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def process_lead(self, lead_data, message_type="text"):
        response = requests.post(
            f"{self.base_url}/api/process-lead",
            json={
                "lead_data": lead_data,
                "message_type": message_type
            },
            headers=self.headers
        )
        return response.json()
```

### **cURL Examples**
```bash
# Process a lead
curl -X POST http://localhost:8000/api/process-lead \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_data": {
      "name": "John Smith",
      "company": "TechCorp",
      "title": "CTO"
    },
    "message_type": "text"
  }'

# Send WhatsApp message
curl -X POST http://localhost:3001/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "1234567890",
    "message": "Hi John, saw your recent news..."
  }'
```

---

**For more examples and advanced usage, see the [GitHub repository](https://github.com/your-repo/agno-sales-extension) and [documentation](docs/).**
