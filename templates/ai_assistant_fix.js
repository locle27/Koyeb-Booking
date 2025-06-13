// ========== ENHANCED TEMPLATES MANAGEMENT FUNCTIONS ==========
// This will replace the templates management section in ai_assistant.html

let templates = [];
let isTemplatesLoaded = false;

// Enhanced load templates with proper error handling
async function loadTemplatesForTab() {
    const container = document.getElementById('templatesContainer');
    
    // Show loading with detailed status
    container.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Đang tải...</span>
            </div>
            <p class="mt-2 text-muted">Đang tải danh sách mẫu tin nhắn...</p>
            <small class="text-muted">Kết nối API templates...</small>
        </div>
    `;
    
    try {
        console.log('[TEMPLATES] Starting to load templates from API...');
        
        const response = await fetch('/api/templates', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        console.log('[TEMPLATES] Response status:', response.status);
        console.log('[TEMPLATES] Response headers:', response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('[TEMPLATES] Received data:', data);
        console.log('[TEMPLATES] Data type:', typeof data);
        console.log('[TEMPLATES] Is array:', Array.isArray(data));
        
        // Handle different response formats
        let templatesData = [];
        
        if (data.success === false) {
            // API returned error format
            console.error('[TEMPLATES] API returned error:', data.error);
            throw new Error(data.error || 'API returned error status');
        } else if (Array.isArray(data)) {
            // Direct array format
            templatesData = data;
        } else if (data.templates && Array.isArray(data.templates)) {
            // Wrapped in templates property
            templatesData = data.templates;
        } else {
            console.error('[TEMPLATES] Unexpected data format:', data);
            throw new Error('Invalid data format from API');
        }
        
        console.log('[TEMPLATES] Processing templates data:', templatesData);
        
        // Transform data for display
        templates = templatesData.map((item, index) => {
            console.log(`[TEMPLATES] Processing template ${index}:`, item);
            
            return {
                id: index.toString(),
                name: `${item.Category || 'Chung'} - ${item.Label || 'DEFAULT'}`,
                content: item.Message || item.Content || item.content || '',
                category: item.Category || 'Chung',
                label: item.Label || 'DEFAULT'
            };
        });
        
        console.log('[TEMPLATES] Transformed templates:', templates);
        
        isTemplatesLoaded = true;
        renderTemplatesForTab();
        
    } catch (error) {
        console.error('[TEMPLATES] Load error:', error);
        
        // Show detailed error message
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h6><i class="fas fa-exclamation-triangle"></i> Lỗi tải mẫu tin nhắn</h6>
                <p class="mb-2"><strong>Chi tiết lỗi:</strong> ${error.message}</p>
                <div class="mt-3">
                    <button class="btn btn-primary btn-sm me-2" onclick="retryLoadTemplates()">
                        <i class="fas fa-retry"></i> Thử lại
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="showTemplateDebugInfo()">
                        <i class="fas fa-info-circle"></i> Debug
                    </button>
                </div>
            </div>
        `;
        
        // Also show toast notification
        showError('Không thể tải mẫu tin nhắn: ' + error.message);
    }
}

// Retry function
async function retryLoadTemplates() {
    console.log('[TEMPLATES] Retrying template load...');
    templates = [];
    isTemplatesLoaded = false;
    await loadTemplatesForTab();
}

// Debug info function
async function showTemplateDebugInfo() {
    try {
        const response = await fetch('/api/templates/debug');
        const debugInfo = await response.json();
        
        const debugModal = document.createElement('div');
        debugModal.className = 'modal fade';
        debugModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Debug Templates</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" style="font-family: monospace; font-size: 0.9rem;">
                        <pre>${JSON.stringify(debugInfo, null, 2)}</pre>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(debugModal);
        const modal = new bootstrap.Modal(debugModal);
        modal.show();
        
    } catch (error) {
        showError('Debug info không khả dụng: ' + error.message);
    }
}

// Enhanced render function with better error handling
function renderTemplatesForTab() {
    const container = document.getElementById('templatesContainer');
    
    if (!templates || templates.length === 0) {
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="text-muted mb-3">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <h6>Chưa có mẫu tin nhắn nào</h6>
                    <p>Hãy thêm mẫu tin nhắn đầu tiên hoặc import từ Google Sheets</p>
                </div>
                <div class="d-flex gap-2 justify-content-center">
                    <button class="btn btn-primary btn-sm" onclick="showAddTemplateModal()">
                        <i class="fas fa-plus"></i> Thêm mẫu đầu tiên
                    </button>
                    <button class="btn btn-outline-success btn-sm" onclick="importFromSheets()">
                        <i class="fas fa-download"></i> Import từ Sheets
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
    try {
        // Group templates by category
        const groupedTemplates = {};
        templates.forEach(template => {
            const category = template.category || 'Khác';
            if (!groupedTemplates[category]) {
                groupedTemplates[category] = [];
            }
            groupedTemplates[category].push(template);
        });
        
        console.log('[TEMPLATES] Grouped templates:', groupedTemplates);
        
        // Render categories
        const categoriesHtml = Object.keys(groupedTemplates).map(category => {
            const categoryTemplates = groupedTemplates[category];
            const categoryId = category.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
            
            return `
                <div class="template-category mb-3 border rounded">
                    <div class="template-header p-3 bg-light rounded-top" onclick="toggleCategoryForTab('${categoryId}')" style="cursor: pointer;">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1 text-primary">
                                    <i class="fas fa-folder me-2"></i>${category}
                                </h6>
                                <small class="text-muted">
                                    <i class="fas fa-file-text me-1"></i>${categoryTemplates.length} mẫu tin nhắn
                                </small>
                            </div>
                            <i class="fas fa-chevron-down transition-all" id="icon-${categoryId}"></i>
                        </div>
                    </div>
                    <div class="template-content border-top" id="category-${categoryId}" style="display: none;">
                        <div class="p-3">
                            ${categoryTemplates.map(template => `
                                <div class="template-item border-start border-3 border-primary ms-2 ps-3 mb-3 bg-light rounded">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <div class="flex-grow-1">
                                            <h6 class="mb-1 text-secondary">
                                                <i class="fas fa-tag me-1"></i>
                                                ${template.label !== 'DEFAULT' ? template.label : 'Mặc định'}
                                            </h6>
                                            <small class="text-muted">Template ID: ${template.id}</small>
                                        </div>
                                        <div class="template-actions">
                                            <button class="btn btn-sm btn-primary me-1" onclick="useTemplateFromTab('${template.id}')" title="Sử dụng template">
                                                <i class="fas fa-paper-plane"></i>
                                            </button>
                                            <button class="btn btn-sm btn-outline-secondary" onclick="copyTemplateFromTab('${template.id}')" title="Copy nội dung">
                                                <i class="fas fa-copy"></i>
                                            </button>
                                        </div>
                                    </div>
                                    <div class="template-content-text bg-white p-3 rounded border" style="white-space: pre-wrap; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.5; max-height: 200px; overflow-y: auto;">
                                        ${template.content || 'Nội dung trống'}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = `
            <div class="templates-list">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <h6 class="mb-0">
                            <i class="fas fa-clipboard-list text-primary me-2"></i>
                            Tổng cộng: ${templates.length} mẫu tin nhắn
                        </h6>
                        <small class="text-muted">Trong ${Object.keys(groupedTemplates).length} danh mục</small>
                    </div>
                    <button class="btn btn-sm btn-outline-primary" onclick="expandAllCategories()">
                        <i class="fas fa-expand-arrows-alt"></i> Mở rộng tất cả
                    </button>
                </div>
                ${categoriesHtml}
            </div>
        `;
        
        console.log('[TEMPLATES] Render completed successfully');
        
    } catch (error) {
        console.error('[TEMPLATES] Render error:', error);
        container.innerHTML = `
            <div class="alert alert-warning" role="alert">
                <h6><i class="fas fa-exclamation-triangle"></i> Lỗi hiển thị templates</h6>
                <p>Đã tải được dữ liệu nhưng không thể hiển thị: ${error.message}</p>
                <button class="btn btn-sm btn-primary" onclick="retryLoadTemplates()">
                    <i class="fas fa-retry"></i> Thử lại
                </button>
            </div>
        `;
    }
}

// Enhanced toggle function
function toggleCategoryForTab(categoryId) {
    try {
        const content = document.getElementById(`category-${categoryId}`);
        const icon = document.getElementById(`icon-${categoryId}`);
        
        if (!content || !icon) {
            console.error('[TEMPLATES] Toggle elements not found:', categoryId);
            return;
        }
        
        if (content.style.display === 'block') {
            content.style.display = 'none';
            icon.className = 'fas fa-chevron-down transition-all';
        } else {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up transition-all';
        }
    } catch (error) {
        console.error('[TEMPLATES] Toggle error:', error);
    }
}

// Expand all categories
function expandAllCategories() {
    try {
        const allContent = document.querySelectorAll('[id^="category-"]');
        const allIcons = document.querySelectorAll('[id^="icon-"]');
        
        allContent.forEach(content => {
            content.style.display = 'block';
        });
        
        allIcons.forEach(icon => {
            icon.className = 'fas fa-chevron-up transition-all';
        });
        
        showSuccess('✅ Đã mở rộng tất cả danh mục');
    } catch (error) {
        console.error('[TEMPLATES] Expand all error:', error);
    }
}

// Enhanced template actions
function useTemplateFromTab(id) {
    try {
        const template = templates.find(t => t.id === id);
        if (!template) {
            showError('Không tìm thấy template với ID: ' + id);
            return;
        }
        
        if (!template.content) {
            showError('Template này không có nội dung');
            return;
        }
        
        copyToClipboard(template.content);
        showSuccess(`✅ Đã copy "${template.name}" để sử dụng!`);
        
    } catch (error) {
        console.error('[TEMPLATES] Use template error:', error);
        showError('Lỗi khi sử dụng template: ' + error.message);
    }
}

function copyTemplateFromTab(id) {
    try {
        const template = templates.find(t => t.id === id);
        if (!template) {
            showError('Không tìm thấy template với ID: ' + id);
            return;
        }
        
        if (!template.content) {
            showError('Template này không có nội dung để copy');
            return;
        }
        
        copyToClipboard(template.content);
        showSuccess(`📋 Đã copy nội dung "${template.label}"!`);
        
    } catch (error) {
        console.error('[TEMPLATES] Copy template error:', error);
        showError('Lỗi khi copy template: ' + error.message);
    }
}

// Enhanced event listener for templates tab
document.addEventListener('DOMContentLoaded', function() {
    const templatesTab = document.getElementById('templates-tab');
    if (templatesTab) {
        templatesTab.addEventListener('click', function() {
            console.log('[TEMPLATES] Templates tab clicked, loaded:', isTemplatesLoaded);
            if (!isTemplatesLoaded) {
                loadTemplatesForTab();
            }
        });
    }
});

// Test connection function
async function testTemplatesConnection() {
    try {
        showLoading(true);
        
        const response = await fetch('/api/templates/debug');
        const result = await response.json();
        
        console.log('[TEMPLATES] Debug result:', result);
        
        if (result.file_exists) {
            showSuccess('✅ Kết nối templates API thành công!');
            if (result.templates_count > 0) {
                showSuccess(`📋 Tìm thấy ${result.templates_count} templates`);
            }
        } else {
            showError('⚠️ File templates không tồn tại');
        }
        
    } catch (error) {
        console.error('[TEMPLATES] Test connection error:', error);
        showError('❌ Lỗi kết nối: ' + error.message);
    } finally {
        showLoading(false);
    }
}

console.log('[TEMPLATES] Enhanced templates management loaded');
