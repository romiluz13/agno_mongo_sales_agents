# 🤖 AI Sales Agent: Powered by MongoDB

> **This is not just another sales tool. It's a demonstration of how a modern data platform is the essential, beating heart of a sophisticated AI agent system.**

This open-source project showcases a production-ready AI sales automation system built to prove a critical point: for AI agents to be truly intelligent, coordinated, and effective, they require **MongoDB as their central intelligence hub and single source of truth.**

---

## ✨ Why This Project is a Game-Changer for AI

In the age of AI, data is not just stored; it's the lifeblood of intelligence. Traditional, rigid databases fail to handle the dynamic, complex, and unpredictable nature of AI-generated data. This system proves that **MongoDB's flexible document model is the superior choice for building high-performance AI applications.**

Our AI agents can:

-   🧠 **Achieve Perfect Recall:** Access a complete, unified history for every contact—CRM notes, past conversations, and real-time research—all from a single document.
-   🔍 **Conduct Intelligent, Context-Aware Research:** Fuse static CRM data with dynamic intelligence gathered by the `ResearchAgent`, creating a rich, multi-faceted view of every lead.
-   💬 **Generate Truly Personalized Messages:** Craft outreach that is not just personalized, but *hyper-relevant*, referencing specific data points that signal genuine understanding.
-   🚀 **Operate with Unprecedented Agility:** Adapt their behavior in real-time, as their core logic and prompts are stored and managed directly within MongoDB, not hardcoded in the application.

---

## 🏗️ MongoDB: The Core of Our AI Agent Infrastructure

MongoDB is not a passive database in this architecture; it is the active, central nervous system that enables our AI agents to function as a cohesive, intelligent team. It serves four critical functions: as a Unified Data Hub, a State Management Engine, a Resilient Message Broker, and a Dynamic Configuration Center.

### 1. The Single Source of Truth: The `contacts` Collection

Forget scattered data. Every piece of information about a lead—from initial CRM data pulled from Monday.com to the rich, nested JSON produced by the `ResearchAgent`—is consolidated into a **single document** within the `contacts` collection.

**Why this is revolutionary:**

-   **Eliminates Data Silos:** The `MessageAgent` doesn't need to query multiple tables or services. It retrieves one document and instantly has the full context to generate a hyper-personalized message.
-   **Handles AI's Complexity:** The `ResearchAgent` produces complex, semi-structured data with nested objects and arrays. MongoDB's document model stores this rich intelligence natively, without cumbersome normalization or rigid schemas. This is something relational databases struggle with.
-   **Creates a "Digital Twin" of the Lead:** Each document becomes a living profile, constantly enriched by agent activity, creating a comprehensive "single source of truth" that gets smarter over time.

```javascript
// A single document in the `contacts` collection holds ALL context
{
  "monday_item_id": "2010022334",
  "comprehensive_data": { // Data from Monday.com
    "name": "Maor Shlomo",
    "company": "Base44",
    "notes_and_updates": [{"content": "Interested in database solutions"}]
  },
  "research_data": { // Enriched by the ResearchAgent
    "company_intelligence": {
      "recent_news": "Base44 acquisition by TechCorp announced...",
      "challenges": ["database scaling", "AI integration"]
    },
    "conversation_hooks": ["Recent acquisition creates database scaling needs"]
  },
  "generated_message": { // Added by the MessageAgent
    "message_text": "Hi Maor, saw the news about the TechCorp acquisition. This often brings database scaling challenges. How are you planning to handle this?",
    "personalization_score": 0.91
  },
  "outreach_status": "SENT" // Updated by the OutreachAgent
}
```

### 2. State Management & Monitoring: The `workflow_progress` Collection

A multi-agent workflow is complex. The `workflow_progress` collection acts as a real-time flight recorder. As a lead moves from research to messaging to outreach, the `WorkflowCoordinator` agent logs every step, output, and status change.

**Business Impact:**

-   **Complete Observability:** We can track the exact state of any lead at any time, making debugging and monitoring trivial.
-   **Performance Analytics:** By analyzing this collection, we can identify bottlenecks, measure agent performance, and optimize the entire workflow.

### 3. Resilience and Reliability: The `message_queue` Collection

What happens if the WhatsApp service disconnects? The system doesn't fail. The `OutreachErrorRecoverySystem` catches the error and places the unsent message into the `message_queue` collection in MongoDB. A background worker monitors this queue and resends the message once the connection is restored.

**MongoDB's role:** It acts as a simple, durable, and effective message queue, providing enterprise-grade resilience to the system without requiring additional complex infrastructure like RabbitMQ or Kafka.

### 4. Dynamic Control Center: The `agent_configurations` Collection

This is one of the most powerful features of the architecture. The "brains" of our AI agents—their prompts, quality thresholds, and operational parameters—are not hardcoded. They are stored in a single, comprehensive document in the `agent_configurations` collection.

**Unprecedented Agility:**

-   **Tune AI in Real-Time:** Want to make the `MessageAgent` more aggressive? Or change the research strategy of the `ResearchAgent`? Simply update the document in MongoDB. The changes take effect immediately, with **no code deployment required.**
-   **A/B Test Prompts:** Easily test different prompt strategies by modifying the configuration and observing the impact on message quality and response rates via the `workflow_progress` data.

---

## 🔄 How It Works: An Agentic Workflow on MongoDB

```mermaid
graph TD
    A[CRM: User clicks "Process Lead"] --> B[Chrome Extension]
    B --> C{API Backend: /process-lead}
    C --> D[1. Fetch & Store in `contacts`]
    D --> E[2. Research Agent]
    E --> F[Enrich `contacts` document]
    F --> G[3. Message Agent]
    G --> H[Fetch enriched `contacts` doc]
    H --> I[Enrich `contacts` with message]
    I --> J[4. Outreach Agent]
    J --> K[Send Message via WhatsApp]
    K --> L[Update `contacts` with status]

    subgraph MongoDB Atlas - The AI's Brain
        D
        F
        H
        I
        L
    end

    subgraph Agent Team
        E
        G
        J
    end
```

---

## 🚀 Quick Start (5 Minutes)

### **Prerequisites**
- Python 3.11+ and Node.js 16+
- [MongoDB Atlas](https://www.mongodb.com/atlas) (the free M0 tier is perfect)
- API keys: [Monday.com](https://monday.com), [Tavily](https://tavily.com), [Google AI](https://ai.google.dev)

### **1. Clone & Install**
```bash
git clone https://github.com/agno-ai/agno-sales-extension.git
cd agno-sales-extension

# Install backend dependencies
cd backend && pip install -r requirements.txt

# Install WhatsApp bridge dependencies
cd ../whatsapp && npm install
```

### **2. Configure Environment**
```bash
# From the root directory, copy the example environment file
cp .env.example .env

# Edit .env with your credentials
MONGODB_CONNECTION_STRING="your_mongodb_atlas_connection_string"
MONDAY_API_TOKEN="your_monday_api_token"
TAVILY_API_KEY="your_tavily_api_key"
GEMINI_API_KEY="your_google_ai_api_key"
```

### **3. Start the System**
```bash
# Terminal 1: Start the FastAPI Backend
cd backend
python main.py
# ✅ Backend running on http://localhost:8000

# Terminal 2: Start the WhatsApp Bridge
cd ../whatsapp
node working_bridge.js
# ✅ Scan the QR code with your phone's WhatsApp app

# Terminal 3: Load the Chrome Extension
# 1. Open Chrome and navigate to chrome://extensions
# 2. Enable "Developer mode"
# 3. Click "Load unpacked" and select the `extension/` folder
```

### **4. Process Your First Lead**
1.  Navigate to your Monday.com board.
2.  The extension will add a button to your lead items. Click it.
3.  Watch the logs in your backend terminal as the agents collaborate, using MongoDB to pass data and context between each step.
4.  Receive a hyper-personalized WhatsApp message on your test number.

---

## 🛠️ Verified MongoDB Collections

Based on our latest code verification (`ANALYSIS-04-CODE-VERIFICATION.md`), the following collections are actively used to power the AI agent system. Legacy collections have been identified and are slated for removal to ensure clarity.

| Collection Name         | Purpose                                                              | Owning Agent(s)                               |
| ----------------------- | -------------------------------------------------------------------- | --------------------------------------------- |
| **`contacts`**          | **Single Source of Truth.** Stores all lead data, research, messages.  | All Agents                                    |
| **`agent_configurations`**| Dynamic configuration for all agents (prompts, settings).            | `WorkflowCoordinator`                         |
| **`workflow_progress`** | Real-time tracking of the multi-step agent workflow.                 | `WorkflowCoordinator`                         |
| **`research_results`**  | Stores the detailed, structured output of the `ResearchAgent`.       | `ResearchStorageManager`                      |
| **`message_queue`**     | Queues messages for retry upon outreach failure.                     | `OutreachErrorRecoverySystem`                 |
| **`interaction_history`**| Creates a detailed audit trail of every interaction.                 | `StatusTrackingSystem`                        |
| **`agent_sessions`**    | Stores conversation history for agent debugging and traceability.    | `ResearchStorageManager`                      |
| **`message_previews`**  | Used for the optional message approval workflow.                     | `MessageQualityOptimizer`                     |

---

## 🤝 Contributing

This project was built with the [Agno Framework](https://github.com/agno-ai/agno) to demonstrate how to build powerful, production-grade AI systems on MongoDB. Contributions are welcome!

-   🔧 Add new CRM integrations (e.g., HubSpot, Salesforce).
-   💬 Build new messaging channels (e.g., Email, LinkedIn).
-   🧠 Enhance the capabilities of the AI agents.

---

**⭐ Star this repo if you believe MongoDB is the ultimate data platform for AI!**

*This project showcases MongoDB as the intelligent, flexible, and scalable foundation required for the next generation of AI agent systems.*
