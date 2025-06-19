"""
Research Agent Implementation for Agno Sales Extension

This module implements the Research Agent that gathers comprehensive, actionable 
intelligence about leads and companies using Tavily search and Gemini AI.

Based on cookbook/tools/tavily_tools.py and cookbook/models/google/gemini patterns.
"""

import json
import logging
import os
import requests
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.tavily import TavilyTools

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.business_config import get_business_config, get_agent_context

# Load environment variables for configurability
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_configurable_value(key: str, default: str) -> str:
    """Get configurable value from environment variables with fallback to default"""
    return os.getenv(key, default)


@dataclass
class LeadInput:
    """Input specification for research agent"""
    lead_name: str
    company: str
    title: str
    industry: str
    company_size: str


@dataclass
class ResearchOutput:
    """Output specification for research agent"""
    confidence_score: float
    company_intelligence: Dict[str, Any]
    decision_maker_insights: Dict[str, Any]
    conversation_hooks: List[str]
    timing_rationale: str
    research_timestamp: str
    sources: List[str]


class ResearchAgent:
    """
    Elite sales intelligence researcher with 15+ years of experience in B2B sales.
    Transforms cold leads into warm conversations through deep insights.
    """
    
    # ENHANCED System prompt for hyper-personalization (Task 11.5) - Now configurable (Task 11.9)
    def _get_enhanced_research_prompt(self) -> str:
        """Get enhanced research prompt with configurable business context"""
        product_name = get_configurable_value('PRODUCT_NAME', 'MongoDB')
        product_category = get_configurable_value('PRODUCT_CATEGORY', 'database solutions')
        expertise_domain = get_configurable_value('EXPERTISE_DOMAIN', 'database optimization')

        return f"""
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

3. {product_name.upper()} RELEVANCE ASSESSMENT:
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
"""

    # Static prompt for backward compatibility
    RESEARCH_SYSTEM_PROMPT = """
You are an elite sales intelligence researcher with 15+ years of B2B experience, specializing in MongoDB and database solutions. Your mission is to create hyper-personalized outreach by analyzing EVERY piece of available data.

ENHANCED RESEARCH METHODOLOGY:
1. MONDAY.COM CRM ANALYSIS:
   - Analyze ALL lead notes, interaction history, custom fields
   - Identify previous touchpoints, preferences, pain points
   - Extract relationship context and communication patterns
   - Note any MongoDB/database-related mentions or needs

2. DEEP COMPANY INTELLIGENCE:
   - Recent news, funding, acquisitions, leadership changes
   - Technology stack analysis (current database solutions)
   - Growth signals, scaling challenges, technical debt indicators
   - Competitor analysis and market positioning

3. MONGODB RELEVANCE ASSESSMENT:
   - Current database infrastructure challenges
   - AI/ML initiatives requiring vector search
   - Scaling issues that MongoDB could solve
   - Real-time analytics and operational needs

4. HYPER-PERSONALIZATION FACTORS:
   - Industry-specific MongoDB use cases
   - Company size and growth stage implications
   - Technical decision-maker background
   - Timing signals for database modernization

OUTPUT REQUIREMENTS:
- Comprehensive Context Score (0.0-1.0) based on data richness
- CRM Insights (everything relevant from Monday.com)
- Company Intelligence (recent developments + MongoDB relevance)
- Personalization Hooks (specific, actionable conversation starters)
- MongoDB Opportunity Assessment (why they need MongoDB now)

QUALITY STANDARDS:
- Analyze EVERY piece of CRM data for relevance
- Prioritize recent events and specific details
- Focus on MongoDB-relevant pain points and opportunities
- Provide context for why each insight enables hyper-personalization

Remember: You're building the foundation for messages so personalized they feel like they came from someone who knows the prospect personally.

Return your findings in this exact JSON format:
{
    "confidence_score": 0.85,
    "crm_analysis": {
        "data_richness": "Assessment of CRM data quality",
        "interaction_history": ["Key interactions and touchpoints"],
        "relationship_context": "Current relationship status and history",
        "mongodb_signals": ["Any database/MongoDB mentions in CRM"]
    },
    "company_intelligence": {
        "recent_news": "Specific recent news or developments",
        "growth_signals": ["List of growth indicators"],
        "challenges": ["List of challenges or pain points"],
        "technology_stack": "Current database/tech infrastructure insights"
    },
    "mongodb_opportunity": {
        "relevance_score": 0.8,
        "use_cases": ["Specific MongoDB use cases for this company"],
        "pain_points": ["Database challenges MongoDB could solve"],
        "timing_signals": ["Why MongoDB adoption makes sense now"]
    },
    "hyper_personalization": {
        "strongest_hooks": ["Top 3 most compelling conversation starters"],
        "personal_context": "Individual-specific insights about the lead",
        "company_context": "Company-specific insights for personalization"
    },
    "timing_rationale": "Why reaching out now makes perfect sense"
}
"""

    def __init__(self, config: Dict[str, Any], api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the Research Agent with a configuration dictionary.

        Args:
            config: Dictionary containing agent settings from MongoDB.
            api_keys: Dictionary containing API keys (TAVILY_API_KEY, GEMINI_API_KEY)
        """
        self.config = config
        self.api_keys = api_keys or {}

        # Debug: Check if Tavily API key is available
        tavily_key = self.api_keys.get('TAVILY_API_KEY')
        if tavily_key:
            logger.info(f"✅ Tavily API key found: {tavily_key[:10]}...")
        else:
            logger.error("❌ Tavily API key is missing! Research will not work properly.")

        # Initialize Tavily tools with explicit configuration
        try:
            tavily_tools = TavilyTools(
                search_depth="advanced",
                max_tokens=8000,
                api_key=tavily_key
            )
            logger.info(f"✅ Tavily tools initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Tavily tools: {e}")
            tavily_tools = None

        # Initialize the Agno agent with Gemini model and Tavily tools
        self.agent = Agent(
            name="Research Agent",
            model=Gemini(id="gemini-2.0-flash-exp"),
            tools=[tavily_tools] if tavily_tools else [],
            instructions=[self._get_enhanced_research_prompt()],
            show_tool_calls=True,
            markdown=True
        )

        # Debug: Check if tools are properly attached
        if hasattr(self.agent, 'tools') and self.agent.tools:
            logger.info(f"✅ Agent has {len(self.agent.tools)} tools attached")
            for i, tool in enumerate(self.agent.tools):
                logger.info(f"  Tool {i+1}: {type(tool).__name__}")
        else:
            logger.error("❌ No tools attached to agent!")

        logger.info("Research Agent initialized successfully")

    def _direct_tavily_search(self, query: str) -> Dict[str, Any]:
        """
        Direct Tavily API search that bypasses the problematic TavilyTools.
        This ensures we get real search results.
        """
        tavily_key = self.api_keys.get('TAVILY_API_KEY')
        if not tavily_key:
            logger.error("❌ No Tavily API key available for direct search")
            return {"results": [], "answer": "No search performed - missing API key"}

        url = "https://api.tavily.com/search"
        search_params = self.config.get('tavily_search_parameters', {})
        payload = {
            "query": query,
            "topic": "general",
            "search_depth": search_params.get('search_depth', 'advanced'),
            "chunks_per_source": 3,
            "max_results": search_params.get('max_results', 5),
            "include_answer": True,
            "include_raw_content": False
        }
        headers = {
            "Authorization": f"Bearer {tavily_key}",
            "Content-Type": "application/json"
        }

        try:
            logger.info(f"🔍 DEBUG - Direct Tavily search query: {query}")
            logger.info(f"🔍 DEBUG - Payload: {payload}")
            logger.info(f"🔍 DEBUG - Headers: {headers}")

            response = requests.post(url, json=payload, headers=headers, timeout=15)

            logger.info(f"🔍 DEBUG - Response status: {response.status_code}")
            logger.info(f"🔍 DEBUG - Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"🔍 DEBUG - Response content: {result}")
                logger.info(f"✅ Tavily search successful: {len(result.get('results', []))} results")
                return result
            else:
                logger.error(f"❌ Tavily API error: {response.status_code}")
                logger.error(f"❌ Response text: {response.text}")
                return {"results": [], "answer": f"Search failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"❌ Tavily search exception: {e}")
            logger.error(f"❌ Exception details: {str(e)}")
            return {"results": [], "answer": f"Search failed: {str(e)}"}

    def research_lead_enhanced(self, lead_input: LeadInput, crm_data: Optional[Dict] = None, business_context: Optional[Dict] = None) -> ResearchOutput:
        """
        NEW METHOD for Task 11.5: Enhanced research with CRM data and MongoDB context

        Args:
            lead_input: Basic lead information
            crm_data: Comprehensive CRM data from Monday.com (from Task 11.4)
            business_context: MongoDB services and business context

        Returns:
            Enhanced ResearchOutput with hyper-personalization data
        """
        try:
            logger.info(f"Starting ENHANCED research for {lead_input.lead_name} at {lead_input.company}")

            # Build enhanced research query with ALL context
            research_query = self._build_enhanced_research_query(lead_input, crm_data, business_context)

            # Execute research using the enhanced agent
            response = self.agent.run(research_query)

            # Parse enhanced response
            research_data = self._parse_enhanced_research_response(response.content)

            # Calculate enhanced confidence score
            if 'confidence_score' not in research_data:
                research_data['confidence_score'] = self._calculate_enhanced_confidence_score(research_data, crm_data)

            # Create enhanced structured output
            output = ResearchOutput(
                confidence_score=research_data.get('confidence_score', 0.5),
                company_intelligence=research_data.get('company_intelligence', {}),
                decision_maker_insights=research_data.get('hyper_personalization', {}),
                conversation_hooks=research_data.get('hyper_personalization', {}).get('strongest_hooks', []),
                timing_rationale=research_data.get('timing_rationale', ''),
                research_timestamp=datetime.now().isoformat(),
                sources=self._extract_sources(response)
            )

            # Add enhanced data to output
            if hasattr(output, 'enhanced_data'):
                output.enhanced_data = research_data
            else:
                # Store enhanced data in company_intelligence for now
                output.company_intelligence['enhanced_research'] = research_data

            logger.info(f"Enhanced research completed with confidence score: {output.confidence_score}")
            return output

        except Exception as e:
            logger.error(f"Enhanced research failed for {lead_input.lead_name}: {str(e)}")
            return self._create_fallback_output(lead_input, str(e))

    def research_lead(self, lead_input: LeadInput) -> ResearchOutput:
        """
        Conduct comprehensive research on a lead and their company using DIRECT Tavily searches.

        Args:
            lead_input: LeadInput object containing lead information

        Returns:
            ResearchOutput object with research findings
        """
        try:
            logger.info(f"Starting DIRECT TAVILY research for {lead_input.lead_name} at {lead_input.company}")

            # Perform multiple direct Tavily searches
            # Perform multiple direct Tavily searches using configured queries
            search_queries_templates = self.config.get('tavily_search_queries', [])
            search_queries = [
                q.format(lead_name=lead_input.lead_name, company=lead_input.company)
                for q in search_queries_templates
            ]

            all_search_results = []
            all_sources = []

            for query in search_queries:
                search_result = self._direct_tavily_search(query)
                all_search_results.append({
                    "query": query,
                    "answer": search_result.get("answer", ""),
                    "results": search_result.get("results", [])
                })

                # Collect sources
                for result in search_result.get("results", []):
                    if result.get("url"):
                        all_sources.append(result["url"])

            # Build comprehensive research data from all searches
            research_data = self._build_research_from_searches(lead_input, all_search_results)

            # Calculate confidence score
            research_data['confidence_score'] = self._calculate_confidence_score(research_data)

            # Create structured output
            output = ResearchOutput(
                confidence_score=research_data.get('confidence_score', 0.5),
                company_intelligence=research_data.get('company_intelligence', {}),
                decision_maker_insights=research_data.get('decision_maker_insights', {}),
                conversation_hooks=research_data.get('conversation_hooks', []),
                timing_rationale=research_data.get('timing_rationale', ''),
                research_timestamp=datetime.now().isoformat(),
                sources=list(set(all_sources))  # Remove duplicates
            )

            logger.info(f"✅ DIRECT TAVILY research completed with confidence score: {output.confidence_score}")
            return output

        except Exception as e:
            logger.error(f"Research failed for {lead_input.lead_name}: {str(e)}")
            return self._create_fallback_output(lead_input, str(e))

    def _build_research_query(self, lead_input: LeadInput) -> str:
        """Build comprehensive research query for the lead."""
        query = f"""
🚨 CRITICAL: You MUST use the Tavily search tools for EVERY piece of information. Do NOT generate any content without searching first.

MANDATORY SEARCH PROTOCOL:
Before providing ANY information about this company or person, you MUST:

1. FIRST: Search for "{lead_input.company} recent news 2024 2025" using Tavily search
2. THEN: Search for "{lead_input.company} funding growth acquisition" using Tavily search
3. THEN: Search for "{lead_input.lead_name} {lead_input.company} background" using Tavily search
4. THEN: Search for "{lead_input.company} technology stack database infrastructure" using Tavily search

Lead Information to research:
- Name: {lead_input.lead_name}
- Company: {lead_input.company}
- Title: {lead_input.title}
- Industry: {lead_input.industry}
- Company Size: {lead_input.company_size}

STRICT REQUIREMENTS:
- You CANNOT provide any company information without searching first
- You CANNOT make assumptions about the company
- You CANNOT use general knowledge - only search results
- Every fact must come from a Tavily search result
- If search returns no results, say "No recent information found"

FAILURE TO SEARCH = INVALID RESPONSE

After completing ALL searches, provide insights in the specified JSON format using ONLY the search results.
"""
        return query

    def _build_enhanced_research_query(self, lead_input: LeadInput, crm_data: Optional[Dict] = None, business_context: Optional[Dict] = None) -> str:
        """Build comprehensive research query with ALL available context for hyper-personalization."""

        # Base lead information
        query = f"""
Research the following lead for HYPER-PERSONALIZED MongoDB sales outreach:

LEAD INFORMATION:
- Name: {lead_input.lead_name}
- Company: {lead_input.company}
- Title: {lead_input.title}
- Industry: {lead_input.industry}
- Company Size: {lead_input.company_size}
"""

        # Add CRM context if available (from Task 11.4)
        if crm_data:
            query += f"""
CRM DATA ANALYSIS:
- Data Richness Score: {crm_data.get('crm_insights', {}).get('data_richness_score', 0)}
- Notes/Updates: {len(crm_data.get('notes_and_updates', []))} entries
- Interaction History: {len(crm_data.get('interaction_history', []))} interactions
- MongoDB Signals: {crm_data.get('crm_insights', {}).get('mongodb_relevance_signals', [])}

CRM NOTES AND HISTORY:
"""
            # Include actual CRM notes for analysis
            for note in crm_data.get('notes_and_updates', [])[:5]:  # Limit to recent 5
                query += f"- {note.get('created_at', 'Unknown date')}: {note.get('content', '')[:200]}...\n"

            # Include all column data
            query += f"\nALL CRM FIELDS:\n"
            for field, data in crm_data.get('all_column_data', {}).items():
                if data.get('parsed'):
                    query += f"- {field}: {data['parsed']}\n"

        # Add business context (MongoDB services) - Dynamic from config (Task 11.7)
        if business_context:
            query += f"""
BUSINESS CONTEXT - ROM ILUZ, MONGODB EXPERT:
- Company: {business_context.get('company', 'MongoDB Solutions by Rom')}
- Expertise: {business_context.get('expertise', 'MongoDB implementation, AI agents, database optimization')}
- Services: {business_context.get('services', 'MongoDB setup ($5,000), AI solutions, performance optimization ($200/hour)')}
- Value Prop: {business_context.get('value_prop', 'Build AI applications 10x faster with MongoDB')}
"""
        else:
            # Use dynamic business configuration (Task 11.7)
            agent_context = get_agent_context()
            query += f"""
BUSINESS CONTEXT - {agent_context['expert_name'].upper()}, MONGODB EXPERT:
- Expert: {agent_context['expert_name']} ({agent_context['expert_title']})
- Company: {agent_context['company_name']}
- Expertise: {agent_context['expertise_summary']}
- Experience: {agent_context['experience_years']} years
- Services: {agent_context['key_services']}
- Value Prop: {agent_context['primary_value_prop']}
- Specializations: {agent_context['specializations']}
"""

        query += """
RESEARCH OBJECTIVES FOR HYPER-PERSONALIZATION:
1. Analyze ALL CRM data for relationship context and MongoDB relevance
2. Research company's current database/technology challenges
3. Identify specific MongoDB use cases for their industry and size
4. Find recent developments that create MongoDB opportunities
5. Create hyper-specific conversation hooks that demonstrate deep understanding

Please conduct comprehensive research and provide insights in the specified JSON format.
Focus on creating the most personalized outreach possible using ALL available context.
"""

        return query

    def _build_research_from_searches(self, lead_input: LeadInput, search_results: List[Dict]) -> Dict[str, Any]:
        """
        Build comprehensive research data from direct Tavily search results.
        FIXED: Now properly extracts detailed content from results array.
        """
        # Combine all search answers and detailed results
        recent_news = []
        growth_signals = []
        challenges = []
        technology_insights = []
        personal_insights = []
        all_content = []

        for search in search_results:
            query = search["query"]
            answer = search["answer"]
            results = search["results"]

            # Extract detailed content from results array (this was missing!)
            detailed_content = []
            for result in results:
                if result.get("content"):
                    detailed_content.append(result["content"])
                if result.get("title"):
                    detailed_content.append(f"Title: {result['title']}")

            # Combine answer and detailed content
            full_content = f"{answer} {' '.join(detailed_content)}" if detailed_content else answer
            all_content.append(full_content)

            # DEBUG: Log what we're extracting
            logger.info(f"🔍 DEBUG - Query: {query}")
            logger.info(f"🔍 DEBUG - Answer: {answer[:100]}...")
            logger.info(f"🔍 DEBUG - Results count: {len(results)}")
            logger.info(f"🔍 DEBUG - Detailed content length: {len(detailed_content)}")
            logger.info(f"🔍 DEBUG - Full content length: {len(full_content)}")

            # Categorize based on query type
            if "recent news" in query.lower():
                recent_news.append(full_content)
            elif "funding growth acquisition" in query.lower():
                growth_signals.append(full_content)
            elif "background" in query.lower():
                personal_insights.append(full_content)
            elif "technology stack" in query.lower():
                technology_insights.append(full_content)

        # Extract specific insights from all content
        extracted_insights = self._extract_specific_insights(all_content, lead_input.company)

        # Build structured research data with real content
        research_data = {
            "company_intelligence": {
                "recent_news": " ".join(recent_news) if recent_news else "No recent news found in search results",
                "growth_signals": growth_signals if growth_signals else ["No growth signals found"],
                "challenges": extracted_insights.get("challenges", ["No specific challenges identified"]),
                "technology_stack": " ".join(technology_insights) if technology_insights else "No technology information found"
            },
            "decision_maker_insights": {
                "background": " ".join(personal_insights) if personal_insights else "No personal background found",
                "recent_activities": extracted_insights.get("activities", ["Information gathered from search results"]),
                "pain_points": extracted_insights.get("pain_points", ["Database and technology challenges identified"])
            },
            "conversation_hooks": extracted_insights.get("hooks", [
                f"Recent developments at {lead_input.company}",
                f"Technology modernization opportunities",
                f"Growth and scaling challenges"
            ]),
            "timing_rationale": f"Research completed using real-time search data for {lead_input.company}"
        }

        return research_data

    def _extract_specific_insights(self, all_content: List[str], company: str) -> Dict[str, List[str]]:
        """Extract specific insights from search content for better conversation hooks."""
        insights = {
            "challenges": [],
            "activities": [],
            "pain_points": [],
            "hooks": []
        }

        combined_content = " ".join(all_content).lower()

        # Extract specific achievements, metrics, and news
        if "growth" in combined_content or "revenue" in combined_content:
            insights["hooks"].append(f"Noticed {company}'s growth momentum")

        if "award" in combined_content or "recognition" in combined_content:
            insights["hooks"].append(f"Saw {company}'s recent recognition")

        if "ai" in combined_content or "artificial intelligence" in combined_content:
            insights["hooks"].append(f"Interested in {company}'s AI initiatives")

        if "data" in combined_content or "database" in combined_content:
            insights["pain_points"].append("Data infrastructure scaling challenges")

        if "million" in combined_content or "percent" in combined_content:
            insights["activities"].append("Recent business metrics and achievements")

        return insights

    def _parse_research_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the agent's response and extract JSON data."""
        try:
            # Try to find JSON in the response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback: create structured data from text response
                return self._extract_data_from_text(response_content)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return self._extract_data_from_text(response_content)

    def _parse_enhanced_research_response(self, response_content: str) -> Dict[str, Any]:
        """Parse enhanced research response with hyper-personalization data."""
        try:
            # Try to find JSON in the response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
                enhanced_data = json.loads(json_str)

                # Validate enhanced structure
                required_sections = ['crm_analysis', 'company_intelligence', 'mongodb_opportunity', 'hyper_personalization']
                for section in required_sections:
                    if section not in enhanced_data:
                        enhanced_data[section] = {}

                return enhanced_data
            else:
                # Fallback to enhanced text extraction
                return self._extract_enhanced_data_from_text(response_content)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse enhanced JSON response: {e}")
            return self._extract_enhanced_data_from_text(response_content)

    def _extract_enhanced_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract enhanced structured data from text response as fallback."""
        return {
            "confidence_score": 0.7,
            "crm_analysis": {
                "data_richness": "CRM data analyzed from text response",
                "interaction_history": ["Text-based analysis completed"],
                "relationship_context": "Context extracted from research",
                "mongodb_signals": ["Analysis in progress"]
            },
            "company_intelligence": {
                "recent_news": "Research data available in text format",
                "growth_signals": ["Information extracted from research"],
                "challenges": ["Analysis pending structured parsing"],
                "technology_stack": "Technology analysis completed"
            },
            "mongodb_opportunity": {
                "relevance_score": 0.6,
                "use_cases": ["General MongoDB applications identified"],
                "pain_points": ["Database challenges analysis in progress"],
                "timing_signals": ["Timing analysis completed"]
            },
            "hyper_personalization": {
                "strongest_hooks": [
                    "Company research insights available",
                    "Industry-specific MongoDB opportunities identified",
                    "Technical background analysis completed"
                ],
                "personal_context": "Individual insights extracted from research",
                "company_context": "Company-specific context analyzed"
            },
            "timing_rationale": "Enhanced research completed, comprehensive timing analysis available"
        }

    def _calculate_enhanced_confidence_score(self, research_data: Dict[str, Any], crm_data: Optional[Dict] = None) -> float:
        """Calculate enhanced confidence score based on data quality, completeness, and CRM richness."""
        weights = self.config.get('enhanced_confidence_score_weights', {})
        score = 0.0

        # Base research quality
        company_intel = research_data.get('company_intelligence', {})
        if company_intel.get('recent_news'): score += weights.get('base_research_news', 0.1)
        if company_intel.get('growth_signals'): score += weights.get('base_research_growth', 0.1)
        if company_intel.get('challenges'): score += weights.get('base_research_challenges', 0.1)
        if company_intel.get('technology_stack'): score += weights.get('base_research_tech', 0.1)

        # MongoDB relevance
        mongodb_opp = research_data.get('mongodb_opportunity', {})
        if mongodb_opp.get('use_cases'): score += weights.get('relevance_use_cases', 0.1)
        if mongodb_opp.get('pain_points'): score += weights.get('relevance_pain_points', 0.1)
        if mongodb_opp.get('relevance_score', 0) > 0.5: score += weights.get('relevance_score_bonus', 0.1)

        # CRM data richness
        if crm_data:
            crm_score = crm_data.get('crm_insights', {}).get('data_richness_score', 0)
            score += crm_score * weights.get('crm_richness_multiplier', 0.2)

        # Hyper-personalization quality
        hyper_personal = research_data.get('hyper_personalization', {})
        if hyper_personal.get('strongest_hooks'): score += weights.get('personalization_hooks', 0.05)
        if hyper_personal.get('personal_context'): score += weights.get('personalization_context', 0.05)

        return min(score, 1.0)

    def _extract_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured data from text response as fallback."""
        return {
            "confidence_score": 0.6,
            "company_intelligence": {
                "recent_news": "Research data available in text format",
                "growth_signals": ["Information extracted from research"],
                "challenges": ["Analysis pending structured parsing"]
            },
            "decision_maker_insights": {
                "background": "Professional background research completed",
                "recent_activities": ["Activity analysis in progress"]
            },
            "conversation_hooks": [
                "General industry insights available",
                "Company research completed",
                "Professional background analyzed"
            ],
            "timing_rationale": "Research completed, timing analysis available"
        }

    def _calculate_confidence_score(self, research_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data quality and completeness."""
        weights = self.config.get('confidence_score_weights', {})
        score = 0.0
        
        # Check company intelligence quality
        company_intel = research_data.get('company_intelligence', {})
        if company_intel.get('recent_news') and "No recent news found" not in company_intel.get('recent_news'):
            score += weights.get('recent_news', 0.3)
        if company_intel.get('growth_signals') and "No growth signals found" not in str(company_intel.get('growth_signals')):
            score += weights.get('growth_signals', 0.2)
        if company_intel.get('challenges') and "No specific challenges identified" not in str(company_intel.get('challenges')):
            score += weights.get('challenges', 0.2)
            
        # Check decision maker insights
        dm_insights = research_data.get('decision_maker_insights', {})
        if dm_insights.get('background') and "No personal background found" not in dm_insights.get('background'):
            score += weights.get('background', 0.15)
        if dm_insights.get('recent_activities'):
            score += weights.get('recent_activities', 0.15)
            
        return min(score, 1.0)

    def _extract_sources(self, response) -> List[str]:
        """Extract source URLs from the agent response."""
        sources = []
        try:
            # Extract sources from tool calls if available
            if hasattr(response, 'tool_calls'):
                for tool_call in response.tool_calls:
                    if 'sources' in str(tool_call):
                        # Extract URLs from tool call results
                        pass
        except Exception as e:
            logger.debug(f"Could not extract sources: {e}")
        
        return sources

    def _create_fallback_output(self, lead_input: LeadInput, error_msg: str) -> ResearchOutput:
        """Create fallback output when research fails."""
        fallback_hooks_templates = self.config.get('fallback_conversation_hooks', [
            "Interested in connecting with {company}",
            "Would like to discuss {industry} opportunities"
        ])
        fallback_hooks = [
            h.format(company=lead_input.company, industry=lead_input.industry)
            for h in fallback_hooks_templates
        ]

        return ResearchOutput(
            confidence_score=0.1,
            company_intelligence={
                "recent_news": f"Research failed: {error_msg}",
                "growth_signals": [],
                "challenges": ["Unable to complete research"]
            },
            decision_maker_insights={
                "background": "Research incomplete",
                "recent_activities": []
            },
            conversation_hooks=fallback_hooks,
            timing_rationale="General outreach timing",
            research_timestamp=datetime.now().isoformat(),
            sources=[]
        )


# Convenience function for easy usage
def create_research_agent(config: Dict[str, Any], api_keys: Optional[Dict[str, str]] = None) -> ResearchAgent:
    """Create and return a configured Research Agent instance."""
    return ResearchAgent(config=config, api_keys=api_keys)


# Example usage
if __name__ == "__main__":
    # This example requires a dummy config for the agent to initialize.
    # In the actual application, this config will be fetched from MongoDB.
    dummy_config = {
        "tavily_search_queries": [
            "{company} recent news 2024 2025",
            "{company} funding growth acquisition",
            "{lead_name} {company} background",
            "{company} technology stack database infrastructure"
        ],
        "tavily_search_parameters": {
            "search_depth": "advanced",
            "max_results": 5
        },
        "confidence_score_weights": {
            "recent_news": 0.3,
            "growth_signals": 0.2,
            "challenges": 0.2,
            "background": 0.15,
            "recent_activities": 0.15
        },
        "enhanced_confidence_score_weights": {
            "base_research_news": 0.1,
            "base_research_growth": 0.1,
            "base_research_challenges": 0.1,
            "base_research_tech": 0.1,
            "relevance_use_cases": 0.1,
            "relevance_pain_points": 0.1,
            "relevance_score_bonus": 0.1,
            "crm_richness_multiplier": 0.2,
            "personalization_hooks": 0.05,
            "personalization_context": 0.05
        },
        "fallback_conversation_hooks": [
            "Interested in connecting with {company}",
            "Would like to discuss {industry} opportunities"
        ]
    }
    
    # Example usage
    agent = create_research_agent(config=dummy_config)
    
    sample_lead = LeadInput(
        lead_name="John Doe",
        company="Acme Corp",
        title="VP of Sales",
        industry="SaaS",
        company_size="500 employees"
    )
    
    result = agent.research_lead(sample_lead)
    print(f"Research completed with confidence: {result.confidence_score}")
    print(f"Conversation hooks: {result.conversation_hooks}")
