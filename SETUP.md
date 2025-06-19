# 🚀 Quick Setup Guide

## Prerequisites
- Python 3.11+
- Node.js 16+
- MongoDB Atlas account
- Chrome browser

## API Keys Required
- Monday.com API token
- Tavily API key  
- Google Gemini API key
- MongoDB Atlas connection string

## Installation Steps

### 1. Install Agno Framework
```bash
cd ../libs/agno
pip install -e .
```

### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Install WhatsApp Dependencies
```bash
cd whatsapp
npm install
```

### 4. Environment Configuration
Create `.env` file in project root:
```bash
MONGODB_CONNECTION_STRING=mongodb+srv://your-atlas-connection
MONDAY_API_TOKEN=your_monday_token
TAVILY_API_KEY=your_tavily_key
GEMINI_API_KEY=your_gemini_key
```

### 5. Verify Setup
```bash
python verify_mongodb_single_source_truth.py
```

## Start Servers

### Backend Server
```bash
cd backend
python main.py
```
Server runs on http://localhost:8000

### WhatsApp Bridge
```bash
cd whatsapp
node working_bridge.js
```
Bridge runs on http://localhost:3001
Scan QR code when prompted

### Chrome Extension
1. Open Chrome → Extensions → Developer mode
2. Click "Load unpacked"
3. Select `extension/` folder
4. Navigate to Monday.com and test

## Testing
1. Go to Monday.com board with leads
2. Click "Process Lead" button
3. Watch MongoDB Single Source of Truth workflow!

## Troubleshooting
- Ensure all API keys are valid
- Check MongoDB Atlas connection
- Verify WhatsApp QR code scanning
- Check browser console for extension errors
