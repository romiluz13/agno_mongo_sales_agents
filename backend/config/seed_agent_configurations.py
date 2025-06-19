"""
One-time script to seed the `agent_configurations` collection in MongoDB.

This script centralizes all hardcoded agent configurations into a single
document in the database, enabling dynamic configuration of agents.
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the project root
try:
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logger.info(f"Loaded environment variables from {dotenv_path}")
    else:
        logger.warning(f".env file not found at {dotenv_path}. Relying on system environment variables.")
except Exception as e:
    logger.error(f"Error loading .env file: {e}")


# --- Centralized Agent Configuration Data ---
AGENT_CONFIGURATIONS = {
    "config_version": "1.0",
    "research_agent": {
        "enhanced_research_prompt_template": """
You are an elite sales intelligence researcher with 15+ years of B2B experience, specializing in {product_name} and {product_category}. Your mission is to create hyper-personalized outreach by analyzing EVERY piece of available data.

ENHANCED RESEARCH METHODOLOGY:
1. MONDAY.COM CRM ANALYSIS:
   - Analyze ALL lead notes, interaction history, custom fields
   - Identify previous touchpoints, preferences, pain points
   - Extract relationship context and communication patterns
   - Note any {product_category}-related mentions or needs

2. DEEP COMPANY INTELLIGENCE:
   - Recent news, funding, acquisitions, leadership changes
   - Technology stack analysis (current {product_category} infrastructure)
   - Growth signals, scaling challenges, technical debt indicators
   - Competitor analysis and market positioning

3. {product_name_upper} RELEVANCE ASSESSMENT:
   - Current {product_category} infrastructure challenges
   - Initiatives requiring {product_name} capabilities
   - Scaling issues that {product_name} could solve
   - Operational needs matching {product_name} strengths

4. HYPER-PERSONALIZATION FACTORS:
   - Industry-specific {product_name} use cases
   - Company size and growth stage implications
   - Technical decision-maker background
   - Timing signals for {product_category} modernization

OUTPUT REQUIREMENTS:
- Comprehensive Context Score (0.0-1.0) based on data richness
- CRM Insights (everything relevant from Monday.com)
- Company Intelligence (recent developments + {product_name} relevance)
- Personalization Hooks (specific, actionable conversation starters)
- {product_name} Opportunity Assessment (why they need {product_name} now)

QUALITY STANDARDS:
- Analyze EVERY piece of CRM data for relevance
- Prioritize recent events and specific details
- Focus on {product_name}-relevant pain points and opportunities
- Provide context for why each insight enables hyper-personalization

Remember: You're building the foundation for messages so personalized they feel like they came from someone who knows the prospect personally.

Return your findings in this exact JSON format:
{{
    "confidence_score": 0.85,
    "crm_analysis": {{
        "data_richness": "Assessment of CRM data quality",
        "interaction_history": ["Key interactions and touchpoints"],
        "relationship_context": "Current relationship status and history",
        "product_signals": ["Any {product_category}/{product_name} mentions in CRM"]
    }},
    "company_intelligence": {{
        "recent_news": "Specific recent news or developments",
        "growth_signals": ["List of growth indicators"],
        "challenges": ["List of challenges or pain points"],
        "technology_stack": "Current {product_category}/tech infrastructure insights"
    }},
    "product_opportunity": {{
        "relevance_score": 0.8,
        "use_cases": ["Specific {product_name} use cases for this company"],
        "pain_points": ["{product_category} challenges {product_name} could solve"],
        "timing_signals": ["Why {product_name} adoption makes sense now"]
    }},
    "hyper_personalization": {{
        "strongest_hooks": ["Top 3 most compelling conversation starters"],
        "personal_context": "Individual-specific insights about the lead",
        "company_context": "Company-specific insights for personalization"
    }},
    "timing_rationale": "Why reaching out now makes perfect sense"
}}
""",
        "tavily_search_queries": [
            "{company} recent news 2024 2025",
            "{company} funding growth acquisition",
            "{lead_name} {company} background",
            "{company} technology stack database infrastructure"
        ],
        "tavily_api_config": {
            "topic": "general",
            "search_depth": "advanced",
            "chunks_per_source": 3,
            "max_results": 5,
            "include_answer": True,
            "include_raw_content": False
        },
        "confidence_scoring": {
            "weights": {
                "recent_news": 0.3,
                "growth_signals": 0.2,
                "challenges": 0.2,
                "background": 0.15,
                "recent_activities": 0.15
            }
        },
        "fallback_output": {
            "conversation_hooks": [
                "Interested in connecting with {company}",
                "Would like to discuss {industry} opportunities"
            ],
            "timing_rationale": "General outreach timing"
        }
    },
    "message_generation_agent": {
        "revolutionary_prompt_template": """
🔥 CRITICAL INSTRUCTION: OUTPUT ONLY THE ACTUAL MESSAGE TEXT - NO META-DESCRIPTIONS! 🔥

You are a MongoDB Solutions Architect who generates ACTUAL hyper-personalized messages. You NEVER write about writing messages - you write the actual messages.

❌ FORBIDDEN OUTPUTS (These cause IMMEDIATE FAILURE):
- "Here's a hyper-personalized message for..."
- "Okay, here's a message draft..."
- "I'll create a personalized message..."
- Any meta-commentary about the message

✅ REQUIRED: ONLY the actual message text to send.

🎯 PERFECT MESSAGE EXAMPLES:

TECH COMPANY:
"Hi Sarah! Noticed Acme Corp's recent Series B. Many fast-growing SaaS companies use MongoDB's Vector Search for their AI features. Quick question - what's your current approach for semantic search?"

ENTERPRISE:
"Hi Mike! Saw the TechCrunch article about GlobalTech's AI expansion. We've helped similar enterprises scale their data infrastructure for AI workloads. Are you evaluating database solutions?"

STARTUP:
"Hi Alex! Love what StartupXYZ is building in fintech. MongoDB's document model has helped similar companies iterate 3x faster. What's been your biggest database challenge?"

🎯 GENERATION RULES:
1. Start with "Hi [LEAD_NAME]!"
2. Include ONE specific detail from research/CRM
3. Reference relevant MongoDB capability
4. End with specific question
5. Keep under 120 characters
6. NO meta-commentary

🔥 OUTPUT ONLY THE MESSAGE TEXT - NO JSON, NO EXPLANATIONS:
""",
        "industry_specific_prompts": {
            "technology": "Focus on MongoDB's AI capabilities, Vector Search, developer productivity. Reference scaling challenges and innovation speed.",
            "financial_services": "Emphasize security, compliance, real-time processing. Reference fraud detection and regulatory requirements.",
            "healthcare": "Focus on HIPAA compliance, patient data management, interoperability. Reference clinical data analytics.",
            "retail_ecommerce": "Emphasize personalization, recommendations, inventory management. Reference customer experience optimization."
        },
        "role_specific_prompts": {
            "cto": "Focus on technical architecture and strategic technology decisions. Emphasize scalability and innovation.",
            "vp_engineering": "Focus on team productivity and engineering efficiency. Emphasize developer experience.",
            "data_engineer": "Focus on data pipeline efficiency and real-time processing. Emphasize performance optimization.",
            "product_manager": "Focus on feature velocity and user experience. Emphasize time-to-market."
        },
        "response_optimization": {
            "optimal_length": [50, 120],
            "high_converting_elements": ["personal_name", "company_reference", "question_ending", "value_first", "curiosity_gap"],
            "timing_words": ["noticed", "saw", "quick question", "curious", "wondering"],
            "forbidden_phrases": ["Here's a", "I'll create", "Okay, here's", "Let me craft"]
        },
        "anti_hallucination_rules": {
            "never_mention": ["specific_meetings_not_in_crm", "unverified_news", "specific_people_not_mentioned", "unverified_metrics"],
            "safe_assumptions": ["industry_challenges", "common_mongodb_use_cases", "technology_trends", "role_pain_points"]
        },
        "fallback_message_template": "Hi {lead_name}! I specialize in MongoDB solutions and help {industry} companies optimize their data infrastructure. Quick question - what's your biggest database challenge right now?",
        "emergency_fallback": "Hi {lead_name}! MongoDB Solutions Architect here. Would love to connect about database optimization opportunities at {company}. Quick chat?"
    },
    "outreach_agent": {
        "whatsapp_service_url": "http://localhost:3001",
        "rate_limiting": {
            "messages_per_minute": 10,
            "delay_between_messages": 5
        },
        "retry_configuration": {
            "max_retries": 3,
            "retry_delay_seconds": 30,
            "exponential_backoff": True
        },
        "status_tracking": {
            "check_interval_seconds": 30,
            "delivery_timeout_minutes": 10,
            "read_timeout_minutes": 60
        },
        "monday_integration": {
            "status_field": "lead_status",
            "update_notes": True,
            "create_activities": True
        }
    },
    "workflow_coordinator": {
        "team_coordination": {
            "mode": "coordinate",
            "success_criteria": "Lead successfully processed through complete workflow with high-quality research, personalized message, and successful outreach delivery",
            "enable_agentic_context": True
        },
        "quality_thresholds": {
            "research_confidence_minimum": 0.5,
            "personalization_score_minimum": 0.8,
            "response_rate_minimum": 0.4
        },
        "progress_tracking": {
            "store_in_mongodb": True,
            "collection_name": "workflow_progress",
            "update_frequency": "real_time"
        }
    },
    "multimodal_message_agent": {
        "output_directory": "tmp",
        "voice_generation": {
            "enabled": False,
            "voice_model": "alloy",
            "audio_format": "wav"
        },
        "image_generation": {
            "enabled": True,
            "model": "gemini-2.0-flash-exp-image-generation",
            "response_modalities": ["Text", "Image"]
        }
    },
    "message_quality_optimizer": {
        "target_response_rate": 0.40,
        "quality_threshold": 0.65,
        "optimization_criteria": {
            "personalization_weight": 0.3,
            "readability_weight": 0.2,
            "sentiment_weight": 0.15,
            "urgency_weight": 0.15,
            "value_proposition_weight": 0.1,
            "call_to_action_weight": 0.1
        },
        "approval_workflow": {
            "auto_approve_threshold": 0.85,
            "manual_review_threshold": 0.65,
            "reject_threshold": 0.5
        }
    },
    "error_recovery_system": {
        "retry_configuration": {
            "max_retries": 5,
            "initial_delay_seconds": 30,
            "max_delay_seconds": 300,
            "exponential_backoff_factor": 2.0
        },
        "error_categorization": {
            "network_errors": ["connection", "timeout", "dns"],
            "api_errors": ["rate_limit", "authentication", "quota"],
            "whatsapp_errors": ["not_connected", "invalid_number", "blocked"]
        },
        "escalation_rules": {
            "critical_errors": ["authentication", "quota_exceeded"],
            "notification_threshold": 3,
            "auto_disable_threshold": 10
        }
    },
    "status_tracking_system": {
        "tracking_intervals": {
            "delivery_check_seconds": 30,
            "read_check_seconds": 60,
            "response_check_seconds": 120
        },
        "mongodb_collections": {
            "interaction_history": "interaction_history",
            "delivery_tracking": "delivery_tracking",
            "response_tracking": "response_tracking"
        },
        "metrics_calculation": {
            "response_rate_window_hours": 24,
            "delivery_rate_window_hours": 1,
            "engagement_metrics": ["delivered", "read", "replied"]
        }
    }
}

def seed_database():
    """
    Connects to MongoDB and seeds the agent_configurations collection.
    """
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    database_name = os.getenv("MONGODB_DATABASE", "agno_sales_agent")
    
    if not connection_string:
        logger.error("❌ MONGODB_CONNECTION_STRING environment variable not set.")
        sys.exit(1)
        
    try:
        client = MongoClient(connection_string)
        db = client[database_name]
        
        # Test connection
        client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB database: '{database_name}'")
        
        # Get the collection
        configurations_collection = db["agent_configurations"]
        
        # Use update_one with upsert=True to insert or update the config
        # We use a filter to target a single document for this configuration
        result = configurations_collection.update_one(
            {"config_version": "1.0"},  # Filter to find this specific config document
            {"$set": AGENT_CONFIGURATIONS},
            upsert=True
        )
        
        if result.upserted_id:
            logger.info(f"✅ Successfully inserted the agent configuration document with ID: {result.upserted_id}")
        elif result.modified_count > 0:
            logger.info("✅ Successfully updated the existing agent configuration document.")
        else:
            logger.info("Agent configuration document is already up-to-date.")

    except Exception as e:
        logger.error(f"❌ Failed to seed database: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()
            logger.info("MongoDB connection closed.")

if __name__ == "__main__":
    logger.info("🚀 Starting agent configuration seeding script...")
    seed_database()
    logger.info("🏁 Seeding script finished.")