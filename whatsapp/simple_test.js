/**
 * Simple WhatsApp Web.js test to debug the QR code issue
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

console.log('🧪 Testing WhatsApp Web.js with minimal configuration...');

// Create client with minimal configuration
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
    }
});

// QR Code event
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
});

client.on('auth_failure', msg => {
    console.error('❌ Authentication failed:', msg);
});

client.on('ready', () => {
    console.log('🎉 WhatsApp client is ready!');
    console.log('✅ Test completed successfully!');
    process.exit(0);
});

client.on('disconnected', (reason) => {
    console.log('📱 WhatsApp disconnected:', reason);
});

// Error handling
client.on('error', (error) => {
    console.error('❌ WhatsApp client error:', error);
});

// Initialize
console.log('🔄 Initializing WhatsApp client...');
client.initialize().catch(error => {
    console.error('❌ Failed to initialize WhatsApp client:', error);
    process.exit(1);
});

// Timeout after 60 seconds
setTimeout(() => {
    console.log('⏰ Timeout reached - no QR code generated');
    console.log('❌ There might be an issue with the WhatsApp Web.js setup');
    process.exit(1);
}, 60000);
