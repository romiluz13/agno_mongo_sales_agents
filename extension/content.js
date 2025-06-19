// content.js - Monday.com Integration Content Script
// Enhanced page detection and DOM handling for reliable Monday.com integration

class MondayIntegration {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.selectors = this.initializeSelectors();
        this.pageDetection = this.initializePageDetection();
        this.retryCount = 0;
        this.maxRetries = 10;
        this.connectionStatus = 'unknown'; // Track backend connection status
        this.init();
    }

    initializeSelectors() {
        // Robust selector system with fallbacks for Monday.com DOM changes
        return {
            // Primary selectors (current Monday.com structure)
            primary: {
                boardHeader: '[data-testid="board-header"]',
                boardRows: '[data-testid="row"], .table-row, [class*="table-row"]',
                boardCells: '[data-testid="cell"], .table-cell, [class*="table-cell"]',
                itemId: '[data-item-id]',
                columnHeader: '[data-testid="column-header"]',
                boardContainer: '[data-testid="board"]',
                tableBody: '[data-testid="table-body"]'
            },
            // Fallback selectors (alternative structures)
            fallback: {
                boardHeader: '.board-header, .pulse-table-header, [class*="board-header"]',
                boardRows: '.pulse-row, [class*="pulse-row"], tr[data-pulse-id]',
                boardCells: '.pulse-cell, [class*="pulse-cell"], td',
                itemId: '[data-pulse-id], [data-row-id]',
                columnHeader: '.column-header, [class*="column-header"]',
                boardContainer: '.board-component, [class*="board"]',
                tableBody: '.pulse-table-body, tbody'
            },
            // Legacy selectors (older Monday.com versions)
            legacy: {
                boardHeader: '.board-title, .pulse-table-title',
                boardRows: '.pulse, .pulse-row-wrapper',
                boardCells: '.pulse-cell-wrapper, .cell-wrapper',
                itemId: '[pulse-id], [data-pulse]',
                columnHeader: '.column-title',
                boardContainer: '.pulse-table-wrapper',
                tableBody: '.pulse-table-content'
            }
        };
    }

    initializePageDetection() {
        return {
            // URL patterns for Monday.com pages
            urlPatterns: [
                /https:\/\/.*\.monday\.com\/boards\/\d+/,
                /https:\/\/monday\.com\/boards\/\d+/,
                /https:\/\/.*\.monday\.com\/.*\/boards\/\d+/
            ],
            // Page type detection
            pageTypes: {
                BOARD: 'board',
                DASHBOARD: 'dashboard',
                ITEM: 'item',
                UNKNOWN: 'unknown'
            }
        };
    }

    init() {
        console.log('🤖 Agno Sales Agent: Initializing Monday.com integration...');
        console.log('🔍 Current URL:', window.location.href);

        // Test backend connection on initialization with enhanced feedback
        this.testBackendConnection().then(result => {
            if (result.success) {
                console.log('✅ Backend connection verified');
                this.connectionStatus = 'connected';
                this.showConnectionStatus('connected');
            } else {
                console.warn('⚠️ Backend connection failed:', result.error);
                this.connectionStatus = 'disconnected';
                this.showConnectionStatus('disconnected');
            }
        });

        // Enhanced page detection and loading
        this.detectPageType();
        this.waitForMondayLoad(() => {
            console.log('✅ Monday.com loaded, injecting buttons...');
            this.injectBoardHeaderButton();
            this.injectProcessButtons();
            this.setupObserver();
        });
    }

    detectPageType() {
        const url = window.location.href;
        const pageType = this.determinePageType(url);

        console.log('📄 Page type detected:', pageType);

        // Store page type for conditional logic
        this.currentPageType = pageType;

        return pageType;
    }

    determinePageType(url) {
        if (this.pageDetection.urlPatterns.some(pattern => pattern.test(url))) {
            if (url.includes('/boards/')) {
                return this.pageDetection.pageTypes.BOARD;
            }
        }

        if (url.includes('dashboard')) {
            return this.pageDetection.pageTypes.DASHBOARD;
        }

        if (url.includes('/pulses/') || url.includes('/items/')) {
            return this.pageDetection.pageTypes.ITEM;
        }

        return this.pageDetection.pageTypes.UNKNOWN;
    }

    waitForMondayLoad(callback) {
        console.log('⏳ Waiting for Monday.com to load...');

        const checkInterval = setInterval(() => {
            this.retryCount++;

            if (this.isMondayBoardPage() && this.areRowsLoaded()) {
                console.log(`✅ Monday.com loaded after ${this.retryCount} attempts`);
                clearInterval(checkInterval);
                callback();
            } else if (this.retryCount >= this.maxRetries) {
                console.warn('⚠️ Max retries reached, attempting to inject anyway...');
                clearInterval(checkInterval);
                callback();
            }
        }, 1000);
    }

    isMondayBoardPage() {
        // Enhanced page detection with URL-first approach
        const url = window.location.href;

        // Primary check: URL contains monday.com and boards
        if (url.includes('monday.com') && (url.includes('/boards/') || url.includes('/pulses/'))) {
            console.log('✅ Monday.com board page detected via URL');
            return true;
        }

        // Secondary check: DOM-based detection
        const strategies = [
            () => this.findElement(this.selectors.primary.boardHeader),
            () => this.findElement(this.selectors.fallback.boardHeader),
            () => this.findElement(this.selectors.legacy.boardHeader),
            () => document.title.includes('Board') || document.title.includes('monday'),
            () => document.querySelector('[class*="board"]') || document.querySelector('[data-testid*="board"]')
        ];

        for (const strategy of strategies) {
            try {
                if (strategy()) {
                    console.log('✅ Monday.com board page detected via DOM');
                    return true;
                }
            } catch (error) {
                console.warn('⚠️ Page detection strategy failed:', error);
            }
        }

        console.log('❌ Not a Monday.com board page');
        return false;
    }

    areRowsLoaded() {
        // Enhanced row detection with multiple selector strategies
        const rowCounts = [
            this.findElements(this.selectors.primary.boardRows).length,
            this.findElements(this.selectors.fallback.boardRows).length,
            this.findElements(this.selectors.legacy.boardRows).length,
            // Additional lenient detection
            this.findElements('tr').length,
            this.findElements('div[role="row"]').length,
            this.findElements('[class*="row"]:not([class*="header"])').length
        ];

        const maxRows = Math.max(...rowCounts);
        console.log(`📊 Detected ${maxRows} rows on page`);

        // Be more lenient - even if we detect the page structure, proceed
        return maxRows > 0 || this.isMondayBoardPage();
    }

    findElement(selector) {
        // Utility method to find element with error handling
        try {
            return document.querySelector(selector);
        } catch (error) {
            console.warn(`⚠️ Selector failed: ${selector}`, error);
            return null;
        }
    }

    findElements(selector) {
        // Utility method to find elements with error handling
        try {
            return document.querySelectorAll(selector);
        } catch (error) {
            console.warn(`⚠️ Selector failed: ${selector}`, error);
            return [];
        }
    }

    injectBoardHeaderButton() {
        console.log('🔧 Injecting board header button...');

        // Check if button already exists
        if (document.querySelector('.agno-board-header-btn')) {
            console.log('⚠️ Board header button already exists');
            return;
        }

        // Find the board header area with filter button
        const headerButton = this.createBoardHeaderButton();
        if (this.insertBoardHeaderButton(headerButton)) {
            console.log('✅ Board header button injected successfully');
        } else {
            console.warn('⚠️ Failed to inject board header button');
        }
    }

    injectProcessButtons() {
        console.log('🔧 Injecting process buttons...');

        // Get rows using robust selector strategy
        const rows = this.getAllBoardRows();

        if (rows.length === 0) {
            console.warn('⚠️ No rows found for button injection');
            return;
        }

        console.log(`📋 Found ${rows.length} rows for button injection`);

        let injectedCount = 0;
        rows.forEach((row, index) => {
            try {
                if (!row.querySelector('.agno-process-btn')) {
                    const button = this.createProcessButton(row, index);
                    if (this.insertButton(row, button)) {
                        injectedCount++;
                    }
                }
            } catch (error) {
                console.error(`❌ Failed to inject button for row ${index}:`, error);
            }
        });

        console.log(`✅ Successfully injected ${injectedCount} process buttons`);
    }

    getAllBoardRows() {
        // Robust row detection using multiple selector strategies
        const strategies = [
            () => this.findElements(this.selectors.primary.boardRows),
            () => this.findElements(this.selectors.fallback.boardRows),
            () => this.findElements(this.selectors.legacy.boardRows),
            // Additional aggressive strategies
            () => this.findElements('tr[role="row"]'),
            () => this.findElements('div[role="row"]'),
            () => this.findElements('[class*="row"]:not([class*="header"])'),
            () => this.findElements('tr:has(td)'),
            () => this.findElements('div:has([class*="cell"])')
        ];

        for (const strategy of strategies) {
            try {
                const rows = strategy();
                if (rows.length > 0) {
                    console.log(`✅ Found ${rows.length} rows using selector strategy`);
                    return Array.from(rows);
                }
            } catch (error) {
                console.warn('⚠️ Row detection strategy failed:', error);
            }
        }

        // Last resort: try to find any table-like structure
        console.log('🔍 Trying last resort row detection...');
        const allElements = document.querySelectorAll('*');
        const potentialRows = [];

        for (const element of allElements) {
            const className = element.className || '';
            const tagName = element.tagName.toLowerCase();

            if ((tagName === 'tr' || tagName === 'div') &&
                (className.includes('row') || className.includes('item') || className.includes('pulse')) &&
                !className.includes('header') &&
                element.children.length > 2) {
                potentialRows.push(element);
            }
        }

        if (potentialRows.length > 0) {
            console.log(`✅ Found ${potentialRows.length} potential rows using last resort`);
            return potentialRows;
        }

        console.warn('⚠️ No rows found with any selector strategy');
        return [];
    }

    createBoardHeaderButton() {
        const button = document.createElement('button');
        button.className = 'agno-board-header-btn';
        button.setAttribute('data-agno-header-button', 'true');
        button.innerHTML = '🤖 AI Outreach';

        // Enhanced styling to match Monday.com header buttons exactly
        button.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            margin: 0 4px;
            transition: all 0.2s ease;
            z-index: 9999;
            position: relative;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.4;
            text-align: center;
            white-space: nowrap;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            min-width: auto;
            height: 32px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            vertical-align: middle;
        `;

        // Enhanced interaction handlers for header button
        this.setupHeaderButtonInteractions(button);

        return button;
    }

    createProcessButton(row, index) {
        const button = document.createElement('button');
        button.className = 'agno-process-btn';
        button.setAttribute('data-row-index', index);
        button.setAttribute('data-agno-button', 'true');
        button.innerHTML = '🤖 AI Outreach';

        // Enhanced styling to match Monday.com design language
        button.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            margin: 0 4px;
            transition: all 0.2s ease;
            z-index: 9999;
            position: relative;
            font-family: Roboto, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.2;
            text-align: center;
            white-space: nowrap;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
            min-width: 100px;
            height: 28px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        `;

        // Enhanced interaction handlers
        this.setupButtonInteractions(button, row, index);

        return button;
    }

    setupButtonInteractions(button, row, index) {
        // Hover effects
        button.addEventListener('mouseenter', () => {
            if (!button.disabled) {
                button.style.transform = 'translateY(-1px)';
                button.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
                button.style.background = 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)';
            }
        });

        button.addEventListener('mouseleave', () => {
            if (!button.disabled) {
                button.style.transform = 'translateY(0)';
                button.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.12)';
                button.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
        });

        // Click handler with enhanced feedback
        button.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.handleButtonClick(row, button, index);
        });

        // Keyboard accessibility
        button.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.handleButtonClick(row, button, index);
            }
        });

        // Focus styles
        button.addEventListener('focus', () => {
            button.style.outline = '2px solid #667eea';
            button.style.outlineOffset = '2px';
        });

        button.addEventListener('blur', () => {
            button.style.outline = 'none';
        });
    }

    setupHeaderButtonInteractions(button) {
        // Hover effects for header button
        button.addEventListener('mouseenter', () => {
            if (!button.disabled) {
                button.style.transform = 'translateY(-1px)';
                button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
                button.style.background = 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)';
            }
        });

        button.addEventListener('mouseleave', () => {
            if (!button.disabled) {
                button.style.transform = 'translateY(0)';
                button.style.boxShadow = '0 2px 4px rgba(102, 126, 234, 0.2)';
                button.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
        });

        // Click handler for header button
        button.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.handleHeaderButtonClick(button);
        });

        // Keyboard accessibility
        button.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.handleHeaderButtonClick(button);
            }
        });

        // Focus styles
        button.addEventListener('focus', () => {
            button.style.outline = '2px solid #667eea';
            button.style.outlineOffset = '2px';
        });

        button.addEventListener('blur', () => {
            button.style.outline = 'none';
        });
    }

    insertBoardHeaderButton(button) {
        // Find the board header area and insert button at the same level as New email, Add activity, etc.
        const insertionStrategies = [
            // Strategy 1: Find the exact container with New email, Add activity buttons
            () => {
                // Look for the specific container that has the action buttons
                const containers = document.querySelectorAll('div');
                for (const container of containers) {
                    const hasNewEmail = container.querySelector('button[aria-label*="New email"], [data-testid*="new-email"]');
                    const hasAddActivity = container.querySelector('button[aria-label*="Add activity"], [data-testid*="add-activity"]');
                    const hasFilter = container.querySelector('button[aria-label*="Filter"], [data-testid*="filter"]');

                    if ((hasNewEmail || hasAddActivity || hasFilter) && container.children.length < 10) {
                        // This looks like the action buttons container
                        container.appendChild(button);
                        console.log('✅ Found action buttons container');
                        return true;
                    }
                }
                return false;
            },

            // Strategy 2: Find Filter button and insert before it (same level)
            () => {
                const filterButton = document.querySelector('button[aria-label*="Filter"], [data-testid*="filter"], button[title*="Filter"]');
                if (filterButton && filterButton.parentNode) {
                    // Insert before filter button at the same level
                    filterButton.parentNode.insertBefore(button, filterButton);
                    console.log('✅ Inserted before filter button');
                    return true;
                }
                return false;
            },

            // Strategy 3: Find "Add activity" button and insert after it (same level)
            () => {
                const addActivityButton = document.querySelector('button[aria-label*="Add activity"], [data-testid*="add-activity"]');
                if (addActivityButton && addActivityButton.parentNode) {
                    addActivityButton.parentNode.insertBefore(button, addActivityButton.nextSibling);
                    console.log('✅ Inserted after Add activity button');
                    return true;
                }
                return false;
            },

            // Strategy 4: Find "New email" button and insert after it (same level)
            () => {
                const newEmailButton = document.querySelector('button[aria-label*="New email"], [data-testid*="new-email"]');
                if (newEmailButton && newEmailButton.parentNode) {
                    newEmailButton.parentNode.insertBefore(button, newEmailButton.nextSibling);
                    console.log('✅ Inserted after New email button');
                    return true;
                }
                return false;
            },

            // Strategy 5: Look for the board header toolbar area
            () => {
                // Find elements that contain multiple buttons in a row
                const potentialToolbars = document.querySelectorAll('div[class*="toolbar"], div[class*="actions"], div[class*="header"]');
                for (const toolbar of potentialToolbars) {
                    const buttonCount = toolbar.querySelectorAll('button').length;
                    if (buttonCount >= 2 && buttonCount <= 6) {
                        toolbar.appendChild(button);
                        console.log('✅ Found toolbar with buttons');
                        return true;
                    }
                }
                return false;
            },

            // Strategy 6: Find any container with multiple buttons at the top level
            () => {
                const allDivs = document.querySelectorAll('div');
                for (const div of allDivs) {
                    const buttons = div.querySelectorAll(':scope > button'); // Direct children only
                    if (buttons.length >= 2 && buttons.length <= 5) {
                        // Check if this looks like a button toolbar
                        const hasActionButtons = Array.from(buttons).some(btn =>
                            btn.textContent.includes('New email') ||
                            btn.textContent.includes('Add activity') ||
                            btn.getAttribute('aria-label')?.includes('Filter')
                        );

                        if (hasActionButtons) {
                            div.appendChild(button);
                            console.log('✅ Found button toolbar container');
                            return true;
                        }
                    }
                }
                return false;
            },

            // Strategy 7: Fallback - create our own container in a visible area
            () => {
                // Find any header-like area and create our own button container
                const headerAreas = document.querySelectorAll('[class*="header"], [class*="toolbar"], [class*="top"]');
                for (const header of headerAreas) {
                    if (header.offsetHeight > 0 && header.offsetWidth > 0) { // Visible element
                        const buttonContainer = document.createElement('div');
                        buttonContainer.style.cssText = `
                            display: inline-flex;
                            align-items: center;
                            gap: 8px;
                            margin: 0 8px;
                            position: relative;
                            z-index: 1000;
                        `;
                        buttonContainer.appendChild(button);
                        header.appendChild(buttonContainer);
                        console.log('✅ Created fallback container in header area');
                        return true;
                    }
                }
                return false;
            }
        ];

        for (let i = 0; i < insertionStrategies.length; i++) {
            try {
                if (insertionStrategies[i]()) {
                    console.log(`✅ Header button inserted using strategy ${i + 1}`);
                    return true;
                }
            } catch (error) {
                console.warn(`⚠️ Header button insertion strategy ${i + 1} failed:`, error);
            }
        }

        console.error('❌ All header button insertion strategies failed');
        return false;
    }

    handleHeaderButtonClick(button) {
        console.log('🖱️ Header button clicked - showing lead selection');

        // Show a modal to select which leads to process
        this.showLeadSelectionModal(button);
    }

    showLeadSelectionModal(button) {
        // Get all available rows
        const rows = this.getAllBoardRows();

        if (rows.length === 0) {
            this.showError(button, 'No leads found on this board');
            return;
        }

        // Create lead selection modal
        const modal = this.createLeadSelectionModal(rows);
        document.body.appendChild(modal);
    }

    createLeadSelectionModal(rows) {
        // Remove any existing modals first
        const existingModals = document.querySelectorAll('.agno-lead-selection-modal');
        existingModals.forEach(modal => modal.remove());

        const modal = document.createElement('div');
        modal.className = 'agno-lead-selection-modal';
        modal.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            background: rgba(0, 0, 0, 0.8) !important;
            z-index: 99999999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: Roboto, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            pointer-events: auto !important;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white !important;
            border-radius: 12px !important;
            padding: 24px !important;
            max-width: 700px !important;
            width: 90% !important;
            max-height: 80vh !important;
            overflow-y: auto !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
            position: relative !important;
            z-index: 100000000 !important;
            pointer-events: auto !important;
        `;

        // Extract lead data for display
        const leadData = rows.map((row, index) => {
            const cells = this.getAllRowCells(row);
            const name = this.extractCellValueRobust(cells, ['Lead', 'Lead Name', 'Name', 'Contact Name', 'Person']) || `Lead ${index + 1}`;
            const company = this.extractCellValueRobust(cells, ['Company', 'Organization', 'Account']) || 'Unknown Company';
            return { row, index, name, company };
        });

        modalContent.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #333; font-size: 24px;">🤖 AI Outreach - Select Leads</h2>
                <button class="agno-close-modal" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #666;">×</button>
            </div>

            <p style="color: #666; margin-bottom: 20px;">Select the leads you want to process with AI outreach:</p>

            <div class="agno-lead-list" style="max-height: 400px; overflow-y: auto; margin-bottom: 20px;">
                ${leadData.map(lead => `
                    <div class="agno-lead-item" style="
                        display: flex;
                        align-items: center;
                        padding: 12px;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        margin-bottom: 8px;
                        cursor: pointer;
                        transition: background 0.2s;
                    " data-row-index="${lead.index}">
                        <input type="checkbox" class="agno-lead-checkbox" style="margin-right: 12px;" data-row-index="${lead.index}">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #333;">${lead.name}</div>
                            <div style="color: #666; font-size: 14px;">${lead.company}</div>
                        </div>
                    </div>
                `).join('')}
            </div>

            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button class="agno-cancel-btn" style="
                    padding: 10px 20px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    background: white;
                    color: #666;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                ">Cancel</button>
                <button class="agno-process-selected-btn" style="
                    padding: 10px 20px;
                    border: none;
                    border-radius: 6px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                    transition: background 0.2s;
                ">Process Selected Leads</button>
            </div>
        `;

        modal.appendChild(modalContent);

        // Add event listeners
        this.setupLeadSelectionModalEvents(modal, rows);

        return modal;
    }

    setupLeadSelectionModalEvents(modal, rows) {
        const closeBtn = modal.querySelector('.agno-close-modal');
        const cancelBtn = modal.querySelector('.agno-cancel-btn');
        const processBtn = modal.querySelector('.agno-process-selected-btn');
        const leadItems = modal.querySelectorAll('.agno-lead-item');
        const checkboxes = modal.querySelectorAll('.agno-lead-checkbox');

        // Close modal
        const closeModal = () => {
            document.body.removeChild(modal);
        };

        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Make lead items clickable to toggle checkbox
        leadItems.forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox') {
                    const checkbox = item.querySelector('.agno-lead-checkbox');
                    checkbox.checked = !checkbox.checked;
                }

                // Update item styling based on selection
                if (item.querySelector('.agno-lead-checkbox').checked) {
                    item.style.background = '#f0f7ff';
                    item.style.borderColor = '#667eea';
                } else {
                    item.style.background = 'white';
                    item.style.borderColor = '#e0e0e0';
                }
            });

            // Hover effects
            item.addEventListener('mouseenter', () => {
                if (!item.querySelector('.agno-lead-checkbox').checked) {
                    item.style.background = '#f8f9fa';
                }
            });

            item.addEventListener('mouseleave', () => {
                if (!item.querySelector('.agno-lead-checkbox').checked) {
                    item.style.background = 'white';
                }
            });
        });

        // Process selected leads
        processBtn.addEventListener('click', async () => {
            const selectedIndices = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => parseInt(cb.dataset.rowIndex));

            if (selectedIndices.length === 0) {
                alert('Please select at least one lead to process.');
                return;
            }

            console.log(`🚀 Processing ${selectedIndices.length} selected leads...`);

            // Disable button and show processing state
            processBtn.disabled = true;
            processBtn.textContent = `Processing ${selectedIndices.length} leads...`;

            // Close modal
            closeModal();

            // Process each selected lead
            for (const index of selectedIndices) {
                const row = rows[index];
                if (row) {
                    try {
                        // Create a temporary button for this row
                        const tempButton = this.createProcessButton(row, index);
                        await this.processLead(row, tempButton, index);
                    } catch (error) {
                        console.error(`❌ Failed to process lead ${index}:`, error);
                    }
                }
            }

            console.log('✅ Finished processing all selected leads');
        });
    }

    handleButtonClick(row, button, index) {
        // Enhanced click handling with better state management
        if (button.disabled) {
            console.log('⚠️ Button already processing, ignoring click');
            return;
        }

        console.log(`🖱️ Button clicked for row ${index}`);

        // Add click animation
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            if (!button.disabled) {
                button.style.transform = 'translateY(0)';
            }
        }, 150);

        // Process the lead
        this.processLead(row, button, index);
    }

    insertButton(row, button) {
        // Enhanced button insertion with multiple strategies
        const insertionStrategies = [
            // Strategy 1: Last cell with primary selectors
            () => {
                const lastCell = row.querySelector(`${this.selectors.primary.boardCells}:last-child`);
                if (lastCell) {
                    lastCell.appendChild(button);
                    return true;
                }
                return false;
            },

            // Strategy 2: Last cell with fallback selectors
            () => {
                const cells = row.querySelectorAll(this.selectors.fallback.boardCells);
                if (cells.length > 0) {
                    const lastCell = cells[cells.length - 1];
                    lastCell.appendChild(button);
                    return true;
                }
                return false;
            },

            // Strategy 3: Create new cell if needed
            () => {
                const newCell = document.createElement('div');
                newCell.className = 'agno-button-cell';
                newCell.style.cssText = `
                    display: inline-flex;
                    align-items: center;
                    padding: 4px 8px;
                    min-width: 120px;
                `;
                newCell.appendChild(button);
                row.appendChild(newCell);
                return true;
            },

            // Strategy 4: Direct append to row
            () => {
                row.appendChild(button);
                return true;
            }
        ];

        for (let i = 0; i < insertionStrategies.length; i++) {
            try {
                if (insertionStrategies[i]()) {
                    console.log(`✅ Button inserted using strategy ${i + 1}`);
                    return true;
                }
            } catch (error) {
                console.warn(`⚠️ Button insertion strategy ${i + 1} failed:`, error);
            }
        }

        console.error('❌ All button insertion strategies failed');
        return false;
    }

    async processLead(row, button, index) {
        try {
            console.log(`🚀 Processing lead for row ${index}...`);

            // Prevent multiple simultaneous processing
            if (button.dataset.processing === 'true') {
                console.log('⚠️ Lead already being processed');
                return;
            }

            // Mark as processing
            button.dataset.processing = 'true';

            // Feature flag: Use MongoDB-powered workflow if available
            const useMongoDBWorkflow = await this.shouldUseMongoDBWorkflow();

            if (useMongoDBWorkflow) {
                console.log('🔄 Using MongoDB-powered workflow');
                await this.processLeadWithMongoDB(row, button, index);
            } else {
                console.log('🔄 Using legacy DOM-based workflow');
                await this.processLeadLegacy(row, button, index);
            }

        } catch (error) {
            console.error('❌ Process lead error:', error);
            this.showError(button, 'Processing failed. Please try again.');
            this.trackProcessingError({ monday_id: 'unknown' }, error.message);
        } finally {
            // Always clear processing state
            button.dataset.processing = 'false';
        }
    }

    async shouldUseMongoDBWorkflow() {
        // Feature flag to enable MongoDB workflow
        // Check if we can extract board ID (indicates Monday.com page)
        const boardId = this.getBoardIdFromUrl();
        return boardId !== null;
    }

    async processLeadWithMongoDB(row, button, index) {
        try {
            // Extract Monday.com identifiers
            const mondayData = this.extractMondayItemId(row);
            mondayData.row_index = index;
            console.log('🆔 Extracted Monday.com data:', mondayData);

            // Validate Monday.com data
            const validation = this.validateMondayData(mondayData);
            if (!validation.isValid) {
                this.showError(button, `Validation failed: ${validation.errors.join(', ')}`);
                return;
            }

            // Show processing state with progress
            this.showProcessing(button, `Generating preview for ${mondayData.fallback_name}...`, 0);

            // NEW: Generate message preview first
            const previewRequest = {
                monday_item_id: mondayData.monday_item_id,
                board_id: mondayData.board_id,
                fallback_name: mondayData.fallback_name,
                fallback_company: mondayData.fallback_company
            };

            console.log('🔄 Generating message preview...');
            const previewResult = await this.sendToBackend('/api/preview-message', previewRequest);

            if (previewResult.preview_id) {
                // Show preview and approval UI
                console.log('🎯 Preview result received:', previewResult);
                console.log('🎯 Monday data:', mondayData);
                this.showMessagePreview(button, previewResult, mondayData);
                console.log('🎯 showMessagePreview called');
            } else {
                console.error('❌ No preview_id in result:', previewResult);
                this.showError(button, 'Failed to generate message preview');
            }

        } catch (error) {
            console.error('❌ MongoDB workflow error:', error);
            throw error; // Re-throw to be handled by main processLead method
        }
    }

    async processLeadLegacy(row, button, index) {
        try {
            // Extract lead data from row (legacy method)
            const leadData = this.extractLeadData(row);
            leadData.row_index = index;
            console.log('📊 Extracted lead data:', leadData);

            if (!this.validateLeadData(leadData)) {
                this.showError(button, 'Missing required lead information');
                return;
            }

            // Show processing state with progress
            this.showProcessing(button, 'Researching...', 0);

            // Create progress tracking
            const progressSteps = [
                { message: 'Researching company...', progress: 25 },
                { message: 'Generating message...', progress: 50 },
                { message: 'Preparing outreach...', progress: 75 },
                { message: 'Finalizing...', progress: 90 }
            ];

            let currentStep = 0;
            const progressInterval = setInterval(() => {
                if (currentStep < progressSteps.length) {
                    const step = progressSteps[currentStep];
                    this.showProcessing(button, step.message, step.progress);
                    currentStep++;
                } else {
                    clearInterval(progressInterval);
                }
            }, 2000);

            // Transform lead data to backend API format
            const apiRequest = this.transformLeadDataForAPI(leadData);
            console.log('🔄 Transformed API request:', apiRequest);

            // Send to backend for processing
            const result = await this.sendToBackend('/api/process-lead', apiRequest);

            // Clear progress interval
            clearInterval(progressInterval);

            if (result.success) {
                this.showSuccess(button, 'Lead processed successfully!');
                this.showSuccessWithDetails('Legacy processing completed', result);
                this.updateMondayRow(row, result);

                // Track successful processing
                this.trackProcessingSuccess(leadData, result);
            } else {
                this.showError(button, result.error || 'Processing failed');
                this.showDetailedError(result.error || 'Processing failed', 'Legacy Processing');
                this.trackProcessingError(leadData, result.error);
            }

        } catch (error) {
            console.error('❌ Legacy workflow error:', error);
            throw error; // Re-throw to be handled by main processLead method
        }
    }

    trackProcessingSuccess(leadData, result) {
        // Track successful processing for analytics
        console.log('✅ Lead processing successful:', {
            monday_id: leadData.monday_id,
            company: leadData.company,
            timestamp: new Date().toISOString()
        });
    }

    trackProcessingError(leadData, error) {
        // Track processing errors for debugging
        console.error('❌ Lead processing failed:', {
            monday_id: leadData.monday_id,
            company: leadData.company,
            error: error,
            timestamp: new Date().toISOString()
        });
    }

    extractLeadData(row) {
        console.log('📊 Extracting lead data from row...');

        // Get cells using robust selector strategy
        const cells = this.getAllRowCells(row);
        console.log('📊 Found cells for extraction:', cells.length);

        const leadData = {
            monday_id: this.getMondayItemId(row),
            name: this.extractCellValueRobust(cells, ['Lead', 'Lead Name', 'Name', 'Contact Name', 'Person']),
            company: this.extractCellValueRobust(cells, ['Company', 'Organization', 'Account']),
            email: this.extractCellValueRobust(cells, ['Email', 'Email Address', 'Contact Email']),
            phone: this.extractCellValueRobust(cells, ['Phone', 'Phone Number', 'Mobile', 'Contact Phone']),
            status: this.extractCellValueRobust(cells, ['Status', 'Lead Status', 'Stage']),
            // Additional fields for better data extraction
            title: this.extractCellValueRobust(cells, ['Title', 'Job Title', 'Position']),
            notes: this.extractCellValueRobust(cells, ['Notes', 'Description', 'Comments']),
            source: this.extractCellValueRobust(cells, ['Source', 'Lead Source', 'Origin'])
        };

        console.log('📊 Column-based extraction results:', {
            name: leadData.name,
            company: leadData.company,
            email: leadData.email,
            phone: leadData.phone
        });

        // Fallback: if no data found, try to extract from cell text content directly
        if (!leadData.name && !leadData.company && cells.length > 0) {
            console.log('🔄 Using fallback data extraction...');

            // Try to extract data from cell text content by position
            const cellTexts = cells.map(cell => this.getCellTextContent(cell)).filter(text => text);
            console.log('📊 Cell texts:', cellTexts);

            if (cellTexts.length >= 2) {
                leadData.name = cellTexts[0] || 'Demo Lead';
                leadData.company = cellTexts[1] || 'Demo Company';
                leadData.phone = this.findPhoneInTexts(cellTexts) || '+1234567890';
                leadData.email = this.findEmailInTexts(cellTexts) || 'demo@example.com';
            }
        }

        console.log('📋 Extracted lead data:', leadData);
        return leadData;
    }

    transformLeadDataForAPI(leadData) {
        // Transform extracted lead data to match backend API LeadProcessRequest format
        return {
            lead_id: leadData.monday_id || `agno_${Date.now()}`,
            lead_name: leadData.name || 'Unknown Lead',
            company: leadData.company || 'Unknown Company',
            title: leadData.title || 'Unknown Title',
            industry: this.inferIndustry(leadData.company),
            company_size: this.inferCompanySize(leadData.company),
            phone_number: this.formatPhoneNumber(leadData.phone),
            message_type: 'text', // Default to text messages
            sender_name: 'Agno Sales Agent',
            sender_company: 'Your Company',
            value_proposition: this.generateValueProposition(leadData)
        };
    }

    transformMondayDataForAPI(mondayData) {
        // NEW METHOD: Transform Monday.com data for MongoDB-powered workflow
        return {
            monday_item_id: mondayData.monday_item_id,
            board_id: mondayData.board_id,
            fallback_name: mondayData.fallback_name,
            fallback_company: mondayData.fallback_company
        };
    }

    inferIndustry(company) {
        // Simple industry inference based on company name
        if (!company) return 'Unknown';

        const companyLower = company.toLowerCase();
        const industryKeywords = {
            'technology': ['tech', 'software', 'digital', 'ai', 'data', 'cloud', 'cyber'],
            'healthcare': ['health', 'medical', 'pharma', 'bio', 'clinic', 'hospital'],
            'finance': ['bank', 'financial', 'invest', 'capital', 'fund', 'insurance'],
            'retail': ['retail', 'store', 'shop', 'commerce', 'market'],
            'manufacturing': ['manufacturing', 'industrial', 'factory', 'production'],
            'consulting': ['consulting', 'advisory', 'services', 'solutions']
        };

        for (const [industry, keywords] of Object.entries(industryKeywords)) {
            if (keywords.some(keyword => companyLower.includes(keyword))) {
                return industry;
            }
        }

        return 'General Business';
    }

    inferCompanySize(company) {
        // Simple company size inference - in real implementation, this would use research data
        if (!company) return 'Unknown';

        const companyLower = company.toLowerCase();

        // Large company indicators
        if (['inc', 'corp', 'corporation', 'ltd', 'limited', 'group', 'holdings'].some(term => companyLower.includes(term))) {
            return 'Large (500+ employees)';
        }

        // Default to medium for now
        return 'Medium (50-500 employees)';
    }

    formatPhoneNumber(phone) {
        if (!phone) return '';

        // Remove all non-digit characters
        const digits = phone.replace(/\D/g, '');

        // Add country code if missing (assuming US for now)
        if (digits.length === 10) {
            return `+1${digits}`;
        } else if (digits.length === 11 && digits.startsWith('1')) {
            return `+${digits}`;
        }

        return phone; // Return original if can't format
    }

    generateValueProposition(leadData) {
        // Generate a basic value proposition based on lead data
        const company = leadData.company || 'your company';
        const title = leadData.title || 'your role';

        return `Hi! I noticed ${company} might benefit from AI-powered sales automation. Given your ${title} position, I thought you'd be interested in how we're helping similar companies increase their sales efficiency by 40%. Would you be open to a brief conversation?`;
    }

    getAllRowCells(row) {
        // Debug: Log the row structure
        console.log('🔍 Debugging row structure:', row);
        console.log('🔍 Row HTML:', row.outerHTML.substring(0, 500) + '...');
        console.log('🔍 Row children:', row.children);

        // Robust cell detection using multiple selector strategies
        const strategies = [
            () => row.querySelectorAll(this.selectors.primary.boardCells),
            () => row.querySelectorAll(this.selectors.fallback.boardCells),
            () => row.querySelectorAll(this.selectors.legacy.boardCells),
            // Additional aggressive strategies for modern Monday.com
            () => row.querySelectorAll('div[class*="cell"]'),
            () => row.querySelectorAll('td'),
            () => row.querySelectorAll('[role="gridcell"]'),
            () => row.querySelectorAll('[class*="column"]'),
            () => row.querySelectorAll('div[data-column-id]'),
            () => row.querySelectorAll('div[style*="width"]'), // Monday.com uses inline styles
            () => Array.from(row.children) // Last resort: all direct children
        ];

        for (let i = 0; i < strategies.length; i++) {
            try {
                const cells = strategies[i]();
                if (cells.length > 0) {
                    console.log(`✅ Found ${cells.length} cells using strategy ${i + 1}`);
                    console.log('🔍 First cell:', cells[0]);
                    return Array.from(cells);
                }
            } catch (error) {
                console.warn(`⚠️ Cell detection strategy ${i + 1} failed:`, error);
            }
        }

        console.warn('⚠️ No cells found in row');
        return [];
    }

    getMondayItemId(row) {
        // Enhanced item ID extraction with multiple strategies
        // Strategy 1: Extract from URL (most reliable for pulse detail pages)
        const currentUrl = window.location.href;
        const pulseMatch = currentUrl.match(/\/pulses\/(\d+)/);
        if (pulseMatch) {
            console.log('✅ Found Monday.com item ID from URL:', pulseMatch[1]);
            return pulseMatch[1];
        }

        // Strategy 2-N: DOM-based extraction
        const idStrategies = [
            () => row.getAttribute('data-item-id'),
            () => row.getAttribute('data-pulse-id'),
            () => row.getAttribute('data-row-id'),
            () => row.querySelector('[data-item-id]')?.getAttribute('data-item-id'),
            () => row.querySelector('[data-pulse-id]')?.getAttribute('data-pulse-id'),
            () => row.querySelector(this.selectors.primary.itemId)?.getAttribute('data-item-id'),
            () => row.querySelector(this.selectors.fallback.itemId)?.getAttribute('data-pulse-id')
        ];

        for (const strategy of idStrategies) {
            try {
                const id = strategy();
                if (id && /^\d+$/.test(id)) {
                    console.log('✅ Found Monday.com item ID:', id);
                    return id;
                }
            } catch (error) {
                console.warn('⚠️ ID extraction strategy failed:', error);
            }
        }

        // Don't generate fallback ID - return null to indicate failure
        console.error('❌ Could not extract Monday.com item ID from URL or DOM');
        console.error('❌ Current URL:', currentUrl);
        console.error('❌ Row element:', row.outerHTML.substring(0, 200) + '...');
        return null;
    }

    getBoardIdFromUrl() {
        // Extract board ID from Monday.com URL pattern: /boards/{board_id}
        const url = window.location.href;
        console.log('🔍 Extracting board ID from URL:', url);

        const boardIdMatch = url.match(/\/boards\/(\d+)/);
        if (boardIdMatch) {
            const boardId = boardIdMatch[1];
            console.log('✅ Found Monday.com board ID:', boardId);
            return boardId;
        }

        console.warn('⚠️ Could not extract board ID from URL');
        return null;
    }

    getMondayItemIdEnhanced(row) {
        // First try existing DOM-based strategies
        const domId = this.getMondayItemId(row);
        if (domId && !domId.startsWith('agno_')) {
            return domId;
        }

        // Fallback: try URL-based extraction for item detail pages
        const url = window.location.href;
        const itemIdMatch = url.match(/\/pulses\/(\d+)/);
        if (itemIdMatch) {
            const itemId = itemIdMatch[1];
            console.log('✅ Found Monday.com item ID from URL:', itemId);
            return itemId;
        }

        console.warn('⚠️ Could not extract Monday.com item ID from DOM or URL');
        return domId; // Return fallback ID if nothing else works
    }

    extractMondayItemId(row) {
        // NEW METHOD: Extract Monday.com item ID and board ID for MongoDB workflow
        console.log('🆔 Extracting Monday.com identifiers...');

        const monday_item_id = this.getMondayItemIdEnhanced(row);
        const board_id = this.getBoardIdFromUrl();

        // Get cells for fallback data extraction
        const cells = this.getAllRowCells(row);

        // Keep minimal fallback data for UI display
        const fallback_name = this.extractCellValueRobust(cells, ['Lead', 'Lead Name', 'Name', 'Contact Name', 'Person']);
        const fallback_company = this.extractCellValueRobust(cells, ['Company', 'Organization', 'Account']);

        const mondayData = {
            monday_item_id,
            board_id,
            fallback_name: fallback_name || 'Unknown Lead',
            fallback_company: fallback_company || 'Unknown Company'
        };

        console.log('🆔 Extracted Monday.com data:', mondayData);
        return mondayData;
    }

    validateMondayData(data) {
        // Validate Monday.com identifiers
        const errors = [];

        if (!data.monday_item_id) {
            errors.push('Monday.com item ID not found - cannot process lead');
            return { isValid: false, errors };
        } else if (!/^\d+$/.test(data.monday_item_id)) {
            errors.push('Invalid Monday.com item ID format - must be numeric');
            return { isValid: false, errors };
        }

        if (!data.board_id) {
            errors.push('Monday.com board ID not found');
        } else if (!/^\d+$/.test(data.board_id)) {
            errors.push('Invalid Monday.com board ID format');
        }

        const isValid = errors.length === 0;

        if (isValid) {
            console.log('✅ Monday.com data validation passed');
        } else {
            console.warn('⚠️ Monday.com data validation failed:', errors);
        }

        return {
            isValid,
            errors
        };
    }

    extractCellValueRobust(cells, columnNames) {
        // Enhanced cell value extraction with multiple column name variations
        for (const columnName of columnNames) {
            const value = this.extractCellValue(cells, columnName);
            if (value) {
                return value;
            }
        }
        return '';
    }

    extractCellValue(cells, columnName) {
        // Enhanced cell value extraction with multiple strategies
        const extractionStrategies = [
            // Strategy 1: data-column-title attribute
            () => {
                const cell = cells.find(cell =>
                    cell.getAttribute('data-column-title') === columnName
                );
                return cell ? this.getCellTextContent(cell) : '';
            },

            // Strategy 2: title attribute contains column name
            () => {
                const cell = cells.find(cell =>
                    cell.querySelector(`[title*="${columnName}"]`)
                );
                return cell ? this.getCellTextContent(cell) : '';
            },

            // Strategy 3: aria-label contains column name
            () => {
                const cell = cells.find(cell =>
                    cell.getAttribute('aria-label')?.includes(columnName)
                );
                return cell ? this.getCellTextContent(cell) : '';
            }
        ];

        for (const strategy of extractionStrategies) {
            try {
                const value = strategy();
                if (value) {
                    return value;
                }
            } catch (error) {
                console.warn(`⚠️ Cell extraction strategy failed for ${columnName}:`, error);
            }
        }

        return '';
    }

    getCellTextContent(cell) {
        // Enhanced text content extraction
        if (!cell) return '';

        // Try different text extraction methods
        const textStrategies = [
            () => cell.querySelector('input')?.value,
            () => cell.querySelector('textarea')?.value,
            () => cell.querySelector('[contenteditable]')?.textContent,
            () => cell.textContent,
            () => cell.innerText
        ];

        for (const strategy of textStrategies) {
            try {
                const text = strategy();
                if (text && text.trim()) {
                    return text.trim();
                }
            } catch (error) {
                console.warn('⚠️ Text extraction strategy failed:', error);
            }
        }

        return '';
    }

    findPhoneInTexts(texts) {
        // Enhanced phone number detection for international numbers
        const phoneRegexes = [
            // International format: +972 53 223 4542
            /\+\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}/,
            // US format: (555) 123-4567
            /(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})/,
            // Simple international: +972532234542
            /\+\d{10,15}/,
            // Any sequence of digits with separators
            /\d{3,4}[\s\-]\d{3,4}[\s\-]\d{3,4}/
        ];

        for (const text of texts) {
            for (const regex of phoneRegexes) {
                const match = text.match(regex);
                if (match) {
                    console.log(`📞 Found phone number: ${match[0]} in text: ${text}`);
                    return match[0];
                }
            }
        }
        return null;
    }

    findEmailInTexts(texts) {
        // Enhanced email detection
        const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
        for (const text of texts) {
            const match = text.match(emailRegex);
            if (match) {
                console.log(`📧 Found email: ${match[0]} in text: ${text}`);
                return match[0];
            }
        }
        return null;
    }

    validateLeadData(data) {
        // More lenient validation for testing - just need name OR company
        const hasMinimumFields = data.name || data.company;
        if (!hasMinimumFields) {
            console.warn('⚠️ Missing minimum required fields:', {
                name: !!data.name,
                company: !!data.company,
                phone: !!data.phone,
                email: !!data.email
            });
        } else {
            console.log('✅ Lead data validation passed:', {
                name: !!data.name,
                company: !!data.company,
                phone: !!data.phone,
                email: !!data.email
            });
        }
        return hasMinimumFields;
    }

    async sendToBackend(endpoint, data, options = {}) {
        const {
            method = 'POST',
            maxRetries = 3,
            retryDelay = 1000,
            timeout = 30000
        } = options;

        let lastError = null;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`🔌 API Request (attempt ${attempt}/${maxRetries}): ${method} ${endpoint}`);

                // Create request with timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);

                const requestOptions = {
                    method,
                    headers: await this.getRequestHeaders(),
                    signal: controller.signal
                };

                // Add body for POST/PUT requests
                if (method !== 'GET' && data) {
                    requestOptions.body = JSON.stringify(data);
                }

                const response = await fetch(`${this.apiUrl}${endpoint}`, requestOptions);

                // Clear timeout
                clearTimeout(timeoutId);

                // Handle different response statuses
                const result = await this.handleApiResponse(response);

                console.log(`✅ API Request successful (attempt ${attempt})`);
                return result;

            } catch (error) {
                lastError = error;
                console.warn(`⚠️ API Request failed (attempt ${attempt}/${maxRetries}):`, error.message);

                // Don't retry for certain error types
                if (this.isNonRetryableError(error)) {
                    console.error('❌ Non-retryable error, aborting:', error.message);
                    throw error;
                }

                // Wait before retry (exponential backoff)
                if (attempt < maxRetries) {
                    const delay = retryDelay * Math.pow(2, attempt - 1);
                    console.log(`⏳ Waiting ${delay}ms before retry...`);
                    await this.sleep(delay);
                }
            }
        }

        // All retries failed
        console.error(`❌ All ${maxRetries} API attempts failed`);
        throw new Error(`API request failed after ${maxRetries} attempts: ${lastError?.message || 'Unknown error'}`);
    }

    async getRequestHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Extension-Version': '1.0.0',
            'X-Request-Source': 'chrome-extension'
        };

        // Add authentication if available
        const authToken = await this.getAuthToken();
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        return headers;
    }

    async getAuthToken() {
        // For development, use bypass token
        // In production, implement proper authentication
        try {
            const result = await chrome.storage.local.get(['authToken']);
            return result.authToken || 'dev-bypass-token';
        } catch (error) {
            console.warn('⚠️ Failed to get auth token:', error);
            return 'dev-bypass-token';
        }
    }

    async handleApiResponse(response) {
        const contentType = response.headers.get('content-type');

        // Handle different content types
        let responseData;
        if (contentType && contentType.includes('application/json')) {
            responseData = await response.json();
        } else {
            responseData = { message: await response.text() };
        }

        // Handle HTTP error statuses
        if (!response.ok) {
            const errorMessage = responseData.detail || responseData.message || `HTTP ${response.status}: ${response.statusText}`;

            // Create specific error types for different status codes
            const error = new Error(errorMessage);
            error.status = response.status;
            error.statusText = response.statusText;
            error.responseData = responseData;

            // Add error classification
            if (response.status >= 400 && response.status < 500) {
                error.type = 'CLIENT_ERROR';
            } else if (response.status >= 500) {
                error.type = 'SERVER_ERROR';
            } else {
                error.type = 'UNKNOWN_ERROR';
            }

            throw error;
        }

        return responseData;
    }

    isNonRetryableError(error) {
        // Don't retry for these error types
        const nonRetryableStatuses = [400, 401, 403, 404, 422];
        const nonRetryableTypes = ['AbortError', 'TypeError'];

        return (
            nonRetryableStatuses.includes(error.status) ||
            nonRetryableTypes.includes(error.name) ||
            error.message.includes('Failed to fetch') ||
            error.message.includes('NetworkError')
        );
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Additional API communication methods for Task 9.2

    async testBackendConnection() {
        try {
            console.log('🔍 Testing backend connection...');

            // Try the new extension-specific endpoint first
            const result = await this.sendToBackend('/api/extension-status', null, {
                method: 'GET',
                timeout: 5000,
                maxRetries: 1
            });

            console.log('✅ Backend connection test successful:', result);
            return { success: true, data: result };

        } catch (error) {
            console.error('❌ Backend connection test failed:', error);

            // Try fallback to health endpoint
            try {
                console.log('🔄 Trying fallback health endpoint...');
                const fallbackResult = await this.sendToBackend('/health', null, {
                    method: 'GET',
                    timeout: 5000,
                    maxRetries: 1
                });

                console.log('✅ Fallback connection successful:', fallbackResult);
                return { success: true, data: fallbackResult };

            } catch (fallbackError) {
                console.error('❌ Fallback connection also failed:', fallbackError);
                return {
                    success: false,
                    error: fallbackError.message,
                    status: fallbackError.status
                };
            }
        }
    }

    async testAllConnections() {
        try {
            console.log('🔍 Testing all API connections...');

            const result = await this.sendToBackend('/api/test-connections', null, {
                method: 'POST',
                timeout: 10000,
                maxRetries: 1
            });

            console.log('✅ Connection test results:', result);
            return { success: true, data: result };

        } catch (error) {
            console.error('❌ Connection test failed:', error);
            return {
                success: false,
                error: error.message,
                status: error.status
            };
        }
    }

    async getLeadStatus(leadId) {
        try {
            console.log(`🔍 Getting status for lead: ${leadId}`);

            const result = await this.sendToBackend(`/api/lead-status/${leadId}`, null, {
                method: 'GET',
                timeout: 5000,
                maxRetries: 2
            });

            console.log('✅ Lead status retrieved:', result);
            return { success: true, data: result };

        } catch (error) {
            console.error('❌ Failed to get lead status:', error);
            return {
                success: false,
                error: error.message,
                status: error.status
            };
        }
    }

    async getWorkflowProgress(workflowId) {
        try {
            console.log(`🔍 Getting workflow progress: ${workflowId}`);

            const result = await this.sendToBackend(`/api/workflow-progress/${workflowId}`, null, {
                method: 'GET',
                timeout: 5000,
                maxRetries: 2
            });

            console.log('✅ Workflow progress retrieved:', result);
            return { success: true, data: result };

        } catch (error) {
            console.error('❌ Failed to get workflow progress:', error);
            return {
                success: false,
                error: error.message,
                status: error.status
            };
        }
    }

    async sendDirectMessage(phoneNumber, message, messageType = 'text') {
        try {
            console.log(`📱 Sending direct message to: ${phoneNumber}`);

            const messageData = {
                phone_number: phoneNumber,
                message: message,
                message_type: messageType
            };

            const result = await this.sendToBackend('/api/send-message', messageData, {
                timeout: 15000,
                maxRetries: 2
            });

            console.log('✅ Message sent successfully:', result);
            return { success: true, data: result };

        } catch (error) {
            console.error('❌ Failed to send message:', error);
            return {
                success: false,
                error: error.message,
                status: error.status
            };
        }
    }

    showProcessing(button, message, progress = 0) {
        // Enhanced processing state with better visual feedback
        button.innerHTML = `
            <span style="display: inline-flex; align-items: center; width: 100%;">
                <span class="agno-loading" style="margin-right: 6px;"></span>
                <span style="flex: 1; text-align: center;">${message}</span>
                ${progress > 0 ? `<span style="font-size: 10px; margin-left: 4px;">${progress}%</span>` : ''}
            </span>
        `;
        button.disabled = true;
        button.style.cursor = 'not-allowed';
        button.style.transform = 'none';
        button.title = `Processing... ${progress}%`;

        // Enhanced progress indicator with smooth transitions
        if (progress > 0) {
            button.style.background = `linear-gradient(90deg, #28a745 0%, #28a745 ${progress}%, #ffa500 ${progress}%, #ff8c00 100%)`;
            button.style.transition = 'background 0.3s ease-in-out';
        } else {
            button.style.background = 'linear-gradient(135deg, #ffa500 0%, #ff8c00 100%)';
        }

        // Add pulsing effect for active processing
        button.style.animation = 'agno-processing-pulse 2s ease-in-out infinite';
    }

    showSuccess(button, message) {
        button.innerHTML = `
            <span style="display: inline-flex; align-items: center;">
                ✅ Success!
            </span>
        `;
        button.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
        button.style.transform = 'none';
        button.title = message;

        // Add success animation
        button.style.animation = 'agno-success-pulse 0.6s ease-out';

        setTimeout(() => {
            this.resetButton(button);
        }, 3000);
    }

    showError(button, message) {
        button.innerHTML = `
            <span style="display: inline-flex; align-items: center;">
                ❌ Error
            </span>
        `;
        button.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
        button.style.transform = 'none';
        button.title = message; // Show full error on hover

        // Add error animation
        button.style.animation = 'agno-error-shake 0.6s ease-out';

        setTimeout(() => {
            this.resetButton(button);
        }, 4000); // Longer timeout for errors
    }

    resetButton(button) {
        button.innerHTML = '🤖 Process Lead';
        button.disabled = false;
        button.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        button.style.cursor = 'pointer';
        button.style.transform = 'translateY(0)';
        button.style.animation = 'none';
        button.title = '';
        button.dataset.processing = 'false';
    }

    addButtonAnimations() {
        // Enhanced CSS animations for comprehensive button feedback
        if (!document.getElementById('agno-button-animations')) {
            const style = document.createElement('style');
            style.id = 'agno-button-animations';
            style.textContent = `
                @keyframes agno-success-pulse {
                    0% { transform: scale(1); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12); }
                    50% { transform: scale(1.05); box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4); }
                    100% { transform: scale(1); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12); }
                }

                @keyframes agno-error-shake {
                    0%, 100% { transform: translateX(0); }
                    10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
                    20%, 40%, 60%, 80% { transform: translateX(4px); }
                }

                @keyframes agno-processing-pulse {
                    0% { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12); }
                    50% { box-shadow: 0 2px 8px rgba(255, 165, 0, 0.3); }
                    100% { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12); }
                }

                @keyframes agno-spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                @keyframes agno-fade-in {
                    0% { opacity: 0; transform: translateY(-10px); }
                    100% { opacity: 1; transform: translateY(0); }
                }

                .agno-loading {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border: 2px solid transparent;
                    border-top: 2px solid white;
                    border-radius: 50%;
                    animation: agno-spin 1s linear infinite;
                }

                .agno-process-btn {
                    animation: agno-fade-in 0.3s ease-out;
                    transition: all 0.2s ease;
                }

                .agno-process-btn:hover:not(:disabled) {
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                }

                .agno-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 12px 16px;
                    border-radius: 6px;
                    color: white;
                    font-family: Roboto, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 14px;
                    z-index: 10000;
                    animation: agno-fade-in 0.3s ease-out;
                    max-width: 300px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }

                .agno-notification.success {
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                }

                .agno-notification.error {
                    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                }

                .agno-notification.info {
                    background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                }
            `;
            document.head.appendChild(style);
        }
    }

    // Enhanced User Feedback System for Task 9.3

    showNotification(message, type = 'info', duration = 5000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `agno-notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()"
                        style="background: none; border: none; color: white; cursor: pointer; margin-left: 10px; font-size: 16px;">×</button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'agno-fade-out 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);

        return notification;
    }

    showConnectionStatus(status) {
        const statusMessages = {
            'connected': { message: '✅ Backend connected successfully', type: 'success' },
            'disconnected': { message: '❌ Backend connection failed', type: 'error' },
            'reconnecting': { message: '🔄 Reconnecting to backend...', type: 'info' }
        };

        const config = statusMessages[status] || { message: `Status: ${status}`, type: 'info' };
        this.showNotification(config.message, config.type, 3000);
    }

    showWorkflowProgress(workflowId, step, progress) {
        // Enhanced workflow progress indication
        const progressMessage = `Workflow ${workflowId}: ${step} (${progress}%)`;
        console.log(`🔄 ${progressMessage}`);

        // Update any existing progress notifications
        const existingNotification = document.querySelector(`.agno-notification[data-workflow="${workflowId}"]`);
        if (existingNotification) {
            existingNotification.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span>${progressMessage}</span>
                    <div style="width: 60px; height: 4px; background: rgba(255,255,255,0.3); border-radius: 2px; margin-left: 10px;">
                        <div style="width: ${progress}%; height: 100%; background: white; border-radius: 2px; transition: width 0.3s ease;"></div>
                    </div>
                </div>
            `;
        } else {
            const notification = this.showNotification(progressMessage, 'info', 10000);
            notification.setAttribute('data-workflow', workflowId);
        }
    }

    showDetailedError(error, context = '') {
        // Enhanced error display with more context
        let errorMessage = 'An error occurred';
        let errorDetails = '';

        if (typeof error === 'string') {
            errorMessage = error;
        } else if (error.message) {
            errorMessage = error.message;
            if (error.status) {
                errorDetails = ` (HTTP ${error.status})`;
            }
        }

        const fullMessage = context ? `${context}: ${errorMessage}${errorDetails}` : `${errorMessage}${errorDetails}`;

        console.error('🚨 Detailed Error:', { error, context, fullMessage });
        this.showNotification(fullMessage, 'error', 8000);
    }

    showSuccessWithDetails(message, details = null) {
        // Enhanced success display with optional details
        let fullMessage = message;

        if (details) {
            if (details.workflow_id) {
                fullMessage += ` (ID: ${details.workflow_id})`;
            }
            if (details.execution_time_seconds) {
                fullMessage += ` - Completed in ${details.execution_time_seconds}s`;
            }
        }

        console.log('🎉 Success:', { message, details, fullMessage });
        this.showNotification(fullMessage, 'success', 5000);
    }

    updateMondayRow(row, data) {
        // Update Monday.com row with processing results
        console.log('📝 Updating Monday.com row with results:', data);
        
        // Update visible cells if they exist
        this.updateCellValue(row, 'Agent Status', 'Processing Complete');
        if (data.research_summary) {
            this.updateCellValue(row, 'Research Notes', data.research_summary.substring(0, 100) + '...');
        }
    }

    updateCellValue(row, columnName, value) {
        const cell = row.querySelector(`[data-column-title="${columnName}"]`);
        if (cell) {
            const textElement = cell.querySelector('span, div') || cell;
            textElement.textContent = value;
        }
    }

    setupObserver() {
        console.log('👀 Setting up enhanced DOM observer...');

        // Enhanced mutation observer for dynamic content
        const observer = new MutationObserver((mutations) => {
            let shouldReinject = false;

            mutations.forEach((mutation) => {
                // Check for added nodes that might be new rows
                if (mutation.addedNodes.length > 0) {
                    for (const node of mutation.addedNodes) {
                        if (this.isRelevantNode(node)) {
                            shouldReinject = true;
                            break;
                        }
                    }
                }

                // Check for attribute changes that might affect our selectors
                if (mutation.type === 'attributes' &&
                    ['data-testid', 'class', 'id'].includes(mutation.attributeName)) {
                    shouldReinject = true;
                }
            });

            if (shouldReinject) {
                // Debounce to avoid excessive calls
                clearTimeout(this.observerTimeout);
                this.observerTimeout = setTimeout(() => {
                    console.log('🔄 DOM changed, re-injecting buttons...');
                    this.injectBoardHeaderButton();
                    this.injectProcessButtons();
                }, 500);
            }
        });

        // Enhanced observer configuration
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['data-testid', 'class', 'id', 'data-item-id', 'data-pulse-id']
        });

        // Also observe URL changes for SPA navigation
        this.setupUrlObserver();

        console.log('✅ Enhanced DOM observer setup complete');
        this.observer = observer;
    }

    isRelevantNode(node) {
        // Check if the added node is relevant for our injection
        if (node.nodeType !== Node.ELEMENT_NODE) return false;

        const relevantSelectors = [
            this.selectors.primary.boardRows,
            this.selectors.fallback.boardRows,
            this.selectors.legacy.boardRows,
            this.selectors.primary.boardContainer,
            this.selectors.fallback.boardContainer
        ];

        for (const selector of relevantSelectors) {
            try {
                if (node.matches && node.matches(selector)) return true;
                if (node.querySelector && node.querySelector(selector)) return true;
            } catch (error) {
                // Ignore selector errors
            }
        }

        return false;
    }

    setupUrlObserver() {
        // Monitor URL changes for SPA navigation
        let currentUrl = window.location.href;

        const urlCheckInterval = setInterval(() => {
            if (window.location.href !== currentUrl) {
                console.log('🔄 URL changed, re-initializing...');
                currentUrl = window.location.href;

                // Reset retry count and re-initialize
                this.retryCount = 0;
                this.detectPageType();

                // Wait a bit for new page to load, then inject
                setTimeout(() => {
                    this.injectBoardHeaderButton();
                    this.injectProcessButtons();
                }, 2000);
            }
        }, 1000);

        // Store interval for cleanup
        this.urlCheckInterval = urlCheckInterval;
    }

    showMessagePreview(button, previewResult, mondayData) {
        console.log('🎯 Showing message preview modal...', previewResult);

        // Create preview modal
        const modal = this.createPreviewModal(previewResult, mondayData);
        document.body.appendChild(modal);

        console.log('✅ Modal added to DOM:', modal);

        // Update button to show preview state (safely handle null button)
        if (button) {
            this.showPreviewState(button, 'Preview ready - click to view', () => {
                // Show modal again if clicked
                modal.style.display = 'flex';
            });
        } else {
            console.log('⚠️ Button is null, modal created but button not updated');
        }
    }

    createPreviewModal(previewResult, mondayData) {
        // Remove any existing modals first
        const existingModals = document.querySelectorAll('.agno-preview-modal');
        existingModals.forEach(modal => modal.remove());

        const modal = document.createElement('div');
        modal.className = 'agno-preview-modal';
        modal.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            background: rgba(0, 0, 0, 0.8) !important;
            z-index: 99999999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: Roboto, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            pointer-events: auto !important;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white !important;
            border-radius: 12px !important;
            padding: 24px !important;
            max-width: 600px !important;
            width: 90% !important;
            max-height: 80vh !important;
            overflow-y: auto !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
            position: relative !important;
            z-index: 100000000 !important;
            pointer-events: auto !important;
        `;

        modalContent.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #333; font-size: 24px;">Message Preview</h2>
                <button class="agno-close-modal" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #666;">×</button>
            </div>

            <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                    <div>
                        <strong>Lead:</strong> ${previewResult.lead_name}<br>
                        <strong>Company:</strong> ${previewResult.company}
                    </div>
                    <div>
                        <strong>Personalization:</strong> ${(previewResult.personalization_score * 100).toFixed(1)}%<br>
                        <strong>Response Rate:</strong> ${(previewResult.predicted_response_rate * 100).toFixed(1)}%
                    </div>
                </div>
            </div>

            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #333;">Message:</label>
                <textarea class="agno-message-editor" style="
                    width: 100%;
                    min-height: 120px;
                    padding: 12px;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    font-size: 14px;
                    line-height: 1.5;
                    resize: vertical;
                    font-family: inherit;
                " placeholder="Edit message here...">${previewResult.message_text}</textarea>
            </div>

            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button class="agno-reject-btn" style="
                    background: #dc3545;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: background 0.2s;
                ">Reject</button>
                <button class="agno-approve-btn" style="
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: background 0.2s;
                ">Send Message</button>
            </div>
        `;

        modal.appendChild(modalContent);

        // Add event listeners
        this.setupPreviewModalEvents(modal, previewResult, mondayData);

        return modal;
    }

    setupPreviewModalEvents(modal, previewResult, mondayData) {
        const closeBtn = modal.querySelector('.agno-close-modal');
        const rejectBtn = modal.querySelector('.agno-reject-btn');
        const approveBtn = modal.querySelector('.agno-approve-btn');
        const messageEditor = modal.querySelector('.agno-message-editor');

        // Close modal
        closeBtn.addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });

        // Reject message
        rejectBtn.addEventListener('click', async () => {
            await this.handleMessageApproval(previewResult.preview_id, 'reject', null, mondayData.monday_item_id);
            document.body.removeChild(modal);
        });

        // Approve/Send message
        approveBtn.addEventListener('click', async () => {
            const editedMessage = messageEditor.value.trim();
            const action = editedMessage !== previewResult.message_text ? 'edit' : 'approve';

            approveBtn.disabled = true;
            approveBtn.textContent = 'Sending...';

            try {
                await this.handleMessageApproval(previewResult.preview_id, action, editedMessage, mondayData.monday_item_id);
                document.body.removeChild(modal);
            } catch (error) {
                approveBtn.disabled = false;
                approveBtn.textContent = 'Send Message';
                this.showError(approveBtn, 'Send failed: ' + error.message);
            }
        });

        // Hover effects
        rejectBtn.addEventListener('mouseenter', () => {
            rejectBtn.style.background = '#c82333';
        });
        rejectBtn.addEventListener('mouseleave', () => {
            rejectBtn.style.background = '#dc3545';
        });

        approveBtn.addEventListener('mouseenter', () => {
            approveBtn.style.background = '#218838';
        });
        approveBtn.addEventListener('mouseleave', () => {
            approveBtn.style.background = '#28a745';
        });
    }

    async handleMessageApproval(previewId, action, editedMessage, mondayItemId) {
        try {
            console.log(`🎯 Handling message approval: ${action} for preview ${previewId}`);

            const approvalRequest = {
                preview_id: previewId,
                action: action,
                edited_message: editedMessage,
                monday_item_id: mondayItemId
            };

            const result = await this.sendToBackend('/api/approve-message', approvalRequest);

            if (result.success) {
                if (action === 'reject') {
                    this.showNotification('Message rejected', 'warning');
                } else {
                    this.showNotification('Message sent successfully!', 'success');
                }
            } else {
                throw new Error(result.error || 'Approval failed');
            }

        } catch (error) {
            console.error('❌ Message approval failed:', error);
            this.showNotification('Approval failed: ' + error.message, 'error');
            throw error;
        }
    }

    showPreviewState(button, message, clickHandler = null) {
        if (!button) {
            console.log('⚠️ Button is null, skipping preview state update');
            return;
        }

        button.innerHTML = '👁️ Preview Ready - Click to View';
        button.style.background = 'linear-gradient(135deg, #17a2b8 0%, #138496 100%)';
        button.disabled = false;

        // Add click handler to reopen preview
        if (clickHandler) {
            // Remove existing listeners by cloning
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);

            newButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🎯 Preview button clicked!');
                clickHandler();
            });
        } else {
            button.addEventListener('click', () => {
                this.showNotification('Preview completed - check Monday.com for updates', 'info');
            });
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 60000000;
            font-family: Roboto, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            max-width: 300px;
            word-wrap: break-word;
        `;

        // Set background color based on type
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        notification.style.background = colors[type] || colors.info;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 5000);
    }

    // Debug method to test modal display
    testModal() {
        console.log('🧪 Testing modal display...');
        const testPreviewResult = {
            preview_id: 'test_123',
            message_text: 'This is a test message for MongoDB sales outreach.',
            personalization_score: 0.85,
            predicted_response_rate: 0.42,
            lead_name: 'Test Lead',
            company: 'Test Company',
            phone_number: '+1234567890',
            generated_at: new Date().toISOString()
        };

        const testMondayData = {
            monday_item_id: 'test_item',
            board_id: 'test_board'
        };

        this.showMessagePreview(null, testPreviewResult, testMondayData);
    }
}

// Global function for testing modal from browser console
window.testAgnoModal = function() {
    console.log('🧪 Testing Agno modal from console...');
    if (window.mondayIntegration) {
        window.mondayIntegration.testModal();
    } else {
        console.error('❌ Monday integration not found');
    }
};

// Initialize when content script loads
console.log('🚀 Agno Sales Agent: Content script loaded');

// Create and initialize the Monday.com integration
const mondayIntegration = new MondayIntegration();
window.mondayIntegration = mondayIntegration;

// Add button animations CSS
mondayIntegration.addButtonAnimations();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (mondayIntegration.observer) {
        mondayIntegration.observer.disconnect();
    }
    if (mondayIntegration.urlCheckInterval) {
        clearInterval(mondayIntegration.urlCheckInterval);
    }
    console.log('🧹 Agno Sales Agent: Cleaned up resources');
});
