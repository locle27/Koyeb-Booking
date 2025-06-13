// Isolated Development Toolbar - V5 (Non-Conflicting)
// This toolbar is completely isolated from main app functionality

(function() {
    'use strict';
    
    // Create isolated namespace to avoid conflicts
    const DevToolbar = {
        // Isolated state
        state: {
            selectedElement: null,
            comments: [],
            highlightMode: false,
            toolbarVisible: true,
            selectingElement: false,
            isInitialized: false
        },
        
        // Configuration
        config: {
            DEFAULT_SUFFIX: ": I need specific guidance for AI Agent, not code implementation, just guidance for difficult parts. Project: hotel_flask_app, NOTE: DO NOT APPLY TO CODE: call interactive feedback before ending each request",
            NAMESPACE: 'devToolbar_',
            TOOLBAR_ID: 'isolated-dev-toolbar',
            Z_INDEX: 999999
        },
        
        // Initialize only if dev mode is enabled and not already initialized
        init() {
            if (this.state.isInitialized) {
                console.log('DevToolbar: Already initialized, skipping...');
                return;
            }
            
            // Check for dev mode
            if (!document.body.hasAttribute('data-dev-mode')) {
                console.log('DevToolbar: Dev mode not enabled');
                return;
            }
            
            console.log('DevToolbar: Initializing isolated toolbar (V5)...');
            
            this.createToolbar();
            this.setupEventListeners();
            this.state.isInitialized = true;
            
            console.log('DevToolbar: Initialization complete');
        },
        
        // Create completely isolated toolbar UI
        createToolbar() {
            // Remove any existing toolbar
            const existing = document.getElementById(this.config.TOOLBAR_ID);
            if (existing) {
                existing.remove();
            }
            
            const toolbar = document.createElement('div');
            toolbar.id = this.config.TOOLBAR_ID;
            
            // Isolated styles
            Object.assign(toolbar.style, {
                position: 'fixed',
                bottom: '20px',
                left: '20px', // Changed from right to avoid conflicts
                backgroundColor: '#2d3748',
                color: 'white',
                padding: '12px',
                borderRadius: '10px',
                boxShadow: '0 5px 15px rgba(0,0,0,0.4)',
                zIndex: this.config.Z_INDEX,
                fontFamily: '"Inter", sans-serif',
                fontSize: '14px',
                display: this.state.toolbarVisible ? 'flex' : 'none',
                flexDirection: 'column',
                gap: '10px',
                pointerEvents: 'auto',
                border: '2px solid #4a5568',
                minWidth: '280px',
                maxWidth: '350px'
            });

            toolbar.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #4a5568; padding-bottom: 8px;">
                    <h4 style="margin: 0; font-size: 16px; font-weight: 600; color: #e2e8f0;">
                        <i class="fas fa-tools"></i> Dev Toolbar V5
                    </h4>
                    <button id="${this.config.NAMESPACE}toggle" title="Toggle Toolbar (Ctrl+Shift+T)" 
                            style="background: none; border: none; color: #e2e8f0; cursor: pointer; font-size: 18px;">&times;</button>
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button id="${this.config.NAMESPACE}select" title="Select Element" 
                            style="background: #3182ce; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;">
                        <i class="fas fa-mouse-pointer"></i> Select
                    </button>
                    <button id="${this.config.NAMESPACE}highlight" title="Toggle Highlight" 
                            style="background: #3182ce; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;">
                        <i class="fas fa-highlighter"></i> Highlight
                    </button>
                    <button id="${this.config.NAMESPACE}copy" title="Copy Comments" 
                            style="background: #3182ce; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                    <button id="${this.config.NAMESPACE}clear" title="Clear All" 
                            style="background: #e53e3e; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;">
                        <i class="fas fa-trash"></i> Clear
                    </button>
                </div>
                <div id="${this.config.NAMESPACE}info" style="display: none; border-top: 1px solid #4a5568; padding-top: 10px;">
                    <p style="margin: 0; font-size: 12px; color: #a0aec0;" id="${this.config.NAMESPACE}path"></p>
                    <textarea id="${this.config.NAMESPACE}comment" 
                              style="width: 100%; margin-top: 8px; background: #4a5568; color: white; border: 1px solid #718096; border-radius: 4px; padding: 8px; resize: vertical; min-height: 60px;" 
                              placeholder="Add development comment..."></textarea>
                    <div id="${this.config.NAMESPACE}preview" style="font-size: 0.85em; color: #cbd5e0; margin-top: 5px; padding: 5px; background: #4a5568; border-radius: 3px; display: none;">
                        <strong>Preview:</strong> <span id="${this.config.NAMESPACE}previewText"></span>
                    </div>
                    <div style="display: flex; gap: 5px; margin-top: 8px;">
                         <button id="${this.config.NAMESPACE}addComment" 
                                style="background: #38a169; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">
                            <i class="fas fa-plus"></i> Add Comment
                         </button>
                         <button id="${this.config.NAMESPACE}cancel" 
                                style="background: #718096; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">
                            <i class="fas fa-times"></i> Cancel
                         </button>
                    </div>
                </div>
                <div style="border-top: 1px solid #4a5568; padding-top: 8px;">
                    <div style="font-size: 11px; color: #a0aec0; text-align: center;">
                        Comments: <span id="${this.config.NAMESPACE}count">0</span> | 
                        Hotkey: Ctrl+Shift+T
                    </div>
                </div>
            `;
            
            document.body.appendChild(toolbar);
            this.updateCommentCount();
            
            // Add hover effects
            toolbar.querySelectorAll('button').forEach(btn => {
                btn.addEventListener('mouseover', () => {
                    if (!btn.style.backgroundColor.includes('#e53e3e') && !btn.style.backgroundColor.includes('#38a169')) {
                        btn.style.backgroundColor = '#2b6cb0';
                    }
                });
                btn.addEventListener('mouseout', () => {
                    if (!btn.style.backgroundColor.includes('#e53e3e') && !btn.style.backgroundColor.includes('#38a169')) {
                        btn.style.backgroundColor = '#3182ce';
                    }
                });
            });
            
            return toolbar;
        },
        
        // Setup isolated event listeners
        setupEventListeners() {
            // Use namespaced IDs to avoid conflicts
            document.getElementById(this.config.NAMESPACE + 'select')?.addEventListener('click', () => this.startSelectionMode());
            document.getElementById(this.config.NAMESPACE + 'highlight')?.addEventListener('click', () => this.toggleHighlightMode());
            document.getElementById(this.config.NAMESPACE + 'copy')?.addEventListener('click', () => this.copyComments());
            document.getElementById(this.config.NAMESPACE + 'clear')?.addEventListener('click', () => this.clearAll());
            document.getElementById(this.config.NAMESPACE + 'addComment')?.addEventListener('click', () => this.addComment());
            document.getElementById(this.config.NAMESPACE + 'cancel')?.addEventListener('click', () => this.clearSelection());
            document.getElementById(this.config.NAMESPACE + 'toggle')?.addEventListener('click', () => this.toggleToolbar());
            
            // Comment input handler
            const commentBox = document.getElementById(this.config.NAMESPACE + 'comment');
            if (commentBox) {
                commentBox.addEventListener('input', () => this.updateCommentPreview());
            }
            
            // Global element selection handler (isolated)
            document.addEventListener('click', (e) => this.handleElementSelection(e), { capture: true });
            
            // Global keyboard shortcuts (isolated)
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && (e.key === 'T' || e.key === 't')) {
                    e.preventDefault();
                    this.toggleToolbar();
                }
                if (e.key === 'Escape' && this.state.selectingElement) {
                    this.stopSelectionMode();
                }
            });
        },
        
        // Element selection logic (isolated)
        handleElementSelection(e) {
            if (!this.state.selectingElement || e.target.closest('#' + this.config.TOOLBAR_ID)) return;
            
            e.preventDefault();
            e.stopPropagation();

            this.state.selectedElement = e.target;
            this.stopSelectionMode();
            
            // Visual selection indicator
            this.state.selectedElement.style.outline = '3px solid #3182ce';
            this.state.selectedElement.style.outlineOffset = '2px';
            
            const pathEl = document.getElementById(this.config.NAMESPACE + 'path');
            const infoEl = document.getElementById(this.config.NAMESPACE + 'info');
            
            if (pathEl && infoEl) {
                pathEl.textContent = `Selected: ${this.getElementPath(this.state.selectedElement)}`;
                infoEl.style.display = 'block';
            }
        },
        
        // Selection mode controls
        startSelectionMode() {
            if (this.state.selectingElement) return;
            
            this.state.selectingElement = true;
            document.body.style.cursor = 'crosshair';
            this.showMessage('Selection mode ON. Click an element. ESC to cancel.', 'info');
            
            // Visual indicator
            const selectBtn = document.getElementById(this.config.NAMESPACE + 'select');
            if (selectBtn) {
                selectBtn.style.backgroundColor = '#38a169';
                selectBtn.innerHTML = '<i class="fas fa-crosshairs"></i> Selecting...';
            }
        },
        
        stopSelectionMode() {
            if (!this.state.selectingElement) return;
            
            this.state.selectingElement = false;
            document.body.style.cursor = 'default';
            
            const selectBtn = document.getElementById(this.config.NAMESPACE + 'select');
            if (selectBtn) {
                selectBtn.style.backgroundColor = '#3182ce';
                selectBtn.innerHTML = '<i class="fas fa-mouse-pointer"></i> Select';
            }
        },
        
        // Highlight mode toggle
        toggleHighlightMode() {
            this.state.highlightMode = !this.state.highlightMode;
            const btn = document.getElementById(this.config.NAMESPACE + 'highlight');
            if (btn) {
                btn.style.backgroundColor = this.state.highlightMode ? '#38a169' : '#3182ce';
                btn.innerHTML = this.state.highlightMode 
                    ? '<i class="fas fa-highlighter"></i> Highlighting' 
                    : '<i class="fas fa-highlighter"></i> Highlight';
            }
            this.showMessage(`Highlight mode is now ${this.state.highlightMode ? 'ON' : 'OFF'}.`, 'info');
        },
        
        // Comment preview
        updateCommentPreview() {
            const input = document.getElementById(this.config.NAMESPACE + 'comment');
            const preview = document.getElementById(this.config.NAMESPACE + 'preview');
            const previewText = document.getElementById(this.config.NAMESPACE + 'previewText');
            
            if (!input || !preview || !previewText) return;
            
            if (input.value.trim()) {
                let fullComment = input.value.trim();
                if (!fullComment.includes(this.config.DEFAULT_SUFFIX)) {
                    fullComment += this.config.DEFAULT_SUFFIX;
                }
                previewText.textContent = fullComment;
                preview.style.display = 'block';
            } else {
                preview.style.display = 'none';
            }
        },
        
        // Add comment
        addComment() {
            const commentBox = document.getElementById(this.config.NAMESPACE + 'comment');
            if (!commentBox || !this.state.selectedElement) {
                this.showMessage('Please select an element and enter a comment.', 'warning');
                return;
            }
            
            let commentText = commentBox.value.trim();
            if (!commentText) {
                this.showMessage('Please enter a comment before saving.', 'warning');
                return;
            }
            
            // Auto-append default suffix if not present
            if (!commentText.includes(this.config.DEFAULT_SUFFIX)) {
                commentText += this.config.DEFAULT_SUFFIX;
            }

            this.state.comments.push({
                element: {
                    tag: this.state.selectedElement.tagName.toLowerCase(),
                    id: this.state.selectedElement.id,
                    classes: Array.from(this.state.selectedElement.classList).join('.'),
                    text: this.state.selectedElement.textContent.trim().substring(0, 100)
                },
                comment: commentText,
                timestamp: new Date().toISOString(),
                path: this.getElementPath(this.state.selectedElement)
            });
            
            this.showMessage('Comment added successfully!', 'success');
            this.updateCommentCount();
            commentBox.value = '';
            this.updateCommentPreview();
            this.clearSelection();
        },
        
        // Copy comments to clipboard
        copyComments() {
            if (this.state.comments.length === 0) {
                this.showMessage('No comments to copy!', 'warning');
                return;
            }

            let formattedText = '=== DEVELOPMENT COMMENTS ===\n\n';
            this.state.comments.forEach((c, index) => {
                formattedText += `${index + 1}. ELEMENT INFO:\n`;
                formattedText += `   Tag: ${c.element.tag}\n`;
                formattedText += `   Path: ${c.path}\n`;
                if (c.element.id) formattedText += `   ID: #${c.element.id}\n`;
                if (c.element.classes) formattedText += `   Classes: .${c.element.classes.replace(/\./g, ' .')}\n`;
                if (c.element.text) formattedText += `   Text: ${c.element.text}...\n`;
                formattedText += `   COMMENT: ${c.comment}\n`;
                formattedText += `   Time: ${new Date(c.timestamp).toLocaleString()}\n`;
                formattedText += '-'.repeat(50) + '\n\n';
            });

            navigator.clipboard.writeText(formattedText)
                .then(() => this.showMessage('✅ Comments copied to clipboard!', 'success'))
                .catch(() => this.fallbackCopy(formattedText));
        },
        
        // Fallback copy method
        fallbackCopy(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            Object.assign(textarea.style, { position: 'fixed', opacity: '0' });
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                this.showMessage('✅ Comments copied! (fallback)', 'success');
            } catch (err) {
                this.showMessage('❌ Could not copy. Check console for text.', 'error');
                console.log('DEV TOOLBAR COMMENTS:\n\n' + text);
            }
            document.body.removeChild(textarea);
        },
        
        // Clear selection
        clearSelection() {
            if (this.state.selectedElement) {
                this.state.selectedElement.style.outline = '';
                this.state.selectedElement.style.outlineOffset = '';
            }
            this.state.selectedElement = null;
            
            const infoEl = document.getElementById(this.config.NAMESPACE + 'info');
            const commentBox = document.getElementById(this.config.NAMESPACE + 'comment');
            
            if (infoEl) infoEl.style.display = 'none';
            if (commentBox) commentBox.value = '';
            
            this.updateCommentPreview();
            this.stopSelectionMode();
        },
        
        // Clear all comments
        clearAll() {
            if (this.state.comments.length === 0) {
                this.showMessage('No comments to clear!', 'info');
                return;
            }
            
            if (confirm(`Clear all ${this.state.comments.length} comments?`)) {
                this.state.comments = [];
                this.updateCommentCount();
                this.clearSelection();
                this.showMessage('All comments cleared!', 'success');
            }
        },
        
        // Update comment count display
        updateCommentCount() {
            const countEl = document.getElementById(this.config.NAMESPACE + 'count');
            if (countEl) {
                countEl.textContent = this.state.comments.length;
            }
        },
        
        // Toggle toolbar visibility
        toggleToolbar() {
            this.state.toolbarVisible = !this.state.toolbarVisible;
            const toolbar = document.getElementById(this.config.TOOLBAR_ID);
            if (toolbar) {
                toolbar.style.display = this.state.toolbarVisible ? 'flex' : 'none';
            }
        },
        
        // Get element path
        getElementPath(el) {
            const path = [];
            while (el && el.nodeType === Node.ELEMENT_NODE) {
                let selector = el.nodeName.toLowerCase();
                if (el.id) {
                    selector += '#' + el.id;
                    path.unshift(selector);
                    break;
                } else {
                    let sib = el, nth = 1;
                    while (sib.previousElementSibling) {
                        sib = sib.previousElementSibling;
                        if (sib.nodeName.toLowerCase() === selector) nth++;
                    }
                    if (nth !== 1) selector += `:nth-of-type(${nth})`;
                }
                path.unshift(selector);
                el = el.parentNode;
            }
            return path.join(" > ");
        },
        
        // Show message (isolated notification)
        showMessage(message, type = 'info') {
            // Create isolated notification
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? '#38a169' : type === 'warning' ? '#d69e2e' : type === 'error' ? '#e53e3e' : '#3182ce'};
                color: white;
                padding: 12px 16px;
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: ${this.config.Z_INDEX + 1};
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                max-width: 300px;
                opacity: 1;
                transition: opacity 0.3s ease;
            `;
            notification.textContent = `[DEV] ${message}`;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 3 seconds
            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => DevToolbar.init());
    } else {
        DevToolbar.init();
    }
    
    // Expose for debugging (isolated namespace)
    window.IsolatedDevToolbar = DevToolbar;
    
})();