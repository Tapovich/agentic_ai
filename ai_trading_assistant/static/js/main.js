/**
 * Main JavaScript File for AI Trading Assistant
 * This file contains all client-side JavaScript logic
 * using vanilla JavaScript (no frameworks)
 */

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Trading Assistant - JavaScript loaded');
    
    // Initialize dashboard if we're on the dashboard page
    if (document.getElementById('refreshPredictionBtn')) {
        initDashboard();
    }
});


// ============================================
// DASHBOARD FUNCTIONALITY
// ============================================

function initDashboard() {
    console.log('Initializing dashboard...');
    
    // Get Prediction Button
    const refreshBtn = document.getElementById('refreshPredictionBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', getPrediction);
    }
    
    // Trading Buttons
    const buyBtn = document.getElementById('buyBtn');
    const sellBtn = document.getElementById('sellBtn');
    
    if (buyBtn) {
        buyBtn.addEventListener('click', () => executeTrade('BUY'));
    }
    
    if (sellBtn) {
        sellBtn.addEventListener('click', () => executeTrade('SELL'));
    }
    
    // Quantity Input - Calculate estimated total
    const quantityInput = document.getElementById('tradeQuantity');
    if (quantityInput) {
        quantityInput.addEventListener('input', updateEstimatedTotal);
    }
    
    // Symbol Select - Update price display
    const symbolSelect = document.getElementById('tradeSymbol');
    if (symbolSelect) {
        symbolSelect.addEventListener('change', updatePriceDisplay);
    }
}


// ============================================
// AI PREDICTION
// ============================================

async function getPrediction() {
    console.log('Getting AI prediction...');
    
    const contentDiv = document.getElementById('predictionContent');
    const loadingDiv = document.getElementById('predictionLoading');
    const button = document.getElementById('refreshPredictionBtn');
    
    // Show loading state
    contentDiv.style.display = 'none';
    loadingDiv.style.display = 'block';
    button.disabled = true;
    button.textContent = '⏳ Loading...';
    
    try {
        // Call API to get prediction
        const response = await fetch('/api/predict');
        const data = await response.json();
        
        if (data.success) {
            // Display prediction
            displayPrediction(data);
            showNotification('Prediction generated successfully!', 'success');
        } else {
            throw new Error(data.error || 'Prediction failed');
        }
    } catch (error) {
        console.error('Error getting prediction:', error);
        showNotification('Failed to get prediction: ' + error.message, 'error');
        contentDiv.innerHTML = `
            <div class="prediction-empty">
                <p style="color: var(--danger-color);">❌ Failed to generate prediction</p>
                <p>${error.message}</p>
            </div>
        `;
    } finally {
        // Hide loading state
        loadingDiv.style.display = 'none';
        contentDiv.style.display = 'block';
        button.disabled = false;
        button.textContent = '🔄 Get New Prediction';
    }
}

function displayPrediction(data) {
    const contentDiv = document.getElementById('predictionContent');
    
    const directionClass = data.direction === 'UP' ? 'up' : 'down';
    const now = new Date().toLocaleString();
    
    contentDiv.innerHTML = `
        <div class="prediction-result">
            <div class="prediction-direction ${directionClass}">
                ${data.direction}
            </div>
            <div class="prediction-confidence">
                <div class="confidence-label">Confidence</div>
                <div class="confidence-value">${data.confidence_pct}%</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${data.confidence_pct}%"></div>
                </div>
            </div>
            <div class="prediction-meta">
                <small>Generated: ${now}</small><br>
                <small>Symbol: ${data.symbol} | Price: $${data.current_price.toLocaleString()}</small>
            </div>
        </div>
    `;
}


// ============================================
// TRADING FUNCTIONALITY
// ============================================

async function executeTrade(side) {
    console.log(`Executing ${side} trade...`);
    
    const symbol = document.getElementById('tradeSymbol').value;
    const quantity = parseFloat(document.getElementById('tradeQuantity').value);
    
    // Validation
    if (!quantity || quantity <= 0) {
        showNotification('Please enter a valid quantity', 'error');
        return;
    }
    
    // This would call your trading API when implemented
    showNotification(
        `Trading feature coming soon! You tried to ${side} ${quantity} ${symbol}`,
        'info'
    );
    
    // TODO: Implement actual trading API call
    // const response = await fetch('/api/trade', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({ symbol, side, quantity })
    // });
}

function updateEstimatedTotal() {
    const quantity = parseFloat(document.getElementById('tradeQuantity').value) || 0;
    const priceText = document.getElementById('currentPrice').textContent;
    
    // Extract price from formatted string (e.g., "$45,000" -> 45000)
    const price = parseFloat(priceText.replace(/[$,]/g, '')) || 0;
    
    const total = quantity * price;
    document.getElementById('estimatedTotal').textContent = 
        '$' + total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function updatePriceDisplay() {
    // This would fetch real price from API when implemented
    // For now, just a placeholder
    const symbol = document.getElementById('tradeSymbol').value;
    
    // Mock prices
    const prices = {
        'BTCUSDT': 45600,
        'ETHUSDT': 2800,
        'BNBUSDT': 420
    };
    
    const price = prices[symbol] || 0;
    document.getElementById('currentPrice').textContent = 
        '$' + price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    // Update estimated total
    updateEstimatedTotal();
}


// ============================================
// NOTIFICATION SYSTEM
// ============================================

function showNotification(message, type = 'info') {
    // Get or create container
    const container = document.querySelector('.flash-container') || createNotificationContainer();
    
    // Remove all existing notifications first (only show one at a time)
    const existingNotifications = container.querySelectorAll('.notification');
    existingNotifications.forEach(notif => {
        notif.remove();
    });
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add to flash container
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.className = 'flash-container';
    document.querySelector('.main-content').insertBefore(
        container, 
        document.querySelector('.main-content').firstChild
    );
    return container;
}


// ============================================
// UTILITY FUNCTIONS
// ============================================

// Format currency
function formatCurrency(value) {
    return '$' + value.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Format percentage
function formatPercentage(value) {
    const sign = value >= 0 ? '+' : '';
    return sign + value.toFixed(2) + '%';
}

// Format large numbers
function formatNumber(value) {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(2) + 'M';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(2) + 'K';
    }
    return value.toFixed(2);
}

