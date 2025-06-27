/**
 * PulseForge Bot Dashboard JavaScript
 * Handles real-time updates, chart management, and UI interactions
 */

// Global variables
let socket = null;
let charts = {};
let updateIntervals = {};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Initialize the dashboard
 */
function initializeDashboard() {
    // Initialize Socket.IO if available
    if (typeof io !== 'undefined') {
        initializeSocketIO();
    }
    
    // Initialize charts
    initializeCharts();
    
    // Set up periodic updates
    setupPeriodicUpdates();
    
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    console.log('PulseForge Dashboard initialized');
}

/**
 * Initialize Socket.IO connection
 */
function initializeSocketIO() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        updateConnectionStatus(true);
        
        // Request initial data
        socket.emit('request_stats');
        socket.emit('request_activity');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });
    
    socket.on('stats_update', function(data) {
        updateStats(data);
    });
    
    socket.on('new_activity', function(activity) {
        addNewActivity(activity);
    });
    
    socket.on('activity_update', function(data) {
        updateActivityList(data.activities);
    });
    
    socket.on('error', function(error) {
        console.error('Socket error:', error);
        showNotification('Connection error: ' + error.message, 'error');
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('bot-status');
    if (statusElement) {
        if (connected) {
            statusElement.textContent = 'Online';
            statusElement.className = 'text-success';
        } else {
            statusElement.textContent = 'Offline';
            statusElement.className = 'text-danger';
        }
    }
}

/**
 * Initialize all charts
 */
function initializeCharts() {
    initializeCommandChart();
    // Add more chart initializations as needed
}

/**
 * Initialize command usage chart
 */
function initializeCommandChart() {
    const ctx = document.getElementById('commandChart');
    if (!ctx) return;
    
    charts.commandChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Command Usage',
                data: [],
                backgroundColor: [
                    'rgba(13, 110, 253, 0.8)',
                    'rgba(25, 135, 84, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(13, 202, 240, 0.8)',
                    'rgba(108, 117, 125, 0.8)',
                    'rgba(111, 66, 193, 0.8)',
                    'rgba(214, 51, 132, 0.8)',
                    'rgba(253, 126, 20, 0.8)',
                    'rgba(32, 201, 151, 0.8)'
                ],
                borderColor: [
                    'rgba(13, 110, 253, 1)',
                    'rgba(25, 135, 84, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(13, 202, 240, 1)',
                    'rgba(108, 117, 125, 1)',
                    'rgba(111, 66, 193, 1)',
                    'rgba(214, 51, 132, 1)',
                    'rgba(253, 126, 20, 1)',
                    'rgba(32, 201, 151, 1)'
                ],
                borderWidth: 2,
                borderRadius: 4,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return 'Command: ' + context[0].label;
                        },
                        label: function(context) {
                            return 'Usage: ' + context.parsed.y + ' times';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                        borderDash: [5, 5]
                    },
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            return Number.isInteger(value) ? value : '';
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

/**
 * Update command chart with new data
 */
function updateCommandChart(data) {
    if (!charts.commandChart || !data) return;
    
    charts.commandChart.data.labels = data.labels || [];
    charts.commandChart.data.datasets[0].data = data.data || [];
    charts.commandChart.update('resize');
}

/**
 * Setup periodic updates for dashboard data
 */
function setupPeriodicUpdates() {
    // Update stats every 30 seconds
    updateIntervals.stats = setInterval(async () => {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const data = await response.json();
                updateStats(data);
            }
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }, 30000);
    
    // Update system info every 15 seconds
    updateIntervals.systemInfo = setInterval(async () => {
        try {
            const response = await fetch('/api/system-info');
            if (response.ok) {
                const data = await response.json();
                updateSystemInfo(data);
            }
        } catch (error) {
            console.error('Error updating system info:', error);
        }
    }, 15000);
    
    // Update command chart every 2 minutes
    updateIntervals.commandChart = setInterval(async () => {
        const days = document.querySelector('[x-model="chartDays"]')?.value || 7;
        try {
            const response = await fetch(`/api/command-usage?days=${days}`);
            if (response.ok) {
                const data = await response.json();
                updateCommandChart(data);
            }
        } catch (error) {
            console.error('Error updating command chart:', error);
        }
    }, 120000);
}

/**
 * Update stats display
 */
function updateStats(data) {
    const statsElements = {
        servers: document.querySelector('[x-text="stats.servers"]'),
        users: document.querySelector('[x-text="stats.users"]'),
        commands_today: document.querySelector('[x-text="stats.commands_today"]'),
        total_commands: document.querySelector('[x-text="stats.total_commands"]'),
        uptime: document.querySelector('[x-text="stats.uptime"]')
    };
    
    Object.keys(statsElements).forEach(key => {
        const element = statsElements[key];
        if (element && data[key] !== undefined) {
            // Add animation class
            element.classList.add('fade-in');
            element.textContent = data[key];
            
            // Remove animation class after animation completes
            setTimeout(() => {
                element.classList.remove('fade-in');
            }, 500);
        }
    });
    
    // Update last updated time
    const lastUpdatedElement = document.querySelector('[x-text="lastUpdated"]');
    if (lastUpdatedElement) {
        lastUpdatedElement.textContent = new Date().toLocaleTimeString();
    }
}

/**
 * Update system info display
 */
function updateSystemInfo(data) {
    // Update progress bars
    updateProgressBar('cpu_percent', data.cpu_percent);
    updateProgressBar('memory_percent', data.memory_percent);
    updateProgressBar('disk_percent', data.disk_percent);
    
    // Update text values
    const memoryUsedElement = document.querySelector('[x-text="systemInfo.memory_used + \' MB\'"]');
    if (memoryUsedElement && data.memory_used !== undefined) {
        memoryUsedElement.textContent = data.memory_used + ' MB';
    }
    
    const diskUsedElement = document.querySelector('[x-text="systemInfo.disk_used + \' GB\'"]');
    if (diskUsedElement && data.disk_used !== undefined) {
        diskUsedElement.textContent = data.disk_used + ' GB';
    }
}

/**
 * Update progress bar
 */
function updateProgressBar(type, value) {
    const progressBar = document.querySelector(`[\\:style="'width: ' + systemInfo.${type} + '%'"]`);
    const percentageSpan = document.querySelector(`[x-text="systemInfo.${type} + '%'"]`);
    
    if (progressBar && value !== undefined) {
        progressBar.style.width = value + '%';
        
        // Change color based on value
        progressBar.className = 'progress-bar';
        if (value > 80) {
            progressBar.classList.add('bg-danger');
        } else if (value > 60) {
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.add(type === 'cpu_percent' ? 'bg-primary' : 
                                      type === 'memory_percent' ? 'bg-success' : 'bg-warning');
        }
    }
    
    if (percentageSpan && value !== undefined) {
        percentageSpan.textContent = (typeof value === 'number' ? value.toFixed(1) : value) + '%';
    }
}

/**
 * Add new activity to the list
 */
function addNewActivity(activity) {
    const activityList = document.querySelector('.activity-list');
    if (!activityList) return;
    
    // Create activity element
    const activityElement = createActivityElement(activity);
    
    // Add to top of list
    const firstChild = activityList.firstElementChild;
    if (firstChild) {
        activityList.insertBefore(activityElement, firstChild);
    } else {
        activityList.appendChild(activityElement);
    }
    
    // Remove excess items (keep only 20)
    const activities = activityList.children;
    while (activities.length > 20) {
        activityList.removeChild(activities[activities.length - 1]);
    }
    
    // Add animation
    activityElement.classList.add('slide-in-right');
}

/**
 * Update entire activity list
 */
function updateActivityList(activities) {
    const activityList = document.querySelector('.activity-list');
    if (!activityList) return;
    
    // Clear existing activities
    activityList.innerHTML = '';
    
    // Add new activities
    activities.forEach(activity => {
        const activityElement = createActivityElement(activity);
        activityList.appendChild(activityElement);
    });
    
    // Show empty state if no activities
    if (activities.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'text-center py-4';
        emptyState.innerHTML = `
            <i class="fas fa-clock text-muted fa-2x mb-2"></i>
            <p class="text-muted mb-0">No recent activity</p>
        `;
        activityList.appendChild(emptyState);
    }
}

/**
 * Create activity element
 */
function createActivityElement(activity) {
    const div = document.createElement('div');
    div.className = 'border-bottom p-3 activity-item';
    
    const iconClass = getActivityIcon(activity.type);
    const timeString = formatTimestamp(activity.timestamp);
    
    div.innerHTML = `
        <div class="d-flex align-items-start">
            <div class="flex-shrink-0 me-3">
                <div class="bg-light rounded-circle p-2">
                    <i class="${iconClass} text-primary"></i>
                </div>
            </div>
            <div class="flex-grow-1">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${activity.command || activity.type}</h6>
                        <p class="text-muted small mb-0">
                            User: ${activity.user_id || 'Unknown'} | 
                            Server: ${activity.guild_id || 'Unknown'}
                        </p>
                    </div>
                    <small class="text-muted">${timeString}</small>
                </div>
            </div>
        </div>
    `;
    
    return div;
}

/**
 * Get icon for activity type
 */
function getActivityIcon(type) {
    const icons = {
        command: 'fas fa-terminal',
        member_join: 'fas fa-user-plus',
        member_leave: 'fas fa-user-minus',
        message: 'fas fa-comment',
        voice: 'fas fa-microphone',
        music: 'fas fa-music'
    };
    
    return icons[type] || 'fas fa-circle';
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // Less than 1 minute
        return 'Just now';
    } else if (diff < 3600000) { // Less than 1 hour
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m ago`;
    } else if (diff < 86400000) { // Less than 1 day
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    } else {
        return date.toLocaleDateString();
    }
}

/**
 * Initialize Bootstrap components
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', duration = 5000) {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 150);
        }
    }, duration);
}

/**
 * Utility function to debounce function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Cleanup function for when page is unloaded
 */
window.addEventListener('beforeunload', function() {
    // Clear all intervals
    Object.values(updateIntervals).forEach(interval => {
        clearInterval(interval);
    });
    
    // Disconnect socket
    if (socket) {
        socket.disconnect();
    }
    
    // Destroy charts
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
});

// Expose some functions globally for Alpine.js or other scripts
window.dashboardUtils = {
    formatTimestamp,
    showNotification,
    updateCommandChart,
    debounce
};
