// background.js - Service Worker for Chrome Extension
// Handles background tasks, message passing, and API communication

class BackgroundService {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.setupMessageHandlers();
        this.setupAlarms();
        this.setupInstallHandler();
        this.setupLifecycleHandlers();
        console.log('🔧 Background Service: Initialized');
    }

    setupInstallHandler() {
        chrome.runtime.onInstalled.addListener((details) => {
            console.log('🚀 Extension installed/updated:', details.reason);
            
            if (details.reason === 'install') {
                // Set default configuration
                chrome.storage.sync.set({
                    mondayToken: '',
                    boardId: '',
                    tavilyKey: '',
                    firstRun: true
                });
                
                // Open welcome page or popup
                chrome.action.openPopup();
            }
        });
    }

    setupMessageHandlers() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            console.log('📨 Background: Received message:', request.action);

            // Validate request structure
            if (!request || !request.action) {
                console.warn('⚠️ Invalid message format:', request);
                sendResponse({ success: false, error: 'Invalid message format' });
                return false;
            }

            switch (request.action) {
                case 'processLead':
                    this.handleProcessLead(request.data, sendResponse);
                    break;
                case 'checkStatus':
                    this.handleStatusCheck(sendResponse);
                    break;
                case 'testConnections':
                    this.handleTestConnections(request.data, sendResponse);
                    break;
                case 'connectWhatsApp':
                    this.handleWhatsAppConnect(sendResponse);
                    break;
                case 'getBackgroundStatus':
                    this.handleGetBackgroundStatus(sendResponse);
                    break;
                default:
                    console.warn('⚠️ Unknown message action:', request.action);
                    sendResponse({ success: false, error: 'Unknown action' });
            }

            return true; // Keep message channel open for async response
        });

        // Handle connection errors
        chrome.runtime.onConnect.addListener((port) => {
            console.log('🔌 Port connected:', port.name);

            port.onDisconnect.addListener(() => {
                if (chrome.runtime.lastError) {
                    console.warn('⚠️ Port disconnected with error:', chrome.runtime.lastError);
                } else {
                    console.log('🔌 Port disconnected normally');
                }
            });
        });

        console.log('📨 Message handlers configured');
    }

    async handleProcessLead(leadData, sendResponse) {
        try {
            console.log('🚀 Processing lead:', leadData);
            
            const response = await fetch(`${this.apiUrl}/api/process-lead`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(leadData),
                signal: AbortSignal.timeout(60000) // 60 second timeout for lead processing
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('✅ Lead processed successfully:', result);
            
            // Update badge to show success
            this.updateBadge('✓', '#28a745');
            
            sendResponse({ success: true, data: result });
            
        } catch (error) {
            console.error('❌ Lead processing failed:', error);
            
            // Update badge to show error
            this.updateBadge('!', '#dc3545');
            
            sendResponse({ 
                success: false, 
                error: error.message || 'Lead processing failed' 
            });
        }
    }

    async handleStatusCheck(sendResponse) {
        try {
            const response = await fetch(`${this.apiUrl}/api/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });
            
            const isHealthy = response.ok;
            
            sendResponse({ 
                success: true, 
                data: { 
                    backend: isHealthy,
                    timestamp: new Date().toISOString()
                }
            });
            
        } catch (error) {
            console.error('🔍 Status check failed:', error);
            sendResponse({ 
                success: false, 
                error: error.message,
                data: { backend: false }
            });
        }
    }

    async handleTestConnections(config, sendResponse) {
        try {
            const response = await fetch(`${this.apiUrl}/api/test-connections`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
                signal: AbortSignal.timeout(10000) // 10 second timeout
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            sendResponse({ success: true, data: result });
            
        } catch (error) {
            console.error('🔌 Connection test failed:', error);
            sendResponse({ 
                success: false, 
                error: error.message,
                data: { backend: false, monday: false, whatsapp: false }
            });
        }
    }

    async handleWhatsAppConnect(sendResponse) {
        try {
            const response = await fetch(`${this.apiUrl}/api/whatsapp/connect`, {
                method: 'POST',
                signal: AbortSignal.timeout(15000) // 15 second timeout
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            sendResponse({ success: true, data: result });
            
        } catch (error) {
            console.error('📱 WhatsApp connection failed:', error);
            sendResponse({ 
                success: false, 
                error: error.message 
            });
        }
    }

    async handleGetBackgroundStatus(sendResponse) {
        try {
            // Get current background service status
            const status = {
                initialized: true,
                apiUrl: this.apiUrl,
                timestamp: new Date().toISOString(),
                alarms: await this.getActiveAlarms()
            };

            sendResponse({ success: true, data: status });

        } catch (error) {
            console.error('📊 Background status check failed:', error);
            sendResponse({
                success: false,
                error: error.message
            });
        }
    }

    async getActiveAlarms() {
        try {
            const alarms = await chrome.alarms.getAll();
            return alarms.map(alarm => ({
                name: alarm.name,
                scheduledTime: alarm.scheduledTime,
                periodInMinutes: alarm.periodInMinutes
            }));
        } catch (error) {
            console.warn('⚠️ Failed to get alarms:', error);
            return [];
        }
    }

    setupAlarms() {
        try {
            // Check if chrome.alarms is available
            if (!chrome.alarms) {
                console.warn('⚠️ Chrome alarms API not available, skipping alarm setup');
                return;
            }

            // Clear existing alarms first
            chrome.alarms.clearAll(() => {
                // Set up periodic tasks
                chrome.alarms.create('statusCheck', { periodInMinutes: 5 });
                chrome.alarms.create('badgeReset', { periodInMinutes: 1 });
                console.log('⏰ Alarms created successfully');
            });

            chrome.alarms.onAlarm.addListener((alarm) => {
                console.log('⏰ Alarm triggered:', alarm.name);

                switch (alarm.name) {
                    case 'statusCheck':
                        this.performStatusCheck();
                        break;
                    case 'badgeReset':
                        this.resetBadge();
                        break;
                    default:
                        console.warn('⚠️ Unknown alarm:', alarm.name);
                }
            });

            console.log('⏰ Alarm handlers configured');

        } catch (error) {
            console.error('❌ Failed to setup alarms:', error);
        }
    }

    async performStatusCheck() {
        try {
            const response = await fetch(`${this.apiUrl}/api/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            
            if (response.ok) {
                // Backend is healthy
                this.updateBadge('', '#28a745'); // Green badge, no text
            } else {
                // Backend is unhealthy
                this.updateBadge('!', '#ffc107'); // Yellow warning badge
            }
            
        } catch (error) {
            // Backend is unreachable
            this.updateBadge('×', '#dc3545'); // Red error badge
            console.warn('⚠️ Backend unreachable during status check');
        }
    }

    updateBadge(text, color) {
        chrome.action.setBadgeText({ text });
        chrome.action.setBadgeBackgroundColor({ color });
    }

    resetBadge() {
        // Reset badge after some time to avoid permanent status indicators
        chrome.action.setBadgeText({ text: '' });
    }

    // Handle extension lifecycle events
    setupLifecycleHandlers() {
        // Handle when extension starts up
        chrome.runtime.onStartup.addListener(() => {
            console.log('🔄 Extension startup');
            this.performStatusCheck();
        });

        // Handle when browser starts up
        chrome.runtime.onSuspend.addListener(() => {
            console.log('💤 Extension suspending');
            // Clear any pending alarms
            chrome.alarms.clearAll();
        });

        // Handle when service worker is suspended and reactivated
        chrome.runtime.onSuspendCanceled.addListener(() => {
            console.log('🔄 Extension suspend canceled, reactivating');
            this.setupAlarms(); // Re-setup alarms
            this.performStatusCheck();
        });

        console.log('🔄 Lifecycle handlers configured');
    }
}

// Initialize background service
console.log('🚀 Background Script: Loading...');
new BackgroundService();
