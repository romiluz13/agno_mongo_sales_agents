#!/usr/bin/env python3
"""
Test script to verify the complete research-to-message-to-outreach pipeline
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('/Users/rom.iluz/Dev/agno_sales_agent/agno/agno-sales-extension/backend')

def test_full_pipeline():
    """Test the complete pipeline from research to message generation"""
    
    print('🚀 Testing Complete Research-to-Message Pipeline...\n')
    
    # Get real API keys (using correct uppercase names that agents expect)
    api_keys = {
        'GEMINI_API_KEY': os.getenv('GOOGLE_API_KEY'),  # Using Google API key for Gemini
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'MONDAY_API_KEY': os.getenv('MONDAY_API_TOKEN')
    }
    
    mongodb_connection = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
    
    # Verify API keys are present
    print('🔑 Checking API Keys:')
    for key, value in api_keys.items():
        status = '✅' if value and value != 'test-key' else '❌'
        masked_value = f"{value[:8]}..." if value and len(value) > 8 else 'Missing'
        print(f'  {status} {key}: {masked_value}')
    
    print('\n' + '='*60)
    print('🧪 TESTING COMPLETE PIPELINE')
    print('='*60)
    
    try:
        from agents.research_agent import ResearchAgent, LeadInput
        from agents.message_agent import MessageGenerationAgent, MessageInput, LeadData, ResearchInsights, SenderInfo
        from agents.workflow_coordinator import WorkflowCoordinator, WorkflowInput
        
        # Test data - using a real company for testing
        test_lead = LeadInput(
            lead_name='Sarah Johnson',
            company='MongoDB',
            title='VP Engineering',
            industry='Database Technology',
            company_size='5000+ employees'
        )
        
        print(f'🎯 Testing pipeline for: {test_lead.lead_name} at {test_lead.company}')
        
        # Step 1: Research Agent
        print('\n📊 Step 1: Research Agent')
        research_agent = ResearchAgent(api_keys=api_keys, config={})
        research_result = research_agent.research_lead(test_lead)
        
        if research_result:
            print(f'✅ Research completed with confidence: {research_result.confidence_score}')
            print(f'  📰 Company Intelligence: {len(str(research_result.company_intelligence))} chars')
            print(f'  🎯 Conversation Hooks: {len(research_result.conversation_hooks)}')
        else:
            print('❌ Research failed')
            return False
        
        # Step 2: Message Generation Agent
        print('\n💬 Step 2: Message Generation')
        message_agent = MessageGenerationAgent(api_keys=api_keys, config={})
        
        # Prepare message input
        message_input = MessageInput(
            lead_data=LeadData(
                name=test_lead.lead_name,
                company=test_lead.company,
                title=test_lead.title
            ),
            research_insights=ResearchInsights(
                recent_news=research_result.company_intelligence.get('recent_news', ''),
                conversation_hooks=research_result.conversation_hooks,
                timing_rationale=research_result.timing_rationale
            ),
            message_type="text",
            sender_info=SenderInfo(
                name='Rom Iluz',
                company='MongoDB',
                value_prop='MongoDB database solutions for AI-powered applications'
            )
        )
        
        message_result = message_agent.generate_message(message_input)
        
        if message_result and message_result.message_text:
            print(f'✅ Message generated successfully')
            print(f'  📝 Message length: {len(message_result.message_text)} characters')
            print(f'  📊 Quality score: {getattr(message_result, "quality_score", "N/A")}')
            print(f'  💬 Message preview: "{message_result.message_text[:100]}..."')
        else:
            print('❌ Message generation failed')
            return False
        
        # Step 3: Workflow Coordinator Test
        print('\n🔄 Step 3: Workflow Coordinator')
        coordinator = WorkflowCoordinator(api_keys=api_keys, mongodb_connection=mongodb_connection)

        # Test lead processing through coordinator
        workflow_input = WorkflowInput(
            lead_id='test-lead-123',
            lead_name=test_lead.lead_name,
            company=test_lead.company,
            title=test_lead.title,
            industry=test_lead.industry,
            company_size=test_lead.company_size,
            phone_number='+1234567890',
            message_type='text',
            sender_name='Rom Iluz',
            sender_company='MongoDB',
            value_proposition='MongoDB database solutions for AI-powered applications'
        )

        print('🔄 Processing lead through workflow coordinator...')
        coordinator_result = coordinator.execute_lead_processing_workflow(workflow_input)
        
        if coordinator_result and coordinator_result.success:
            print('✅ Workflow coordinator processed lead successfully')
            print(f'  📊 Final status: {coordinator_result.final_status.value}')
            print(f'  🎯 Research confidence: {coordinator_result.research_confidence}')
            print(f'  💬 Message personalization: {coordinator_result.message_personalization_score}')
            print(f'  📈 Predicted response rate: {coordinator_result.predicted_response_rate}')
            print(f'  📱 Outreach status: {coordinator_result.outreach_status}')
            print(f'  ⏱️ Execution time: {coordinator_result.execution_time_seconds:.2f}s')
        else:
            print('❌ Workflow coordinator failed')
            if coordinator_result:
                print(f'  Error: {coordinator_result.error_details}')
            return False
        
        print('\n' + '='*60)
        print('🎯 PIPELINE TEST SUMMARY')
        print('='*60)
        print('✅ Research Agent: Successfully fetched real data')
        print('✅ Message Generation: Successfully created personalized message')
        print('✅ Workflow Coordinator: Successfully processed lead end-to-end')
        print('\n🎉 COMPLETE PIPELINE IS WORKING CORRECTLY!')
        
        return True
        
    except Exception as e:
        print(f'❌ Pipeline test failed with error: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_mongodb_collections():
    """Test that all required MongoDB collections exist and are accessible"""
    
    print('\n' + '='*60)
    print('💾 TESTING MONGODB COLLECTIONS')
    print('='*60)
    
    try:
        from config.database import MongoDBManager
        
        db_manager = MongoDBManager()
        if db_manager.connect():
            print('✅ Connected to MongoDB successfully')
            
            # List all collections
            collections = list(db_manager.database.list_collection_names())
            print(f'📋 Available collections ({len(collections)}): {collections}')
            
            # Check required collections
            required_collections = [
                'agent_configurations',
                'research_results',
                'interaction_history',
                'workflow_progress',
                'message_queue',
                'leads'
            ]
            
            print('\n📊 Required Collections Status:')
            all_present = True
            for collection in required_collections:
                status = '✅' if collection in collections else '❌'
                print(f'  {status} {collection}')
                if collection not in collections:
                    all_present = False
            
            if all_present:
                print('\n🎉 All required MongoDB collections are present!')
            else:
                print('\n⚠️ Some required collections are missing')
            
            db_manager.disconnect()
            return all_present
        else:
            print('❌ Failed to connect to MongoDB')
            return False
            
    except Exception as e:
        print(f'❌ MongoDB collections test failed: {e}')
        return False

if __name__ == "__main__":
    print('🚀 Starting Full Pipeline Integration Tests...\n')
    
    # Test MongoDB collections first
    mongodb_success = test_mongodb_collections()
    
    # Test complete pipeline
    pipeline_success = test_full_pipeline()
    
    print('\n' + '='*60)
    print('🎯 FULL PIPELINE TEST SUMMARY')
    print('='*60)
    
    print(f'✅ MongoDB Collections: {"PASS" if mongodb_success else "FAIL"}')
    print(f'✅ Complete Pipeline: {"PASS" if pipeline_success else "FAIL"}')
    
    if mongodb_success and pipeline_success:
        print('\n🎉 ALL PIPELINE INTEGRATION TESTS PASSED!')
        print('✅ Your agent system is working correctly end-to-end')
        print('✅ Research → Message Generation → Workflow coordination all functional')
        sys.exit(0)
    else:
        print('\n⚠️ Some pipeline integration tests failed')
        sys.exit(1)
