"""
Monday.com Board Configuration
Documents the actual board structure and column mappings
"""

# Actual Monday.com Board Configuration
MONDAY_BOARD_CONFIG = {
    "board_id": "2001047343",
    "board_name": "Leads",
    "columns": {
        # Core identification
        "name": "name",                           # Lead Name (built-in)
        "lead_company": "lead_company",           # Company (text)
        "lead_email": "lead_email",               # Email (email)
        "lead_phone": "lead_phone",               # Phone (phone)
        "text": "text",                           # Title (text)
        
        # Status tracking
        "lead_status": "lead_status",             # Status (status)
        
        # Dates
        "date__1": "date__1",                     # Last interaction (date)
        
        # System columns
        "subtasks_mkrysmpk": "subtasks_mkrysmpk", # Subitems
        "button": "button",                       # Create contact button
        "enrolled_sequences_mkn3bg52": "enrolled_sequences_mkn3bg52"  # Active sequences
    }
}

# Column mapping for our agent system
AGENT_COLUMN_MAPPING = {
    # Our field name -> Monday.com column ID
    "name": "name",
    "company": "lead_company", 
    "email": "lead_email",
    "phone": "lead_phone",
    "title": "text",
    "status": "lead_status",
    "last_contact": "date__1"
}

# Reverse mapping for parsing Monday.com data
MONDAY_TO_AGENT_MAPPING = {v: k for k, v in AGENT_COLUMN_MAPPING.items()}

# Sample leads created for testing
SAMPLE_LEADS = [
    {
        "name": "John Smith - TechCorp",
        "company": "TechCorp Solutions",
        "email": "john.smith@techcorp.com",
        "phone": "+1-555-0101",
        "title": "VP of Engineering"
    },
    {
        "name": "Sarah Johnson - DataFlow",
        "company": "DataFlow Analytics", 
        "email": "sarah.j@dataflow.io",
        "phone": "+1-555-0102",
        "title": "Chief Technology Officer"
    },
    {
        "name": "Michael Chen - CloudScale",
        "company": "CloudScale Systems",
        "email": "m.chen@cloudscale.com",
        "phone": "+1-555-0103", 
        "title": "Head of Product"
    },
    {
        "name": "Emily Rodriguez - AI Ventures",
        "company": "AI Ventures Inc",
        "email": "emily.r@aiventures.com",
        "phone": "+1-555-0104",
        "title": "Director of Innovation"
    },
    {
        "name": "David Kim - SecureNet",
        "company": "SecureNet Technologies",
        "email": "david.kim@securenet.com",
        "phone": "+1-555-0105",
        "title": "Security Architect"
    },
    {
        "name": "Lisa Wang - GrowthLab",
        "company": "GrowthLab Marketing",
        "email": "lisa.wang@growthlab.com", 
        "phone": "+1-555-0106",
        "title": "Marketing Director"
    },
    {
        "name": "Robert Taylor - FinTech Pro",
        "company": "FinTech Pro Solutions",
        "email": "r.taylor@fintechpro.com",
        "phone": "+1-555-0107",
        "title": "Product Manager"
    },
    {
        "name": "Amanda Foster - HealthTech",
        "company": "HealthTech Innovations",
        "email": "amanda.f@healthtech.com",
        "phone": "+1-555-0108", 
        "title": "VP of Operations"
    },
    {
        "name": "James Wilson - EduPlatform",
        "company": "EduPlatform Solutions",
        "email": "james.w@eduplatform.com",
        "phone": "+1-555-0109",
        "title": "Chief Learning Officer"
    },
    {
        "name": "Maria Garcia - GreenEnergy",
        "company": "GreenEnergy Systems",
        "email": "maria.g@greenenergy.com",
        "phone": "+1-555-0110",
        "title": "Sustainability Director"
    }
]

def get_board_config():
    """Get the Monday.com board configuration"""
    return MONDAY_BOARD_CONFIG

def get_column_mapping():
    """Get the column mapping for agent operations"""
    return AGENT_COLUMN_MAPPING

def get_sample_leads():
    """Get the sample leads data"""
    return SAMPLE_LEADS
