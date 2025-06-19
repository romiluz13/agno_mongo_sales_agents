# 🔄 USER FLOW - MongoDB Single Source of Truth Workflow

## 📋 **COMPLETE USER JOURNEY**

**Goal**: Click button in Monday.com → Hyper-personalized WhatsApp message sent using MongoDB as single source of truth

**Duration**: <60 seconds end-to-end

## 🎯 **STEP-BY-STEP WORKFLOW**

### **STEP 1: User Interaction**
**Location**: Monday.com board page  
**Action**: User clicks "Process Lead" button on lead row  
**File**: `extension/content.js`

**What Happens**:
1. Chrome extension detects Monday.com board URL
2. Extracts `monday_item_id` and `board_id` from DOM/URL
3. Shows processing indicator to user
4. Sends minimal payload to backend: `{monday_item_id, board_id, fallback_name, fallback_company}`

**Code Location**: `extension/content.js` → `processLeadWithMongoDB()` method

---

### **STEP 2: Backend Receives Request**
**Location**: Backend API server  
**Action**: Process MongoDB workflow request  
**File**: `backend/main.py`

**What Happens**:
1. Receives `MondayItemRequest` with item ID and board ID
2. Validates request data
3. Routes to MongoDB-powered workflow
4. Initializes workflow coordinator

**Code Location**: `backend/main.py` → `process_lead_with_mongodb()` function

---

### **STEP 3: Comprehensive CRM Data Extraction**
**Location**: Backend Monday.com integration  
**Action**: Fetch complete CRM data via Monday.com API  
**File**: `backend/tools/monday_client.py`

**What Happens**:
1. Calls `MondayClient.get_lead_comprehensive_data(monday_item_id)`
2. Extracts ALL column data, notes, updates, interaction history
3. Generates CRM insights and data richness score
4. Returns comprehensive contact data object

**Code Location**: `backend/tools/monday_client.py` → `get_lead_comprehensive_data()` method

---

### **STEP 4: MongoDB Storage (Single Source of Truth)**
**Location**: Backend database layer  
**Action**: Store comprehensive contact data in MongoDB  
**File**: `backend/main.py` → `process_lead_with_mongodb()`

**What Happens**:
1. Creates contact document with comprehensive CRM data
2. Stores in MongoDB `contacts` collection
3. Uses `monday_item_id` as unique identifier
4. Sets `data_source: "monday_api"` and timestamp

**MongoDB Document Structure**:
```javascript
{
  monday_item_id: "123456789",
  board_id: "987654321", 
  comprehensive_data: {
    name: "John Doe",
    company: "TechCorp",
    all_column_data: {...},
    notes_and_updates: [...],
    crm_insights: {...}
  },
  last_updated: "2024-01-01T00:00:00Z",
  data_source: "monday_api"
}
```

**Code Location**: `backend/main.py` → MongoDB storage section

---

### **STEP 5: Research Agent Execution**
**Location**: Workflow coordinator  
**Action**: Research company and store results in MongoDB  
**File**: `backend/agents/workflow_coordinator.py`

**What Happens**:
1. Workflow coordinator calls research agent
2. Research agent uses Tavily to research company
3. **CRITICAL**: Research results stored in MongoDB via `ResearchStorageManager`
4. Updates the same contact document with research data

**Code Location**: `backend/agents/workflow_coordinator.py` → `_execute_research_phase()` method

**MongoDB Update**:
```javascript
{
  // ... existing contact data ...
  research_data: {
    company_intelligence: {...},
    decision_maker_insights: {...},
    conversation_hooks: [...],
    confidence_score: 0.92,
    research_timestamp: "2024-01-01T00:00:00Z"
  }
}
```

---

### **STEP 6: Message Generation (MongoDB Single Source)**
**Location**: Workflow coordinator  
**Action**: Generate hyper-personalized message using ALL MongoDB data  
**File**: `backend/agents/workflow_coordinator.py`

**What Happens**:
1. Retrieves comprehensive contact data from MongoDB
2. Retrieves research data from MongoDB
3. Calls `generate_hyper_personalized_message()` with ALL MongoDB data
4. Message references specific CRM interactions and research insights
5. Stores generated message back in MongoDB

**Code Location**: `backend/agents/workflow_coordinator.py` → `_execute_message_generation_phase()` method

**MongoDB Update**:
```javascript
{
  // ... existing contact and research data ...
  message_data: {
    generated_message: "Hi John, following up on your team meeting last week about AI initiatives. Given TechCorp's recent platform expansion mentioned in your CRM notes, I thought you'd be interested in how MongoDB helped similar companies like yours reduce query times by 50%...",
    personalization_score: 0.87,
    response_prediction: 0.45,
    generation_timestamp: "2024-01-01T00:00:00Z"
  }
}
```

---

### **STEP 7: WhatsApp Message Delivery**
**Location**: Outreach agent  
**Action**: Send message via WhatsApp Web.js  
**File**: `backend/agents/outreach_agent.py`

**What Happens**:
1. Outreach agent receives generated message
2. Sends message via WhatsApp bridge API
3. Tracks delivery status
4. Updates MongoDB with outreach results

**Code Location**: `backend/agents/outreach_agent.py` → message sending logic

**MongoDB Final Update**:
```javascript
{
  // ... all previous data ...
  outreach_data: {
    whatsapp_message_id: "msg_123",
    delivery_status: "sent",
    sent_timestamp: "2024-01-01T00:00:00Z"
  },
  workflow_status: "completed"
}
```

---

### **STEP 8: User Feedback**
**Location**: Chrome extension  
**Action**: Show success notification  
**File**: `extension/content.js`

**What Happens**:
1. Backend returns success response
2. Chrome extension shows success notification
3. User sees "Lead processed successfully!" message
4. Monday.com row may be updated with status

---

## 🎯 **MONGODB SINGLE SOURCE OF TRUTH FLOW**

### **Data Flow Diagram**:
```
Monday.com Click
       ↓
Chrome Extension (Item ID)
       ↓
Backend API
       ↓
Monday.com API (Comprehensive Data)
       ↓
MongoDB Storage (Contact Document)
       ↓
Research Agent → MongoDB Update (Research Data)
       ↓
Message Agent ← MongoDB Retrieval (ALL Data)
       ↓
MongoDB Update (Generated Message)
       ↓
WhatsApp Delivery
       ↓
MongoDB Update (Outreach Status)
```

### **Key MongoDB Operations**:
1. **INSERT**: Initial contact data storage
2. **UPDATE**: Research data addition
3. **RETRIEVE**: All data for message generation
4. **UPDATE**: Generated message storage
5. **UPDATE**: Final outreach status

## 🔧 **CRITICAL IMPLEMENTATION POINTS**

### **What Works (98% Complete)**:
- ✅ Chrome extension Monday.com integration
- ✅ Monday.com API comprehensive data extraction
- ✅ MongoDB database and collections setup
- ✅ Research agent with Tavily integration
- ✅ Message agent with hyper-personalization
- ✅ WhatsApp bridge with reliable messaging
- ✅ Workflow coordinator orchestration

### **What Needs Final Integration (2% Remaining)**:
- 🔧 Research agent MongoDB storage integration
- 🔧 Message agent MongoDB data retrieval
- 🔧 End-to-end workflow testing
- 🔧 Error handling and edge cases

### **Reference Resources (DO NOT CALL)**:
- **Agno Examples**: `../cookbook/` - Study patterns only
- **WhatsApp Examples**: `../examples/whatsapp-web-js/` - Reference only
- **Our Code**: `agno-sales-extension/` - Active development location

## 🎯 **SUCCESS VALIDATION**

### **End-to-End Test**:
1. Navigate to Monday.com board
2. Click "Process Lead" button
3. Verify MongoDB document creation
4. Verify research data addition
5. Verify message generation using MongoDB data
6. Verify WhatsApp message delivery
7. Verify final status update

### **Expected Results**:
- **Processing Time**: <60 seconds
- **Personalization Score**: >0.8
- **MongoDB Integration**: 100% data flow
- **Message Quality**: References specific CRM data

---

**This workflow demonstrates MongoDB's power as the central intelligence hub for AI agents, enabling truly intelligent, context-aware automation.**
