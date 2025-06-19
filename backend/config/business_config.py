"""
Business Configuration System for Agno Sales Agent
=================================================

This module provides configurable business context for the sales agent system.
Designed to be easily customizable for different businesses while showcasing MongoDB capabilities.

Task 11.7: Business Context Configuration
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

logger = logging.getLogger(__name__)


@dataclass
class BusinessOwner:
    """Business owner information"""
    name: str
    title: str
    email: str
    linkedin: str
    background: str
    expertise: str


@dataclass
class CompanyInfo:
    """Company information"""
    name: str
    website: str
    description: str
    industry: str
    size: str
    founded: str
    location: str


@dataclass
class ServiceOffering:
    """Individual service offering"""
    name: str
    description: str
    price: str
    duration: str
    deliverables: list
    target_audience: str


@dataclass
class ValueProposition:
    """Value proposition for different scenarios"""
    primary: str
    ai_applications: str
    scaling: str
    real_time: str
    cost_savings: str
    performance: str


@dataclass
class MongoDBExpertise:
    """MongoDB-specific expertise and capabilities"""
    certifications: list
    experience_years: int
    specializations: list
    case_studies: list
    technologies: list


@dataclass
class BusinessConfiguration:
    """Complete business configuration"""
    owner: BusinessOwner
    company: CompanyInfo
    services: Dict[str, ServiceOffering]
    value_propositions: ValueProposition
    mongodb_expertise: MongoDBExpertise
    contact_preferences: Dict[str, Any]
    customization_notes: str


class BusinessConfigManager:
    """Manages business configuration with environment variable support"""
    
    def __init__(self):
        self.config = self._load_configuration()
        logger.info(f"Business configuration loaded for: {self.config.company.name}")
    
    def _load_configuration(self) -> BusinessConfiguration:
        """Load business configuration from environment variables and defaults"""
        
        # Business Owner Configuration
        owner = BusinessOwner(
            name=os.getenv("BUSINESS_OWNER_NAME", "Rom Iluz"),
            title=os.getenv("BUSINESS_OWNER_TITLE", "MongoDB Solutions Expert"),
            email=os.getenv("BUSINESS_OWNER_EMAIL", "rom@iluz.net"),
            linkedin=os.getenv("BUSINESS_OWNER_LINKEDIN", "https://linkedin.com/in/romiluz"),
            background=os.getenv("BUSINESS_OWNER_BACKGROUND", "MongoDB employee with deep technical knowledge and hands-on experience building AI applications"),
            expertise=os.getenv("BUSINESS_OWNER_EXPERTISE", "MongoDB implementation, AI agent development, database optimization, vector search, real-time analytics")
        )
        
        # Company Information
        company = CompanyInfo(
            name=os.getenv("COMPANY_NAME", "MongoDB Solutions by Rom"),
            website=os.getenv("COMPANY_WEBSITE", "https://mongodb-solutions.com"),
            description=os.getenv("COMPANY_DESCRIPTION", "Specialized MongoDB consulting and AI application development services"),
            industry=os.getenv("COMPANY_INDUSTRY", "Database Technology & AI Solutions"),
            size=os.getenv("COMPANY_SIZE", "Boutique Consulting"),
            founded=os.getenv("COMPANY_FOUNDED", "2024"),
            location=os.getenv("COMPANY_LOCATION", "Global (Remote)")
        )
        
        # Service Offerings
        services = {
            "mongodb_setup": ServiceOffering(
                name="MongoDB Implementation & Setup",
                description="Complete MongoDB setup, configuration, and optimization for production environments",
                price=os.getenv("SERVICE_MONGODB_SETUP_PRICE", "$5,000 setup fee"),
                duration="2-4 weeks",
                deliverables=[
                    "Production-ready MongoDB cluster",
                    "Security configuration",
                    "Performance optimization",
                    "Backup and monitoring setup",
                    "Documentation and training"
                ],
                target_audience="Companies migrating to MongoDB or scaling existing deployments"
            ),
            "ai_development": ServiceOffering(
                name="AI Application Development",
                description="Custom AI applications using MongoDB Atlas Vector Search and modern AI frameworks",
                price=os.getenv("SERVICE_AI_DEVELOPMENT_PRICE", "Custom pricing"),
                duration="4-12 weeks",
                deliverables=[
                    "AI-powered applications",
                    "Vector search implementation",
                    "RAG (Retrieval Augmented Generation) systems",
                    "Real-time AI analytics",
                    "Scalable AI infrastructure"
                ],
                target_audience="Companies building AI features or modernizing with AI capabilities"
            ),
            "consulting": ServiceOffering(
                name="MongoDB Consulting & Optimization",
                description="Expert consulting for MongoDB performance, architecture, and best practices",
                price=os.getenv("SERVICE_CONSULTING_PRICE", "$200/hour"),
                duration="Ongoing",
                deliverables=[
                    "Performance analysis and optimization",
                    "Architecture review and recommendations",
                    "Query optimization",
                    "Scaling strategy",
                    "Best practices implementation"
                ],
                target_audience="Teams using MongoDB who need expert guidance and optimization"
            )
        }
        
        # Value Propositions
        value_props = ValueProposition(
            primary=os.getenv("VALUE_PROP_PRIMARY", "Build AI applications 10x faster with MongoDB"),
            ai_applications="Leverage MongoDB Atlas Vector Search for intelligent, context-aware applications",
            scaling="Handle massive scale with MongoDB's horizontal scaling and sharding capabilities",
            real_time="Real-time analytics and operational intelligence with MongoDB's aggregation pipeline",
            cost_savings="Reduce infrastructure costs by 40% with MongoDB's efficient document model",
            performance="Achieve sub-millisecond query performance with proper MongoDB optimization"
        )
        
        # MongoDB Expertise
        mongodb_expertise = MongoDBExpertise(
            certifications=[
                "MongoDB Certified Developer",
                "MongoDB Certified DBA",
                "MongoDB Atlas Certified"
            ],
            experience_years=int(os.getenv("MONGODB_EXPERIENCE_YEARS", "5")),
            specializations=[
                "Vector Search & AI Applications",
                "Real-time Analytics",
                "Performance Optimization",
                "Scaling & Sharding",
                "Atlas Cloud Management"
            ],
            case_studies=[
                "Scaled AI startup from 1M to 100M documents",
                "Implemented vector search for e-commerce recommendation engine",
                "Optimized queries reducing response time by 90%",
                "Migrated legacy SQL database to MongoDB with zero downtime"
            ],
            technologies=[
                "MongoDB Atlas",
                "MongoDB Compass",
                "Aggregation Pipeline",
                "Vector Search",
                "Change Streams",
                "GridFS",
                "MongoDB Charts"
            ]
        )
        
        # Contact Preferences
        contact_preferences = {
            "preferred_method": os.getenv("CONTACT_PREFERRED_METHOD", "WhatsApp"),
            "response_time": os.getenv("CONTACT_RESPONSE_TIME", "Within 24 hours"),
            "availability": os.getenv("CONTACT_AVAILABILITY", "Monday-Friday, 9 AM - 6 PM UTC"),
            "languages": os.getenv("CONTACT_LANGUAGES", "English, Hebrew").split(", "),
            "time_zone": os.getenv("CONTACT_TIMEZONE", "UTC")
        }
        
        return BusinessConfiguration(
            owner=owner,
            company=company,
            services=services,
            value_propositions=value_props,
            mongodb_expertise=mongodb_expertise,
            contact_preferences=contact_preferences,
            customization_notes=os.getenv("CUSTOMIZATION_NOTES", "This configuration can be easily customized by updating environment variables in .env file")
        )
    
    def get_business_context(self) -> Dict[str, Any]:
        """Get business context for agent prompts"""
        return {
            "owner": asdict(self.config.owner),
            "company": asdict(self.config.company),
            "services": {k: asdict(v) for k, v in self.config.services.items()},
            "value_propositions": asdict(self.config.value_propositions),
            "mongodb_expertise": asdict(self.config.mongodb_expertise),
            "contact_preferences": self.config.contact_preferences
        }
    
    def get_agent_context_summary(self) -> Dict[str, str]:
        """Get condensed context for agent prompts"""
        return {
            "expert_name": self.config.owner.name,
            "expert_title": self.config.owner.title,
            "company_name": self.config.company.name,
            "primary_value_prop": self.config.value_propositions.primary,
            "key_services": f"{self.config.services['mongodb_setup'].price}, {self.config.services['consulting'].price}",
            "expertise_summary": self.config.owner.expertise,
            "experience_years": str(self.config.mongodb_expertise.experience_years),
            "specializations": ", ".join(self.config.mongodb_expertise.specializations[:3])
        }
    
    def get_service_details(self, service_key: str) -> Optional[ServiceOffering]:
        """Get specific service details"""
        return self.config.services.get(service_key)
    
    def get_value_proposition_for_context(self, context: str) -> str:
        """Get appropriate value proposition based on context"""
        context_lower = context.lower()
        
        if "ai" in context_lower or "ml" in context_lower or "vector" in context_lower:
            return self.config.value_propositions.ai_applications
        elif "scale" in context_lower or "growth" in context_lower:
            return self.config.value_propositions.scaling
        elif "real-time" in context_lower or "analytics" in context_lower:
            return self.config.value_propositions.real_time
        elif "cost" in context_lower or "budget" in context_lower:
            return self.config.value_propositions.cost_savings
        elif "performance" in context_lower or "speed" in context_lower:
            return self.config.value_propositions.performance
        else:
            return self.config.value_propositions.primary
    
    def export_configuration(self, file_path: str) -> bool:
        """Export configuration to JSON file for backup/sharing"""
        try:
            config_dict = asdict(self.config)
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            logger.info(f"Configuration exported to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate configuration completeness"""
        validation = {
            "owner_info_complete": bool(self.config.owner.name and self.config.owner.email),
            "company_info_complete": bool(self.config.company.name and self.config.company.description),
            "services_configured": len(self.config.services) >= 2,
            "value_props_defined": bool(self.config.value_propositions.primary),
            "mongodb_expertise_defined": len(self.config.mongodb_expertise.specializations) >= 3,
            "contact_preferences_set": bool(self.config.contact_preferences.get("preferred_method"))
        }
        
        all_valid = all(validation.values())
        logger.info(f"Configuration validation: {'PASSED' if all_valid else 'FAILED'}")
        
        return validation


# Global instance for easy access
business_config = BusinessConfigManager()


def get_business_config() -> BusinessConfigManager:
    """Get the global business configuration instance"""
    return business_config


def get_business_context() -> Dict[str, Any]:
    """Quick access to business context"""
    return business_config.get_business_context()


def get_agent_context() -> Dict[str, str]:
    """Quick access to agent context summary"""
    return business_config.get_agent_context_summary()


if __name__ == "__main__":
    # Test the business configuration
    print("🏢 BUSINESS CONFIGURATION TEST")
    print("=" * 50)
    
    config = get_business_config()
    
    print(f"✅ Business Owner: {config.config.owner.name}")
    print(f"✅ Company: {config.config.company.name}")
    print(f"✅ Services: {len(config.config.services)}")
    print(f"✅ MongoDB Experience: {config.config.mongodb_expertise.experience_years} years")
    
    # Validation
    validation = config.validate_configuration()
    print(f"\n📊 Configuration Validation:")
    for check, status in validation.items():
        print(f"   - {check}: {'✅' if status else '❌'}")
    
    # Export test
    if config.export_configuration("business_config_backup.json"):
        print(f"\n💾 Configuration exported successfully")
    
    print(f"\n🎯 Agent Context Summary:")
    agent_context = get_agent_context()
    for key, value in agent_context.items():
        print(f"   - {key}: {value}")
