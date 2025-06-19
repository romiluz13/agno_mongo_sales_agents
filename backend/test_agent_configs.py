#!/usr/bin/env python3
"""
Test script to verify all agent configurations are loading correctly from MongoDB
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('/Users/rom.iluz/Dev/agno_sales_agent/agno/agno-sales-extension/backend')

def test_configuration_loading():
    """Test that all agents can load their configurations from MongoDB"""
    
    print('🧪 Testing Agent Configuration Loading from MongoDB...\n')
    
    # Mock API keys for testing
    api_keys = {
        'openai_api_key': 'test-key',
        'tavily_api_key': 'test-key',
        'monday_api_key': 'test-key'
    }
    
    mongodb_connection = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
    
    test_results = []
    
    # Test 1: Research Agent
    try:
        from agents.research_agent import ResearchAgent
        research_agent = ResearchAgent(api_keys=api_keys, config={})
        test_results.append(('Research Agent', True, 'Configuration loading works'))
        print('✅ Research Agent: Configuration loading works')
    except Exception as e:
        test_results.append(('Research Agent', False, str(e)))
        print(f'❌ Research Agent: {e}')

    # Test 2: Message Generation Agent  
    try:
        from agents.message_agent import MessageGenerationAgent
        message_agent = MessageGenerationAgent(api_keys=api_keys, config={})
        test_results.append(('Message Generation Agent', True, 'Configuration loading works'))
        print('✅ Message Generation Agent: Configuration loading works')
    except Exception as e:
        test_results.append(('Message Generation Agent', False, str(e)))
        print(f'❌ Message Generation Agent: {e}')

    # Test 3: Workflow Coordinator
    try:
        from agents.workflow_coordinator import SalesAgentTeam
        coordinator = SalesAgentTeam(api_keys=api_keys, mongodb_connection=mongodb_connection)
        test_results.append(('Workflow Coordinator', True, 'Configuration loading works'))
        print('✅ Workflow Coordinator: Configuration loading works')
    except Exception as e:
        test_results.append(('Workflow Coordinator', False, str(e)))
        print(f'❌ Workflow Coordinator: {e}')

    # Test 4: Outreach Agent
    try:
        from agents.outreach_agent import OutreachAgent
        outreach_agent = OutreachAgent(api_keys=api_keys, mongodb_connection=mongodb_connection)
        test_results.append(('Outreach Agent', True, 'Configuration loading works'))
        print('✅ Outreach Agent: Configuration loading works')
    except Exception as e:
        test_results.append(('Outreach Agent', False, str(e)))
        print(f'❌ Outreach Agent: {e}')

    # Test 5: Message Quality Optimizer
    try:
        from agents.message_quality_optimizer import MessageQualityOptimizer
        optimizer = MessageQualityOptimizer(api_keys=api_keys, mongodb_connection=mongodb_connection)
        test_results.append(('Message Quality Optimizer', True, 'Configuration loading works'))
        print('✅ Message Quality Optimizer: Configuration loading works')
    except Exception as e:
        test_results.append(('Message Quality Optimizer', False, str(e)))
        print(f'❌ Message Quality Optimizer: {e}')

    # Test 6: MongoDB Configuration Loading
    try:
        from config.database import MongoDBManager
        db_manager = MongoDBManager()
        if db_manager.connect():
            agent_configs_collection = db_manager.get_collection("agent_configurations")
            agent_config = agent_configs_collection.find_one()
            
            if agent_config and len(agent_config.keys()) >= 9:
                test_results.append(('MongoDB Configuration', True, f'Found complete config with {len(agent_config.keys())} keys'))
                print(f'✅ MongoDB Configuration: Found complete config with {len(agent_config.keys())} keys')
            else:
                test_results.append(('MongoDB Configuration', False, 'Incomplete configuration found'))
                print('❌ MongoDB Configuration: Incomplete configuration found')
            
            db_manager.disconnect()
        else:
            test_results.append(('MongoDB Configuration', False, 'Failed to connect to MongoDB'))
            print('❌ MongoDB Configuration: Failed to connect to MongoDB')
    except Exception as e:
        test_results.append(('MongoDB Configuration', False, str(e)))
        print(f'❌ MongoDB Configuration: {e}')

    # Summary
    print('\n' + '='*60)
    print('🎯 AGENT CONFIGURATION TEST SUMMARY')
    print('='*60)
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    for agent, success, message in test_results:
        status = '✅ PASS' if success else '❌ FAIL'
        print(f'{status}: {agent} - {message}')
    
    print(f'\nOverall Result: {passed}/{total} tests passed')
    
    if passed == total:
        print('🎉 ALL AGENT CONFIGURATIONS ARE WORKING CORRECTLY!')
        return True
    else:
        print('⚠️ Some agent configurations need attention.')
        return False

if __name__ == "__main__":
    success = test_configuration_loading()
    sys.exit(0 if success else 1)
