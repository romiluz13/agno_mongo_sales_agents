# MongoDB Schema Verification Report

---

## 1. All Collections in Database

Found 13 collections in the 'agno_sales_agent' database:

- `agent_configurations`
- `agent_logs`
- `agent_sessions`
- `connection_test`
- `contacts`
- `interaction_history`
- `interactions`
- `leads`
- `message_previews`
- `message_queue`
- `research_cache`
- `research_results`
- `workflow_progress`

---

## 2. Sample Document from Key Collections

Fetching one sample document from each key collection to verify schema.

### Collection: `agent_configurations`

```json
{
  "_id": {
    "$oid": "6853b26b602717e741ad5a8c"
  },
  "config_version": "1.0",
  "error_recovery_system": {
    "retry_configuration": {
      "max_retries": 5,
      "initial_delay_seconds": 30,
      "max_delay_seconds": 300,
      "exponential_backoff_factor": 2.0
    },
    "error_categorization": {
      "network_errors": [
        "connection",
        "timeout",
        "dns"
      ],
      "api_errors": [
        "rate_limit",
        "authentication",
        "quota"
      ],
      "whatsapp_errors": [
        "not_connected",
        "invalid_number",
        "blocked"
      ]
    },
    "escalation_rules": {
      "critical_errors": [
        "authentication",
        "quota_exceeded"
      ],
      "notification_threshold": 3,
      "auto_disable_threshold": 10
    }
  },
  "message_generation_agent": {
    "revolutionary_prompt_template": "\n\ud83d\udd25 CRITICAL INSTRUCTION: OUTPUT ONLY THE ACTUAL MESSAGE TEXT - NO META-DESCRIPTIONS! \ud83d\udd25\n\nYou are a MongoDB Solutions Architect who generates ACTUAL hyper-personalized messages. You NEVER write about writing messages - you write the actual messages.\n\n\u274c FORBIDDEN OUTPUTS (These cause IMMEDIATE FAILURE):\n- \"Here's a hyper-personalized message for...\"\n- \"Okay, here's a message draft...\"\n- \"I'll create a personalized message...\"\n- Any meta-commentary about the message\n\n\u2705 REQUIRED: ONLY the actual message text to send.\n\n\ud83c\udfaf PERFECT MESSAGE EXAMPLES:\n\nTECH COMPANY:\n\"Hi Sarah! Noticed Acme Corp's recent Series B. Many fast-growing SaaS companies use MongoDB's Vector Search for their AI features. Quick question - what's your current approach for semantic search?\"\n\nENTERPRISE:\n\"Hi Mike! Saw the TechCrunch article about GlobalTech's AI expansion. We've helped similar enterprises scale their data infrastructure for AI workloads. Are you evaluating database solutions?\"\n\nSTARTUP:\n\"Hi Alex! Love what StartupXYZ is building in fintech. MongoDB's document model has helped similar companies iterate 3x faster. What's been your biggest database challenge?\"\n\n\ud83c\udfaf GENERATION RULES:\n1. Start with \"Hi [LEAD_NAME]!\"\n2. Include ONE specific detail from research/CRM\n3. Reference relevant MongoDB capability\n4. End with specific question\n5. Keep under 120 characters\n6. NO meta-commentary\n\n\ud83d\udd25 OUTPUT ONLY THE MESSAGE TEXT - NO JSON, NO EXPLANATIONS:\n",
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
      "optimal_length": [
        50,
        120
      ],
      "high_converting_elements": [
        "personal_name",
        "company_reference",
        "question_ending",
        "value_first",
        "curiosity_gap"
      ],
      "timing_words": [
        "noticed",
        "saw",
        "quick question",
        "curious",
        "wondering"
      ],
      "forbidden_phrases": [
        "Here's a",
        "I'll create",
        "Okay, here's",
        "Let me craft"
      ]
    },
    "anti_hallucination_rules": {
      "never_mention": [
        "specific_meetings_not_in_crm",
        "unverified_news",
        "specific_people_not_mentioned",
        "unverified_metrics"
      ],
      "safe_assumptions": [
        "industry_challenges",
        "common_mongodb_use_cases",
        "technology_trends",
        "role_pain_points"
      ]
    },
    "fallback_message_template": "Hi {lead_name}! I specialize in MongoDB solutions and help {industry} companies optimize their data infrastructure. Quick question - what's your biggest database challenge right now?",
    "emergency_fallback": "Hi {lead_name}! MongoDB Solutions Architect here. Would love to connect about database optimization opportunities at {company}. Quick chat?"
  },
  "message_quality_optimizer": {
    "target_response_rate": 0.4,
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
  "multimodal_message_agent": {
    "output_directory": "tmp",
    "voice_generation": {
      "enabled": false,
      "voice_model": "alloy",
      "audio_format": "wav"
    },
    "image_generation": {
      "enabled": true,
      "model": "gemini-2.0-flash-exp-image-generation",
      "response_modalities": [
        "Text",
        "Image"
      ]
    }
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
      "exponential_backoff": true
    },
    "status_tracking": {
      "check_interval_seconds": 30,
      "delivery_timeout_minutes": 10,
      "read_timeout_minutes": 60
    },
    "monday_integration": {
      "status_field": "lead_status",
      "update_notes": true,
      "create_activities": true
    }
  },
  "research_agent": {
    "enhanced_research_prompt_template": "\nYou are an elite sales intelligence researcher with 15+ years of B2B experience, specializing in {product_name} and {product_category}. Your mission is to create hyper-personalized outreach by analyzing EVERY piece of available data.\n\nENHANCED RESEARCH METHODOLOGY:\n1. MONDAY.COM CRM ANALYSIS:\n   - Analyze ALL lead notes, interaction history, custom fields\n   - Identify previous touchpoints, preferences, pain points\n   - Extract relationship context and communication patterns\n   - Note any {product_category}-related mentions or needs\n\n2. DEEP COMPANY INTELLIGENCE:\n   - Recent news, funding, acquisitions, leadership changes\n   - Technology stack analysis (current {product_category} infrastructure)\n   - Growth signals, scaling challenges, technical debt indicators\n   - Competitor analysis and market positioning\n\n3. {product_name_upper} RELEVANCE ASSESSMENT:\n   - Current {product_category} infrastructure challenges\n   - Initiatives requiring {product_name} capabilities\n   - Scaling issues that {product_name} could solve\n   - Operational needs matching {product_name} strengths\n\n4. HYPER-PERSONALIZATION FACTORS:\n   - Industry-specific {product_name} use cases\n   - Company size and growth stage implications\n   - Technical decision-maker background\n   - Timing signals for {product_category} modernization\n\nOUTPUT REQUIREMENTS:\n- Comprehensive Context Score (0.0-1.0) based on data richness\n- CRM Insights (everything relevant from Monday.com)\n- Company Intelligence (recent developments + {product_name} relevance)\n- Personalization Hooks (specific, actionable conversation starters)\n- {product_name} Opportunity Assessment (why they need {product_name} now)\n\nQUALITY STANDARDS:\n- Analyze EVERY piece of CRM data for relevance\n- Prioritize recent events and specific details\n- Focus on {product_name}-relevant pain points and opportunities\n- Provide context for why each insight enables hyper-personalization\n\nRemember: You're building the foundation for messages so personalized they feel like they came from someone who knows the prospect personally.\n\nReturn your findings in this exact JSON format:\n{{\n    \"confidence_score\": 0.85,\n    \"crm_analysis\": {{\n        \"data_richness\": \"Assessment of CRM data quality\",\n        \"interaction_history\": [\"Key interactions and touchpoints\"],\n        \"relationship_context\": \"Current relationship status and history\",\n        \"product_signals\": [\"Any {product_category}/{product_name} mentions in CRM\"]\n    }},\n    \"company_intelligence\": {{\n        \"recent_news\": \"Specific recent news or developments\",\n        \"growth_signals\": [\"List of growth indicators\"],\n        \"challenges\": [\"List of challenges or pain points\"],\n        \"technology_stack\": \"Current {product_category}/tech infrastructure insights\"\n    }},\n    \"product_opportunity\": {{\n        \"relevance_score\": 0.8,\n        \"use_cases\": [\"Specific {product_name} use cases for this company\"],\n        \"pain_points\": [\"{product_category} challenges {product_name} could solve\"],\n        \"timing_signals\": [\"Why {product_name} adoption makes sense now\"]\n    }},\n    \"hyper_personalization\": {{\n        \"strongest_hooks\": [\"Top 3 most compelling conversation starters\"],\n        \"personal_context\": \"Individual-specific insights about the lead\",\n        \"company_context\": \"Company-specific insights for personalization\"\n    }},\n    \"timing_rationale\": \"Why reaching out now makes perfect sense\"\n}}\n",
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
      "include_answer": true,
      "include_raw_content": false
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
      "engagement_metrics": [
        "delivered",
        "read",
        "replied"
      ]
    }
  },
  "workflow_coordinator": {
    "team_coordination": {
      "mode": "coordinate",
      "success_criteria": "Lead successfully processed through complete workflow with high-quality research, personalized message, and successful outreach delivery",
      "enable_agentic_context": true
    },
    "quality_thresholds": {
      "research_confidence_minimum": 0.5,
      "personalization_score_minimum": 0.8,
      "response_rate_minimum": 0.4
    },
    "progress_tracking": {
      "store_in_mongodb": true,
      "collection_name": "workflow_progress",
      "update_frequency": "real_time"
    }
  }
}
```

### Collection: `contacts`

```json
{
  "_id": {
    "$oid": "6851979d602717e741ad59a7"
  },
  "monday_item_id": "agno_1750177692181_81c4q05q8",
  "board_id": "2001047343",
  "comprehensive_data": {
    "monday_id": "agno_1750177692181_81c4q05q8",
    "name": "Unknown Lead",
    "company": "Unknown Company",
    "all_column_data": {},
    "notes_and_updates": [],
    "crm_insights": {
      "data_richness_score": 0.1
    }
  },
  "last_updated": "2025-06-17T19:28:12.970314",
  "data_source": "monday_api"
}
```

### Collection: `workflow_progress`

```json
{
  "_id": {
    "$oid": "68506f1c602717e741ad5972"
  },
  "workflow_id": "workflow_20250616_222308_test-lead-123",
  "completed_at": null,
  "current_step": "Executing outreach",
  "error_message": null,
  "message_output": {
    "message_text": "John, noticed you're leading sales at Test Company. Many VPs we work with are wrestling with increasing sales velocity in this market. We're helping companies like yours use AI to automate follow-ups and personalize outreach at scale. Curious, what's your biggest focus for improving sales performance this quarter?",
    "message_voice_script": "Hi John, Sarah Smith from Our Company here. As VP of Sales, I know you're probably dealing with a lot. We've been helping companies similar to Test Company leverage AI to streamline their sales process and boost velocity, especially with the current market conditions. What's top of mind for you in terms of improving your team's output this quarter?",
    "message_image_concept": "Image featuring the Test Company logo alongside a graphic illustrating increased sales velocity. Text overlay: 'AI-Powered Sales Automation for Test Company: Unlock Growth.'",
    "personalization_score": 0.85,
    "predicted_response_rate": 0.4,
    "generation_timestamp": "2025-06-16T22:23:16.283566",
    "message_length": 315,
    "tone_analysis": "Professional, timely, value-focused"
  },
  "outreach_result": null,
  "progress_percentage": 75.0,
  "research_output": {
    "confidence_score": 0.75,
    "company_intelligence": {
      "recent_news": "No significant news found in the last 6 months.",
      "growth_signals": [
        "Limited information available to determine growth signals. Further investigation needed.",
        "Company size indicates established presence but specific growth metrics are unavailable without more data."
      ],
      "challenges": [
        "General challenges within the technology industry, such as rapid innovation and competition.",
        "Specific challenges are difficult to ascertain without deeper insights into Test Company's focus and market position."
      ]
    },
    "decision_maker_insights": {
      "background": "Assuming a standard VP of Sales background, likely with 10+ years of experience in sales leadership roles within the technology sector. Experience in building and scaling sales teams, developing sales strategies, and driving revenue growth.",
      "recent_activities": [
        "Unable to determine recent activities without access to LinkedIn or other professional networking platforms. Need to search for John Doe on LinkedIn to gather more information."
      ]
    },
    "conversation_hooks": [
      "Discuss current trends in the technology sales landscape and how Test Company is adapting its sales strategies.",
      "Inquire about Test Company's biggest sales challenges and explore potential solutions.",
      "Share insights on innovative sales techniques or technologies that could benefit Test Company's sales team."
    ],
    "timing_rationale": "Reaching out now is generally a good time as companies are often planning for the next quarter or year, making them receptive to new ideas and solutions to improve sales performance. However, specific timing would be better informed by identifying a trigger event or announcement related to Test Company or John Doe.",
    "research_timestamp": "2025-06-16T22:23:12.830765",
    "sources": []
  },
  "started_at": "2025-06-16T19:23:08.570925+00:00",
  "status": "outreach_in_progress",
  "total_steps": 3
}
```

### Collection: `research_results`

```json
{
  "_id": {
    "$oid": "68505a1de9305fd34268d52d"
  },
  "research_id": "research_tesla_elon_musk_20250616_175333",
  "lead_name": "Elon Musk",
  "company": "Tesla",
  "title": "CEO",
  "industry": "Electric Vehicles",
  "company_size": "100,000+ employees",
  "confidence_score": 1.0,
  "company_intelligence": {
    "recent_news": "Tesla recently announced record Q1 2024 vehicle deliveries despite production headwinds and is focusing on the ramp-up of its next-generation vehicle platform.",
    "growth_signals": [
      "Expansion of charging infrastructure network globally.",
      "Continued investment in AI and autonomous driving technology.",
      "Significant growth in energy storage solutions (Megapack, Powerwall).",
      "Ramping up production at Gigafactory Texas."
    ],
    "challenges": [
      "Supply chain disruptions and raw material price volatility.",
      "Increasing competition from established automakers and new EV startups.",
      "Regulatory scrutiny regarding autonomous driving features and safety.",
      "Maintaining profitability amidst price cuts."
    ],
    "market_position": "",
    "financial_status": "",
    "competitive_landscape": ""
  },
  "decision_maker_insights": {
    "background": "Elon Musk is the CEO of Tesla, known for his focus on innovation, sustainable energy, and disruptive technologies. He is heavily involved in product development, strategic planning, and public communication.",
    "recent_activities": [
      "Active on X (formerly Twitter), commenting on industry trends, technology advancements, and company updates.",
      "Participating in earnings calls and investor conferences, discussing Tesla's financial performance and future outlook.",
      "Visiting Gigafactories and engaging with employees on production and engineering challenges."
    ],
    "professional_interests": [],
    "pain_points": [],
    "decision_making_style": ""
  },
  "conversation_hooks": [
    "Regarding the Q1 2024 delivery numbers, what strategies are you implementing to mitigate supply chain vulnerabilities and ensure consistent production?",
    "With increasing competition in the EV market, how is Tesla differentiating its products and services to maintain its market leadership position, especially concerning the next-generation vehicle platform?",
    "Given the regulatory landscape surrounding autonomous driving, what proactive measures are you taking to address safety concerns and ensure compliance while pushing the boundaries of innovation?"
  ],
  "timing_rationale": "Tesla's recent Q1 2024 results and ongoing efforts to scale production of new vehicles present a timely opportunity to engage in discussions about optimizing supply chains, navigating competitive pressures, and addressing regulatory challenges. Also, the ramp-up of the next-generation vehicle platform would be a good conversation starter.",
  "sources": [],
  "research_timestamp": "2025-06-16T20:53:33.291716",
  "created_at": "2025-06-16T17:53:33.292250+00:00",
  "updated_at": "2025-06-16T17:53:33.292251+00:00",
  "status": "completed",
  "error_message": null
}
```

### Collection: `interaction_history`

```json
{
  "_id": {
    "$oid": "685068088caab9bf65d80942"
  },
  "interaction_id": "sent_test_123_1750099976",
  "lead_id": "lead_456",
  "lead_name": "Test Lead",
  "company": "Test Corp",
  "interaction_type": "message_sent",
  "timestamp": "2025-06-16T18:52:56.194650+00:00",
  "details": {
    "message_content": "Test message",
    "message_id": "test_123"
  },
  "whatsapp_message_id": "test_123",
  "monday_item_id": "lead_456",
  "status_before": "queued",
  "status_after": "sent"
}
```

### Collection: `message_queue`

*No documents found in this collection or could not fetch a sample.*

### Collection: `research_agent_sessions`

*Collection not found in the database.*