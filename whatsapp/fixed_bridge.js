/**
 * Fixed WhatsApp Bridge - Uses the EXACT configuration that works in simple_test.js
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const cors = require('cors');

console.log('🚀 Starting Fixed WhatsApp Bridge...');

// Global state
let client = null;
let isReady = false;
let isAuthenticated = false;
let clientInfo = null;

// Express app for API endpoints
const app = express();
app.use(cors());
app.use(express.json());

// Initialize WhatsApp client with EXACT working configuration from simple_test.js
function initializeWhatsApp() {
    console.log('🔧 Initializing WhatsApp with PROVEN working configuration...');

    // Use the EXACT same configuration that worked in simple_test.js
    client = new Client({
        authStrategy: new LocalAuth(),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        }
    });

    // QR Code event - EXACT same as working test
    client.on('qr', (qr) => {
        console.log('\n🎉 QR CODE GENERATED SUCCESSFULLY!');
        console.log('='.repeat(60));
        qrcode.generate(qr, { small: true });
        console.log('='.repeat(60));
        console.log('👆 Scan this QR code with WhatsApp on your phone');
        console.log('📱 Go to WhatsApp > Settings > Linked Devices > Link a Device');
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

    // Error handling
    client.on('error', (error) => {
        console.error('❌ WhatsApp client error:', error);
    });

    // Message handling
    client.on('message', async msg => {
        console.log(`📨 Message from ${msg.from}: ${msg.body}`);
        
        if (msg.body === '!test') {
            await msg.reply('🤖 Agno Sales Agent is working perfectly! ✅');
            console.log('✅ Replied to test message');
        }
    });

    // Initialize the client - EXACT same as working test
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

    const { phoneNumber, chatId, message } = req.body;
    const targetNumber = phoneNumber || chatId;

    if (!targetNumber || !message) {
        return res.status(400).json({
            success: false,
            error: 'phoneNumber (or chatId) and message are required'
        });
    }

    try {
        // Format phone number
        let formattedNumber;
        if (targetNumber.includes('@c.us')) {
            formattedNumber = targetNumber;
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
    console.log(`🌐 Fixed WhatsApp Bridge running on http://localhost:${PORT}`);
    console.log('📱 Ready to connect WhatsApp using PROVEN working method');
    
    // Auto-initialize WhatsApp
    setTimeout(() => {
        console.log('🔄 Auto-initializing WhatsApp...');
        initializeWhatsApp();
    }, 1000);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down Fixed WhatsApp Bridge...');
    if (client) {
        await client.destroy();
    }
    process.exit(0);
});
