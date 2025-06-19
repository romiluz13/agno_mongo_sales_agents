// popup.js - Popup Interface Management
// Handles configuration, status checking, and user interactions

class PopupManager {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.init();
    }

    init() {
        console.log('🎛️ Popup Manager: Initializing...');
        this.loadConfiguration();
        this.checkConnectionStatus();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Configuration actions
        document.getElementById('save-config').addEventListener('click', () => this.saveConfiguration());
        
        // Connection actions
        document.getElementById('test-connection').addEventListener('click', () => this.testAllConnections());
        document.getElementById('connect-whatsapp').addEventListener('click', () => this.connectWhatsApp());
        
        // Navigation actions
        document.getElementById('open-monday').addEventListener('click', () => this.openMondayBoard());
        
        // Auto-save on input change
        ['monday-token', 'board-id', 'tavily-key'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                this.saveConfiguration(false); // Save without notification
            });
        });
    }

    async loadConfiguration() {
        try {
            const config = await chrome.storage.sync.get(['mondayToken', 'boardId', 'tavilyKey']);
            
            if (config.mondayToken) {
                document.getElementById('monday-token').value = config.mondayToken;
            }
            if (config.boardId) {
                document.getElementById('board-id').value = config.boardId;
            }
            if (config.tavilyKey) {
                document.getElementById('tavily-key').value = config.tavilyKey;
            }
            
            console.log('✅ Configuration loaded');
        } catch (error) {
            console.error('❌ Failed to load configuration:', error);
            this.showNotification('Failed to load configuration', 'error');
        }
    }

    async saveConfiguration(showNotification = true) {
        try {
            const config = {
                mondayToken: document.getElementById('monday-token').value.trim(),
                boardId: document.getElementById('board-id').value.trim(),
                tavilyKey: document.getElementById('tavily-key').value.trim()
            };

            await chrome.storage.sync.set(config);
            
            if (showNotification) {
                this.showNotification('Configuration saved successfully!', 'success');
                
                // Auto-test connections after saving
                setTimeout(() => this.testAllConnections(), 1000);
            }
            
            console.log('💾 Configuration saved');
        } catch (error) {
            console.error('❌ Failed to save configuration:', error);
            this.showNotification('Failed to save configuration', 'error');
        }
    }

    async testAllConnections() {
        const testButton = document.getElementById('test-connection');
        const originalText = testButton.textContent;
        
        try {
            // Update UI to show testing state
            testButton.innerHTML = '<span class="loading"></span>Testing...';
            testButton.disabled = true;
            
            this.updateStatus('backend-status', '⏳ Testing...', 'testing');
            this.updateStatus('monday-status', '⏳ Testing...', 'testing');
            this.updateStatus('whatsapp-status', '⏳ Testing...', 'testing');
            
            // Get current configuration
            const config = await chrome.storage.sync.get(['mondayToken', 'boardId', 'tavilyKey']);
            
            // Test backend connection (no body needed - backend uses env vars)
            const response = await fetch(`${this.apiUrl}/api/test-connections`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: AbortSignal.timeout(10000) // 10 second timeout
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Update status indicators (match backend response format)
                this.updateStatus('backend-status',
                    result.mongodb ? '✅ Connected' : '❌ Failed',
                    result.mongodb ? 'connected' : 'disconnected'
                );

                this.updateStatus('monday-status',
                    result.monday_com ? '✅ Connected' : '❌ Failed',
                    result.monday_com ? 'connected' : 'disconnected'
                );

                this.updateStatus('whatsapp-status',
                    result.whatsapp ? '✅ Connected' : '❌ Disconnected',
                    result.whatsapp ? 'connected' : 'disconnected'
                );

                // Show overall result
                const allConnected = result.mongodb && result.monday_com;
                this.showNotification(
                    allConnected ? 'All connections successful!' : 'Some connections failed. Check configuration.',
                    allConnected ? 'success' : 'error'
                );
                
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('🔌 Connection test failed:', error);
            
            // Update all statuses to failed
            this.updateStatus('backend-status', '❌ Failed', 'disconnected');
            this.updateStatus('monday-status', '❌ Failed', 'disconnected');
            this.updateStatus('whatsapp-status', '❌ Failed', 'disconnected');
            
            this.showNotification('Connection test failed. Check if backend is running.', 'error');
            
        } finally {
            // Reset button
            testButton.textContent = originalText;
            testButton.disabled = false;
        }
    }

    async connectWhatsApp() {
        const connectButton = document.getElementById('connect-whatsapp');
        const originalText = connectButton.textContent;
        
        try {
            connectButton.innerHTML = '<span class="loading"></span>Connecting...';
            connectButton.disabled = true;
            
            this.updateStatus('whatsapp-status', '⏳ Connecting...', 'testing');
            
            const response = await fetch(`${this.apiUrl}/api/whatsapp/connect`, { 
                method: 'POST',
                signal: AbortSignal.timeout(15000) // 15 second timeout
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.qr_code) {
                    this.showQRCode(result.qr_code);
                    this.showNotification('QR Code generated! Scan with WhatsApp to connect.', 'success');
                } else if (result.connected) {
                    this.updateStatus('whatsapp-status', '✅ Connected', 'connected');
                    this.showNotification('WhatsApp connected successfully!', 'success');
                } else {
                    this.showNotification('WhatsApp connection initiated. Check backend logs.', 'success');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('📱 WhatsApp connection failed:', error);
            this.updateStatus('whatsapp-status', '❌ Failed', 'disconnected');
            this.showNotification('WhatsApp connection failed. Check backend.', 'error');
            
        } finally {
            connectButton.textContent = originalText;
            connectButton.disabled = false;
        }
    }

    showQRCode(qrCode) {
        // Create a new window/tab to display QR code
        const qrWindow = window.open('', '_blank', 'width=400,height=400');
        qrWindow.document.write(`
            <html>
                <head><title>WhatsApp QR Code</title></head>
                <body style="text-align: center; padding: 20px; font-family: Arial, sans-serif;">
                    <h2>🤖 Agno Sales Agent</h2>
                    <p>Scan this QR code with WhatsApp:</p>
                    <img src="${qrCode}" style="max-width: 300px; border: 1px solid #ccc; border-radius: 8px;">
                    <p style="font-size: 12px; color: #666; margin-top: 20px;">
                        Open WhatsApp → Settings → Linked Devices → Link a Device
                    </p>
                </body>
            </html>
        `);
    }

    async openMondayBoard() {
        try {
            const config = await chrome.storage.sync.get(['boardId']);
            const boardId = config.boardId;
            
            if (boardId) {
                const mondayUrl = `https://monday.com/boards/${boardId}`;
                chrome.tabs.create({ url: mondayUrl });
                this.showNotification('Opening Monday.com board...', 'success');
            } else {
                this.showNotification('Please configure Board ID first', 'error');
            }
        } catch (error) {
            console.error('📋 Failed to open Monday.com:', error);
            this.showNotification('Failed to open Monday.com board', 'error');
        }
    }

    updateStatus(elementId, status, className) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = status;
            element.className = `status-indicator status-${className}`;
        }
    }

    showNotification(message, type) {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 5000);
    }

    async checkConnectionStatus() {
        // Initial status check
        setTimeout(() => this.testAllConnections(), 1000);
        
        // Periodic status check every 30 seconds
        setInterval(() => {
            this.testAllConnections();
        }, 30000);
    }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Popup: DOM loaded, initializing...');
    new PopupManager();
});
