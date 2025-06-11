// dashboard.js - Optimized dashboard JavaScript functionality

// ==================== GLOBAL VARIABLES ====================
let activeReminders = JSON.parse(localStorage.getItem('activeReminders') || '[]');
let completedReminders = JSON.parse(localStorage.getItem('completedReminders') || '[]');
let reminderCheckInterval = null;
let currentBookingId = '';
let currentTotalAmount = 0;
let currentCommission = 0;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded, initializing...');
    
    // Initialize reminder system
    initializeReminderSystem();
    
    // Initialize charts
    initializeCharts();
});

function initializeReminderSystem() {
    // Set default reminder time to 1 hour from now
    const now = new Date();
    now.setHours(now.getHours() + 1);
    const defaultTime = now.toISOString().slice(0, 16);
    const reminderInput = document.getElementById('reminderDateTime');
    if (reminderInput) {
        reminderInput.value = defaultTime;
    }
    
    // Load existing reminders and start checker
    loadActiveReminders();
    startReminderChecker();
}

function initializeCharts() {
    // Monthly Revenue Chart
    if (typeof monthlyRevenueChartData !== 'undefined' && monthlyRevenueChartData) {
        createMonthlyRevenueChart(monthlyRevenueChartData);
    }
    
    // Collector Chart
    if (typeof collectorChartData !== 'undefined' && collectorChartData) {
        createCollectorChart(collectorChartData);
    }
}

// ==================== CHART FUNCTIONS ====================
function createMonthlyRevenueChart(chartData) {
    if (chartData && typeof chartData === 'object' && 
        Object.keys(chartData).length > 0 && chartData.data && chartData.layout) {
        try {
            Plotly.newPlot('monthlyRevenueChart', chartData.data, chartData.layout, {
                responsive: true,
                displayModeBar: false
            });
            console.log('Monthly revenue chart rendered successfully');
        } catch (error) {
            console.error('Error rendering monthly revenue chart:', error);
            document.getElementById('monthlyRevenueChart').innerHTML = 
                '<div class="alert alert-danger">Lỗi hiển thị biểu đồ: ' + error.message + '</div>';
        }
    } else {
        console.log('No monthly revenue chart data available');
        document.getElementById('monthlyRevenueChart').innerHTML = 
            '<div class="text-center py-5"><i class="fas fa-chart-line fa-3x text-muted mb-3"></i><p class="text-muted">Không có dữ liệu để hiển thị biểu đồ</p></div>';
    }
}

function createCollectorChart(chartData) {
    if (chartData && typeof chartData === 'object' && 
        Object.keys(chartData).length > 0 && chartData.data && 
        Array.isArray(chartData.data) && chartData.data.length > 0 &&
        chartData.data[0].values && Array.isArray(chartData.data[0].values) &&
        chartData.data[0].values.length > 0 && chartData.layout) {
        try {
            Plotly.newPlot('collectorChart', chartData.data, chartData.layout, {
                responsive: true,
                displayModeBar: false
            });
            console.log('Collector chart rendered successfully');
        } catch (error) {
            console.error('Error rendering collector chart:', error);
            document.getElementById('collectorChart').innerHTML = 
                '<div class="alert alert-danger">Lỗi hiển thị biểu đồ: ' + error.message + '</div>';
        }
    } else {
        console.log('No collector chart data available or empty values');
        document.getElementById('collectorChart').innerHTML = 
            '<div class="text-center py-5"><i class="fas fa-chart-pie fa-3x text-muted mb-3"></i><p class="text-muted">Không có dữ liệu người thu tiền</p></div>';
    }
}

// ==================== OVERDUE GUESTS FUNCTIONS ====================
function toggleMoreOverdue() {
    const moreOverdue = document.getElementById('moreOverdueGuests');
    const button = event.target;
    
    if (moreOverdue.style.display === 'none') {
        moreOverdue.style.display = 'block';
        button.innerHTML = '<i class="fas fa-chevron-up me-1"></i> Thu gọn';
    } else {
        moreOverdue.style.display = 'none';
        const overdueCount = document.querySelectorAll('[id^="overdue_guest_"]').length - 3;
        button.innerHTML = `<i class="fas fa-chevron-down me-1"></i> Xem thêm ${overdueCount} khách`;
    }
}

// ==================== OVERCROWDED DAYS FUNCTIONS ====================
function toggleOvercrowdedDetails() {
    const details = document.getElementById('overcrowdedDetails');
    const toggleText = document.getElementById('overcrowdToggleText');
    
    if (details.style.display === 'none' || details.style.display === '') {
        details.style.display = 'block';
        toggleText.textContent = 'Ẩn chi tiết';
    } else {
        details.style.display = 'none';
        toggleText.textContent = 'Chi tiết';
    }
}

function showDayDetails(date, guestCount, guestNames, bookingIds) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-warning text-dark">
                    <h5 class="modal-title">
                        <i class="fas fa-users me-2"></i>Chi tiết ngày quá tải: ${date}
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-warning">
                        <strong>⚠️ Cảnh báo:</strong> Ngày này có ${guestCount} khách check-in (vượt quá giới hạn 4 phòng)
                    </div>
                    
                    <h6 class="mb-3">Danh sách ${guestCount} khách check-in:</h6>
                    <div class="row">
                        ${guestNames.map((name, index) => `
                            <div class="col-md-6 mb-2">
                                <div class="card border-left-warning">
                                    <div class="card-body py-2 px-3">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <div class="fw-bold">${name || 'N/A'}</div>
                                                <small class="text-muted">ID: ${bookingIds[index] || 'N/A'}</small>
                                            </div>
                                            <span class="badge bg-warning">#${index + 1}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="mt-3 p-3 bg-light rounded">
                        <h6 class="text-primary mb-2">💡 Gợi ý xử lý:</h6>
                        <ul class="mb-0 small">
                            <li>Kiểm tra xem có thể sắp xếp lại lịch check-in không</li>
                            <li>Liên hệ một số khách để thảo luận về check-in sớm/muộn</li>
                            <li>Chuẩn bị thêm nhân viên và tiện nghi cho ngày này</li>
                            <li>Xem xét việc upgrade phòng hoặc hỗ trợ đặc biệt</li>
                        </ul>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Đóng</button>
                    <button type="button" class="btn btn-primary" onclick="goToCalendar('${date}')">
                        <i class="fas fa-calendar me-1"></i>Xem trong lịch
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
}

function goToCalendar(dateStr) {
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    window.open(`/calendar/${year}/${month}`, '_blank');
}

// ==================== PAYMENT COLLECTION FUNCTIONS ====================
function openCollectModal(bookingId, guestName, totalAmount, commission = 0) {
    currentBookingId = bookingId;
    currentTotalAmount = totalAmount;
    currentCommission = commission || 0;
    
    document.getElementById('modalGuestName').textContent = guestName;
    document.getElementById('modalBookingId').textContent = bookingId;
    document.getElementById('modalTotalAmount').textContent = totalAmount.toLocaleString('vi-VN') + 'đ';
    
    const commissionElement = document.getElementById('modalCommissionAmount');
    if (currentCommission > 0) {
        commissionElement.textContent = currentCommission.toLocaleString('vi-VN') + 'đ';
        commissionElement.className = 'fw-bold text-warning fs-6';
    } else {
        commissionElement.textContent = 'Chưa có thông tin';
        commissionElement.className = 'text-muted fs-6';
    }
    
    document.getElementById('collectedAmount').value = totalAmount;
    document.getElementById('collectorName').value = '';
    document.getElementById('paymentNote').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('collectPaymentModal'));
    modal.show();
}

async function collectPayment() {
    const collectedAmount = parseInt(document.getElementById('collectedAmount').value) || 0;
    const collectorName = document.getElementById('collectorName').value;
    const paymentNote = document.getElementById('paymentNote').value;
    
    if (!collectorName) {
        alert('Vui lòng chọn người thu tiền!');
        return;
    }
    
    if (collectedAmount <= 0) {
        alert('Vui lòng nhập số tiền hợp lệ!');
        return;
    }
    
    if (collectedAmount > currentTotalAmount) {
        if (!confirm(`Số tiền thu (${collectedAmount.toLocaleString('vi-VN')}đ) lớn hơn số tiền cần thu (${currentTotalAmount.toLocaleString('vi-VN')}đ). Bạn có chắc chắn?`)) {
            return;
        }
    }
    
    const confirmBtn = document.getElementById('confirmCollectBtn');
    const originalText = confirmBtn.innerHTML;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Đang xử lý...';
    confirmBtn.disabled = true;
    
    try {
        const response = await fetch('/api/collect_payment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                booking_id: currentBookingId,
                collected_amount: collectedAmount,
                collector_name: collectorName,
                payment_note: paymentNote
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('collectPaymentModal'));
            modal.hide();
            
            showSuccessAlert(`Thu tiền thành công! Đã thu ${collectedAmount.toLocaleString('vi-VN')}đ từ khách ${document.getElementById('modalGuestName').textContent}`);
            
            setTimeout(() => { window.location.reload(); }, 2000);
        } else {
            alert('Lỗi: ' + (result.message || 'Không thể thu tiền'));
        }
    } catch (error) {
        console.error('Payment collection error:', error);
        alert('Lỗi kết nối. Vui lòng thử lại!');
    } finally {
        confirmBtn.innerHTML = originalText;
        confirmBtn.disabled = false;
    }
}

// ==================== REMINDER FUNCTIONS ====================
function addReminder() {
    const text = document.getElementById('reminderText').value.trim();
    const dateTime = document.getElementById('reminderDateTime').value;
    const priority = document.getElementById('reminderPriority').value;
    
    if (!text) {
        alert('Vui lòng nhập nội dung nhắc hẹn!');
        return;
    }
    
    if (!dateTime) {
        alert('Vui lòng chọn thời gian nhắc hẹn!');
        return;
    }
    
    const reminderTime = new Date(dateTime);
    const now = new Date();
    
    if (reminderTime <= now) {
        alert('Thời gian nhắc hẹn phải lớn hơn thời gian hiện tại!');
        return;
    }
    
    const reminder = {
        id: 'reminder_' + Date.now(),
        text: text,
        dateTime: dateTime,
        timestamp: reminderTime.getTime(),
        priority: priority,
        created: now.toISOString(),
        triggered: false,
        completed: false,
        completedAt: null
    };
    
    activeReminders.push(reminder);
    localStorage.setItem('activeReminders', JSON.stringify(activeReminders));
    
    // Clear form
    document.getElementById('reminderText').value = '';
    document.getElementById('reminderDateTime').value = '';
    document.getElementById('reminderPriority').value = 'normal';
    
    loadActiveReminders();
    showReminderSuccess(`Đã thêm nhắc hẹn: "${text}" lúc ${formatDateTime(reminderTime)}`);
}

function loadActiveReminders() {
    const remindersList = document.getElementById('remindersList');
    const activeRemindersDiv = document.getElementById('activeReminders');
    
    // Cleanup old reminders
    const now = new Date().getTime();
    activeReminders = activeReminders.filter(reminder => 
        reminder.timestamp > (now - 3600000) || !reminder.triggered || !reminder.completed
    );
    
    localStorage.setItem('activeReminders', JSON.stringify(activeReminders));
    
    const pendingReminders = activeReminders.filter(r => !r.completed);
    const recentCompleted = activeReminders.filter(r => r.completed);
    
    if (activeReminders.length === 0) {
        activeRemindersDiv.style.display = 'none';
        return;
    }
    
    activeRemindersDiv.style.display = 'block';
    remindersList.innerHTML = '';
    
    if (pendingReminders.length > 0 && recentCompleted.length > 0) {
        remindersList.innerHTML = `
            <div class="col-12 mb-2">
                <h6 class="text-primary mb-0"><i class="fas fa-clock me-1"></i>Đang chờ (${pendingReminders.length})</h6>
            </div>
        `;
    }
    
    pendingReminders.sort((a, b) => a.timestamp - b.timestamp).forEach(reminder => {
        displayReminderCard(reminder, remindersList);
    });
    
    if (recentCompleted.length > 0) {
        const completedHeader = document.createElement('div');
        completedHeader.className = 'col-12 mt-3 mb-2';
        completedHeader.innerHTML = `
            <hr class="my-2">
            <h6 class="text-success mb-0">
                <i class="fas fa-check-circle me-1"></i>Đã hoàn thành (${recentCompleted.length})
                <button class="btn btn-sm btn-outline-secondary ms-2" onclick="toggleCompletedSection()">
                    <i class="fas fa-eye"></i> <span id="toggleCompletedText">Ẩn</span>
                </button>
            </h6>
        `;
        remindersList.appendChild(completedHeader);
        
        const completedContainer = document.createElement('div');
        completedContainer.id = 'completedRemindersSection';
        completedContainer.className = 'col-12';
        completedContainer.innerHTML = '<div class="row" id="completedRemindersList"></div>';
        remindersList.appendChild(completedContainer);
        
        const completedList = document.getElementById('completedRemindersList');
        recentCompleted.sort((a, b) => b.completedAt - a.completedAt).forEach(reminder => {
            displayReminderCard(reminder, completedList, true);
        });
    }
}

function displayReminderCard(reminder, container, isCompleted = false) {
    const priorityColors = { normal: 'primary', important: 'warning', urgent: 'danger' };
    const priorityIcons = { normal: '🔵', important: '🟡', urgent: '🔴' };
    
    const timeRemaining = getTimeRemaining(reminder.timestamp);
    const isPastDue = reminder.timestamp < Date.now() && !reminder.completed;
    
    const reminderCard = document.createElement('div');
    reminderCard.className = 'col-md-6 col-lg-4 mb-2';
    reminderCard.innerHTML = `
        <div class="card border-${priorityColors[reminder.priority]} ${isCompleted ? 'bg-light opacity-75' : ''} ${isPastDue ? 'border-danger' : ''}">
            <div class="card-body py-2 px-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            <input type="checkbox" class="form-check-input me-2" 
                                   id="reminder_${reminder.id}" 
                                   ${reminder.completed ? 'checked disabled' : ''} 
                                   onchange="toggleReminderCompletion('${reminder.id}')"
                                   title="${reminder.completed ? 'Đã hoàn thành' : 'Đánh dấu hoàn thành'}">
                            <span class="me-1">${priorityIcons[reminder.priority]}</span>
                            <small class="text-muted">${formatDateTime(new Date(reminder.timestamp))}</small>
                        </div>
                        <div class="fw-bold ${isPastDue ? 'text-danger' : ''} ${reminder.completed ? 'text-decoration-line-through text-muted' : ''}" style="font-size: 0.9rem;">
                            ${reminder.text}
                        </div>
                        <small class="text-${isPastDue ? 'danger' : reminder.completed ? 'success' : 'info'}">
                            ${reminder.completed ? 
                                `✅ Hoàn thành: ${formatDateTime(new Date(reminder.completedAt))}` :
                                isPastDue ? '⏰ Đã quá hạn' : `⏱️ ${timeRemaining}`
                            }
                        </small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="removeReminder('${reminder.id}')" title="Xóa nhắc hẹn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(reminderCard);
}

function removeReminder(reminderId) {
    activeReminders = activeReminders.filter(reminder => reminder.id !== reminderId);
    localStorage.setItem('activeReminders', JSON.stringify(activeReminders));
    loadActiveReminders();
    showReminderSuccess('Đã xóa nhắc hẹn');
}

function startReminderChecker() {
    if (reminderCheckInterval) {
        clearInterval(reminderCheckInterval);
    }
    
    reminderCheckInterval = setInterval(checkForDueReminders, 30000);
    checkForDueReminders();
}

function checkForDueReminders() {
    const now = Date.now();
    const dueReminders = activeReminders.filter(reminder => 
        reminder.timestamp <= now && !reminder.triggered
    );
    
    dueReminders.forEach(reminder => {
        reminder.triggered = true;
        showReminderNotification(reminder);
        playNotificationSound();
    });
    
    if (dueReminders.length > 0) {
        localStorage.setItem('activeReminders', JSON.stringify(activeReminders));
        loadActiveReminders();
    }
}

function showReminderNotification(reminder) {
    const notificationDiv = document.getElementById('reminderNotifications');
    const messageDiv = document.getElementById('reminderMessage');
    const priorityIcons = { normal: '🔵', important: '🟡', urgent: '🔴' };
    
    messageDiv.innerHTML = `
        ${priorityIcons[reminder.priority]} <strong>${reminder.text}</strong><br>
        <small>Thời gian: ${formatDateTime(new Date(reminder.timestamp))}</small>
    `;
    
    notificationDiv.style.display = 'block';
    
    if (reminder.priority === 'normal') {
        setTimeout(() => { dismissReminder(); }, 10000);
    }
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function dismissReminder() {
    document.getElementById('reminderNotifications').style.display = 'none';
}

function toggleReminderCompletion(reminderId) {
    const reminderIndex = activeReminders.findIndex(r => r.id === reminderId);
    if (reminderIndex === -1) return;
    
    const reminder = activeReminders[reminderIndex];
    
    if (!reminder.completed) {
        reminder.completed = true;
        reminder.completedAt = Date.now();
        
        playCompletionSound();
        showReminderSuccess(`✅ Đã hoàn thành: "${reminder.text}"`);
        
        completedReminders.push({...reminder});
        localStorage.setItem('completedReminders', JSON.stringify(completedReminders));
    } else {
        reminder.completed = false;
        reminder.completedAt = null;
    }
    
    localStorage.setItem('activeReminders', JSON.stringify(activeReminders));
    loadActiveReminders();
}

function toggleCompletedSection() {
    const section = document.getElementById('completedRemindersSection');
    const toggleText = document.getElementById('toggleCompletedText');
    
    if (section.style.display === 'none') {
        section.style.display = 'block';
        toggleText.textContent = 'Ẩn';
    } else {
        section.style.display = 'none';
        toggleText.textContent = 'Hiện';
    }
}

// ==================== UTILITY FUNCTIONS ====================
function formatDateTime(date) {
    return date.toLocaleString('vi-VN', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function getTimeRemaining(timestamp) {
    const now = Date.now();
    const diff = timestamp - now;
    
    if (diff < 0) return 'Đã quá hạn';
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} ngày ${hours % 24} giờ`;
    if (hours > 0) return `${hours} giờ ${minutes % 60} phút`;
    return `${minutes} phút`;
}

function playNotificationSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.log('Could not play notification sound:', error);
    }
}

function playCompletionSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.value = 1000;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
    } catch (error) {
        console.log('Could not play completion sound:', error);
    }
}

function showReminderSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'position-fixed top-0 end-0 m-3 alert alert-success alert-dismissible';
    toast.style.zIndex = '9999';
    toast.innerHTML = `<i class="fas fa-check-circle"></i> ${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function showSuccessAlert(message) {
    const successAlert = document.createElement('div');
    successAlert.className = 'alert alert-success alert-dismissible fade show position-fixed';
    successAlert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    successAlert.innerHTML = `
        <strong>✅ ${message}</strong>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(successAlert);
    
    setTimeout(() => {
        if (successAlert.parentNode) {
            successAlert.remove();
        }
    }, 5000);
}
