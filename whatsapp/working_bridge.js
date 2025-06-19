/**
 * Working WhatsApp Bridge - Connects the proven terminal QR client to the backend
 * This uses the ONLY method that works: terminal QR code
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const cors = require('cors');

console.log('🚀 Starting Working WhatsApp Bridge...');

// Global state
let client = null;
let isReady = false;
let isAuthenticated = false;
let clientInfo = null;

// Express app for API endpoints
const app = express();
app.use(cors());
app.use(express.json());

// Initialize WhatsApp client with WORKING configuration
function initializeWhatsApp() {
    console.log('🔧 Initializing WhatsApp with WORKING configuration...');

    // Clean up any existing session that might be corrupted
    const sessionPath = process.env.WHATSAPP_SESSION_PATH || './whatsapp/.wwebjs_auth';
    console.log(`📁 Using session path: ${sessionPath}`);

    client = new Client({
        authStrategy: new LocalAuth({
            dataPath: sessionPath
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        }
    });

    // QR Code event - WORKING method
    client.on('qr', (qr) => {
        console.log('\n📱 QR Code received! Scan with your phone:');
        console.log('='.repeat(60));
        qrcode.generate(qr, { small: true });
        console.log('='.repeat(60));
        console.log('👆 Scan this QR code with WhatsApp on your phone');
        console.log('📱 Go to WhatsApp > Settings > Linked Devices > Link a Device');
        console.log('');
    });

    // Authentication events
    client.on('authenticated', () => {
        console.log('✅ WhatsApp authenticated successfully!');
        isAuthenticated = true;
    });

    client.on('auth_failure', msg => {
        console.error('❌ Authentication failed:', msg);
        isAuthenticated = false;
    });

    client.on('loading_screen', (percent, message) => {
        console.log('🔄 LOADING SCREEN', percent, message);
    });

    // Ready event
    client.on('ready', async () => {
        console.log('🎉 WhatsApp client is ready!');

        // Add page error handlers for debugging
        if (client.pupPage) {
            client.pupPage.on('pageerror', function(err) {
                console.error('❌ Page error:', err.toString());
            });
            client.pupPage.on('error', function(err) {
                console.error('❌ Page error:', err.toString());
            });
        }
        
        isReady = true;
        
        try {
            clientInfo = client.info;
            console.log(`📱 Connected as: ${clientInfo.pushname}`);
            console.log(`📞 Phone number: ${clientInfo.wid.user}`);
            console.log(`🔗 Platform: ${clientInfo.platform}`);
            
            // Send test message to yourself
            const myNumber = clientInfo.wid.user + '@c.us';
            await client.sendMessage(myNumber, '🤖 Agno Sales Agent WhatsApp Bridge is ready! ✅');
            console.log('✅ Test message sent to yourself!');
            
        } catch (error) {
            console.error('❌ Error getting client info:', error);
        }
    });

    // Disconnection event
    client.on('disconnected', (reason) => {
        console.log('📱 WhatsApp disconnected:', reason);
        isReady = false;
        isAuthenticated = false;
        clientInfo = null;
    });

    // Message handling
    client.on('message', async msg => {
        console.log(`📨 Message from ${msg.from}: ${msg.body}`);
        
        if (msg.body === '!test') {
            await msg.reply('🤖 Agno Sales Agent is working perfectly! ✅');
            console.log('✅ Replied to test message');
        }
    });

    // Initialize the client
    console.log('🔄 Initializing WhatsApp client...');
    client.initialize().catch(error => {
        console.error('❌ Failed to initialize WhatsApp client:', error);
        client = null;
        isReady = false;
        isAuthenticated = false;
    });
}

// API Endpoints for backend integration
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        whatsapp_ready: isReady,
        whatsapp_authenticated: isAuthenticated,
        timestamp: new Date().toISOString()
    });
});

app.get('/get-status', (req, res) => {
    console.log('📱 Status request received');
    res.json({
        success: true,
        status: {
            isReady: isReady,
            isAuthenticated: isAuthenticated,
            hasClient: !!client,
            clientInfo: clientInfo
        }
    });
});

app.post('/send-message', async (req, res) => {
    console.log('📤 Send message request received:', req.body);

    if (!isReady || !client) {
        return res.status(400).json({
            success: false,
            error: 'WhatsApp client is not ready'
        });
    }

    // Support both phoneNumber and chatId parameters
    const { phoneNumber, chatId, message, type = 'text' } = req.body;
    const targetNumber = phoneNumber || chatId;

    if (!targetNumber || !message) {
        return res.status(400).json({
            success: false,
            error: 'phoneNumber (or chatId) and message are required'
        });
    }

    try {
        // Format phone number (remove + and add @c.us if not already formatted)
        let formattedNumber;
        if (targetNumber.includes('@c.us')) {
            formattedNumber = targetNumber; // Already formatted
        } else {
            formattedNumber = targetNumber.replace(/[^\d]/g, '') + '@c.us';
        }
        
        console.log(`📤 Sending message to ${formattedNumber}: ${message}`);
        const result = await client.sendMessage(formattedNumber, message);
        
        console.log('✅ Message sent successfully');
        res.json({
            success: true,
            messageId: result.id._serialized,
            timestamp: result.timestamp,
            to: formattedNumber
        });
        
    } catch (error) {
        console.error('❌ Failed to send message:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.post('/connect', (req, res) => {
    if (!client) {
        initializeWhatsApp();
        res.json({
            success: true,
            message: 'WhatsApp initialization started. Check console for QR code.'
        });
    } else {
        res.json({
            success: true,
            message: 'WhatsApp client already initialized',
            ready: isReady
        });
    }
});

// Start the server
const PORT = 3001;
app.listen(PORT, () => {
    console.log(`🌐 Working WhatsApp Bridge running on http://localhost:${PORT}`);
    console.log('📱 Ready to connect WhatsApp using terminal QR method');
    
    // Auto-initialize WhatsApp
    setTimeout(() => {
        console.log('🔄 Auto-initializing WhatsApp...');
        initializeWhatsApp();
    }, 1000);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down Working WhatsApp Bridge...');
    if (client) {
        await client.destroy();
    }
    process.exit(0);
});
