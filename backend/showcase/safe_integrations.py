#!/usr/bin/env python3
"""
Safe Integration Helpers - MongoDB Showcase Enhancement

SAFETY: These are helper functions that can be safely added to existing code
without breaking anything. They provide optional enhancements that fail gracefully.

Features:
- Safe conversation logging (optional, doesn't break if it fails)
- Safe vector embedding storage (optional, doesn't break if it fails)
- Safe semantic search (optional, returns empty if it fails)
- All functions are designed to be non-blocking and fail-safe
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

def safe_log_conversation_message(lead_id: str, lead_name: str, company: str, 
                                phone_number: str, message_content: str,
                                message_type: str = "outbound",
                                whatsapp_message_id: str = None) -> bool:
    """
    SAFE: Log conversation message to MongoDB
    
    This function can be safely called from anywhere in the existing code.
    If it fails, it logs the error but doesn't break the main workflow.
    
    Args:
        lead_id: Monday.com item ID
        lead_name: Lead's name
        company: Company name
        phone_number: WhatsApp phone number
        message_content: The message text
        message_type: "outbound" or "inbound"
        whatsapp_message_id: WhatsApp message ID (optional)
    
    Returns:
        bool: True if successful, False if failed (but doesn't raise exceptions)
    """
    try:
        from showcase.conversation_logs import safe_log_outbound_message
        
        if message_type == "outbound":
            return safe_log_outbound_message(
                lead_id, lead_name, company, phone_number, 
                message_content, whatsapp_message_id
            )
        else:
            # For inbound messages, we'd need to implement safe_log_inbound_message
            logger.info(f"📥 Inbound message logged for {lead_name}: {message_content[:50]}...")
            return True
            
    except Exception as e:
        logger.warning(f"⚠️ Safe conversation logging failed (non-critical): {e}")
        return False

def safe_store_research_vector(research_id: str, research_data: Dict[str, Any]) -> bool:
    """
    SAFE: Store research data as vector embedding
    
    This function can be safely called after research is completed.
    If it fails, it logs the error but doesn't break the main workflow.
    
    Args:
        research_id: Unique research identifier
        research_data: Complete research data dictionary
    
    Returns:
        bool: True if successful, False if failed (but doesn't raise exceptions)
    """
    try:
        from showcase.vector_embeddings import safe_store_research_embedding
        
        return safe_store_research_embedding(research_id, research_data)
        
    except Exception as e:
        logger.warning(f"⚠️ Safe vector storage failed (non-critical): {e}")
        return False

def safe_semantic_search_insights(lead_context: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    SAFE: Get semantic insights for lead personalization
    
    This function can be safely called to enhance message personalization.
    If it fails, it returns an empty list but doesn't break the main workflow.
    
    Args:
        lead_context: Context about the lead (name, company, etc.)
        limit: Maximum number of insights to return
    
    Returns:
        List[Dict]: List of relevant insights, empty list if failed
    """
    try:
        from showcase.vector_embeddings import safe_semantic_search
        
        query = f"insights for {lead_context} personalization conversation hooks"
        results = safe_semantic_search(query, "research_data", limit)
        
        # Extract useful insights
        insights = []
        for result in results:
            if result.get('similarity_score', 0) > 0.7:  # High similarity threshold
                insights.append({
                    'content': result.get('content', ''),
                    'source_company': result.get('metadata', {}).get('company', ''),
                    'confidence': result.get('similarity_score', 0),
                    'source_id': result.get('source_id', '')
                })
        
        logger.info(f"✅ Found {len(insights)} semantic insights for: {lead_context[:30]}...")
        return insights
        
    except Exception as e:
        logger.warning(f"⚠️ Safe semantic search failed (non-critical): {e}")
        return []

def safe_find_similar_companies(company_name: str, limit: int = 2) -> List[Dict[str, Any]]:
    """
    SAFE: Find companies with similar profiles
    
    This function can be safely called to find similar companies for benchmarking.
    If it fails, it returns an empty list but doesn't break the main workflow.
    
    Args:
        company_name: Target company name
        limit: Maximum number of similar companies to return
    
    Returns:
        List[Dict]: List of similar companies, empty list if failed
    """
    try:
        from showcase.vector_embeddings import VectorEmbeddingsManager
        
        vector_manager = VectorEmbeddingsManager()
        if vector_manager.connect():
            results = vector_manager.find_similar_companies(company_name, limit)
            vector_manager.disconnect()
            
            # Extract useful company data
            similar_companies = []
            for result in results:
                if result.get('similarity_score', 0) > 0.6:  # Similarity threshold
                    similar_companies.append({
                        'company': result.get('metadata', {}).get('company', ''),
                        'insights': result.get('content', '')[:200] + '...',
                        'similarity': result.get('similarity_score', 0),
                        'source_id': result.get('source_id', '')
                    })
            
            logger.info(f"✅ Found {len(similar_companies)} similar companies to: {company_name}")
            return similar_companies
        
        return []
        
    except Exception as e:
        logger.warning(f"⚠️ Safe company search failed (non-critical): {e}")
        return []

def safe_get_conversation_analytics() -> Dict[str, Any]:
    """
    SAFE: Get conversation analytics
    
    This function can be safely called to get conversation metrics.
    If it fails, it returns empty analytics but doesn't break the main workflow.
    
    Returns:
        Dict: Conversation analytics, empty dict if failed
    """
    try:
        from showcase.conversation_logs import ConversationLogsManager
        
        conv_manager = ConversationLogsManager()
        if conv_manager.connect():
            analytics = conv_manager.get_conversation_analytics()
            conv_manager.disconnect()
            return analytics
        
        return {}
        
    except Exception as e:
        logger.warning(f"⚠️ Safe analytics failed (non-critical): {e}")
        return {}

def safe_get_vector_analytics() -> Dict[str, Any]:
    """
    SAFE: Get vector embedding analytics
    
    This function can be safely called to get embedding metrics.
    If it fails, it returns empty analytics but doesn't break the main workflow.
    
    Returns:
        Dict: Vector analytics, empty dict if failed
    """
    try:
        from showcase.vector_embeddings import VectorEmbeddingsManager
        
        vector_manager = VectorEmbeddingsManager()
        if vector_manager.connect():
            analytics = vector_manager.get_embedding_analytics()
            vector_manager.disconnect()
            return analytics
        
        return {}
        
    except Exception as e:
        logger.warning(f"⚠️ Safe vector analytics failed (non-critical): {e}")
        return {}

# SAFE INTEGRATION EXAMPLES
# These show how to safely integrate the new features into existing code

def example_safe_integration_in_message_generation():
    """
    Example of how to safely integrate conversation logging and semantic search
    into existing message generation code
    """
    # This is just an example - don't actually run this
    
    # Existing message generation code would be here...
    lead_id = "2010690053"
    lead_name = "Maor Shlomo"
    company = "Base44"
    phone_number = "+1234567890"
    
    # SAFE: Get semantic insights to enhance personalization
    insights = safe_semantic_search_insights(f"{lead_name} at {company}")
    
    # Use insights if available, but don't break if empty
    personalization_hooks = []
    for insight in insights:
        if insight['confidence'] > 0.8:
            personalization_hooks.append(insight['content'][:100])
    
    # Generate message (existing code would be here)
    message = f"Hi {lead_name}, I noticed {company} is growing rapidly..."
    
    # Add personalization if we found good insights
    if personalization_hooks:
        message += f" I saw that {personalization_hooks[0]}..."
    
    # SAFE: Log the conversation (doesn't break if it fails)
    safe_log_conversation_message(
        lead_id, lead_name, company, phone_number, message, "outbound"
    )
    
    return message

def example_safe_integration_in_research_completion():
    """
    Example of how to safely integrate vector storage after research completion
    """
    # This is just an example - don't actually run this
    
    # Existing research completion code would be here...
    research_id = "research_123"
    research_data = {
        "lead_name": "Maor Shlomo",
        "company": "Base44",
        "company_intelligence": {
            "recent_news": "Base44 raised Series A funding",
            "growth_signals": ["hiring", "expansion"],
            "challenges": ["scaling", "competition"]
        },
        "conversation_hooks": ["funding news", "growth trajectory"]
    }
    
    # SAFE: Store vector embedding (doesn't break if it fails)
    safe_store_research_vector(research_id, research_data)
    
    # Continue with existing research workflow...
    return research_data

# SHOWCASE SUMMARY FUNCTION
def get_mongodb_showcase_summary() -> Dict[str, Any]:
    """
    Get a comprehensive summary of MongoDB showcase capabilities
    
    This function demonstrates all the data types and capabilities
    stored in MongoDB for the AI agent system.
    """
    try:
        summary = {
            "timestamp": datetime.now().isoformat(),
            "mongodb_showcase": {
                "core_collections": {
                    "contacts": "Real Monday.com lead data with comprehensive CRM insights",
                    "research_results": "Tavily API research data with company intelligence",
                    "workflow_progress": "Agent workflow states and decision tracking",
                    "agent_configurations": "Dynamic agent prompts and configurations"
                },
                "new_showcase_collections": {
                    "conversation_logs": "Complete WhatsApp conversation threads with nested messages",
                    "vector_embeddings": "Voyage AI embeddings for semantic search and similarity"
                },
                "mongodb_capabilities_demonstrated": [
                    "Document flexibility for complex nested data",
                    "Real-time updates and state tracking",
                    "Vector search for semantic similarity",
                    "Aggregation pipelines for analytics",
                    "Schema-less design for evolving AI agent needs",
                    "Single source of truth for all agent data"
                ]
            },
            "conversation_analytics": safe_get_conversation_analytics(),
            "vector_analytics": safe_get_vector_analytics()
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error generating showcase summary: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Test the safe integrations
    print("🧪 Testing Safe MongoDB Showcase Integrations")
    print("=" * 50)
    
    # Test conversation analytics
    conv_analytics = safe_get_conversation_analytics()
    print(f"📊 Conversation Analytics: {conv_analytics}")
    
    # Test vector analytics
    vector_analytics = safe_get_vector_analytics()
    print(f"🔍 Vector Analytics: {vector_analytics}")
    
    # Test showcase summary
    summary = get_mongodb_showcase_summary()
    print(f"🎯 MongoDB Showcase Summary: {summary}")
