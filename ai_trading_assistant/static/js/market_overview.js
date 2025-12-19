/**
 * Market Overview with Live Prices
 * ===================================
 * Features:
 * - Live prices from CoinMarketCap API
 * - Auto-refresh every 30 seconds
 * - Hover tooltips with detailed token information
 * - Price change animations
 * - Beautiful responsive design
 */

// ============================================
// STATE MANAGEMENT
// ============================================

let marketData = {};  // Store current market data
let previousPrices = {};  // Track previous prices for animation
let autoRefreshInterval = null;  // Auto-refresh timer
let currentTooltip = null;  // Active tooltip element
let tooltipTimeout = null;  // Tooltip show/hide delay

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🌐 Market Overview initializing...');
    
    // Load initial market data
    loadMarketData();
    
    // Set up auto-refresh (every 30 seconds)
    startAutoRefresh();
    
    // Refresh button
    const refreshBtn = document.getElementById('refreshMarketBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadMarketData();
        });
    }
    
    // Create tooltip element
    createTooltipElement();
    
    console.log('✅ Market Overview initialized');
});

// ============================================
// DATA LOADING
// ============================================

async function loadMarketData() {
    const loadingEl = document.getElementById('marketLoading');
    const tableEl = document.getElementById('marketTableContainer');
    const errorEl = document.getElementById('marketError');
    
    // Show loading state
    if (loadingEl) loadingEl.style.display = 'block';
    if (tableEl) tableEl.style.display = 'none';
    if (errorEl) errorEl.style.display = 'none';
    
    try {
        console.log('📊 Fetching market data...');
        
        const response = await fetch('/api/market/top?limit=20');
        const data = await response.json();
        
        if (data.success && data.data) {
            marketData = data.data;
            console.log(`✅ Loaded ${marketData.length} coins`);
            
            // Display market data
            displayMarketData(marketData);
            
            // Update timestamp
            updateTimestamp();
            
            // Hide loading, show table
            if (loadingEl) loadingEl.style.display = 'none';
            if (tableEl) tableEl.style.display = 'block';
            
        } else {
            throw new Error(data.error || 'Failed to load market data');
        }
        
    } catch (error) {
        console.error('❌ Error loading market data:', error);
        
        // Show error state
        if (loadingEl) loadingEl.style.display = 'none';
        if (errorEl) {
            errorEl.style.display = 'block';
            const errorMsgEl = document.getElementById('marketErrorMsg');
            if (errorMsgEl) {
                errorMsgEl.textContent = error.message;
            }
        }
    }
}

// ============================================
// DISPLAY MARKET DATA
// ============================================

function displayMarketData(coins) {
    const tbody = document.getElementById('marketTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    coins.forEach(coin => {
        const row = createCoinRow(coin);
        tbody.appendChild(row);
    });
}

function createCoinRow(coin) {
    const row = document.createElement('tr');
    row.dataset.symbol = coin.symbol;
    
    // Store previous price for animation
    const prevPrice = previousPrices[coin.symbol];
    previousPrices[coin.symbol] = coin.price;
    
    // Build row HTML
    row.innerHTML = `
        <td style="text-align: center; color: #94a3b8;">${coin.rank}</td>
        <td>
            <div class="coin-name-cell">
                <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/${getCoinId(coin.symbol)}.png" 
                     alt="${coin.name}" 
                     class="coin-logo"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2232%22 height=%2232%22><rect width=%2232%22 height=%2232%22 fill=%22%2394a3b8%22/><text x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22white%22 font-size=%2212%22>${coin.symbol[0]}</text></svg>'">
                <div class="coin-info">
                    <div class="coin-name">${coin.name}</div>
                    <div class="coin-symbol">${coin.symbol}</div>
                </div>
            </div>
        </td>
        <td class="price-cell" data-symbol="${coin.symbol}">$${formatPrice(coin.price)}</td>
        <td>${formatPriceChange(coin.percent_change_1h)}</td>
        <td>${formatPriceChange(coin.percent_change_24h)}</td>
        <td>${formatPriceChange(coin.percent_change_7d)}</td>
        <td class="market-cap-value">$${formatLargeNumber(coin.market_cap)}</td>
        <td class="volume-value">$${formatLargeNumber(coin.volume_24h)}</td>
    `;
    
    // Animate price change
    if (prevPrice !== undefined && prevPrice !== coin.price) {
        const priceCell = row.querySelector('.price-cell');
        if (priceCell) {
            if (coin.price > prevPrice) {
                priceCell.classList.add('flash-green');
            } else {
                priceCell.classList.add('flash-red');
            }
            
            setTimeout(() => {
                priceCell.classList.remove('flash-green', 'flash-red');
            }, 600);
        }
    }
    
    // Add hover events for tooltip
    row.addEventListener('mouseenter', (e) => showTooltip(coin, e));
    row.addEventListener('mouseleave', hideTooltip);
    row.addEventListener('mousemove', updateTooltipPosition);
    
    return row;
}

// ============================================
// FORMATTING HELPERS
// ============================================

function formatPrice(price) {
    if (price >= 1) {
        return price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    } else if (price >= 0.01) {
        return price.toLocaleString('en-US', {minimumFractionDigits: 4, maximumFractionDigits: 4});
    } else {
        return price.toLocaleString('en-US', {minimumFractionDigits: 8, maximumFractionDigits: 8});
    }
}

function formatPriceChange(change) {
    const value = parseFloat(change) || 0;
    const className = value >= 0 ? 'positive' : 'negative';
    const sign = value >= 0 ? '+' : '';
    return `<span class="price-change ${className}">${sign}${value.toFixed(2)}%</span>`;
}

function formatLargeNumber(num) {
    const value = parseFloat(num) || 0;
    
    if (value >= 1e12) {
        return (value / 1e12).toFixed(2) + 'T';
    } else if (value >= 1e9) {
        return (value / 1e9).toFixed(2) + 'B';
    } else if (value >= 1e6) {
        return (value / 1e6).toFixed(2) + 'M';
    } else if (value >= 1e3) {
        return (value / 1e3).toFixed(2) + 'K';
    } else {
        return value.toFixed(2);
    }
}

function getCoinId(symbol) {
    // Map symbols to CoinMarketCap IDs
    const idMap = {
        'BTC': 1,
        'ETH': 1027,
        'USDT': 825,
        'BNB': 1839,
        'SOL': 5426,
        'USDC': 3408,
        'XRP': 52,
        'DOGE': 74,
        'ADA': 2010,
        'TRX': 1958,
        'AVAX': 5805,
        'SHIB': 5994,
        'DOT': 6636,
        'LINK': 1975,
        'MATIC': 3890,
        'UNI': 7083,
        'LTC': 2,
        'BCH': 1831,
        'XLM': 512,
        'ATOM': 3794,
        'ETC': 1321
    };
    
    return idMap[symbol] || 1; // Default to Bitcoin
}

// ============================================
// TOOLTIP FUNCTIONALITY
// ============================================

function createTooltipElement() {
    const tooltip = document.createElement('div');
    tooltip.id = 'tokenTooltip';
    tooltip.className = 'token-tooltip';
    document.body.appendChild(tooltip);
    currentTooltip = tooltip;
}

async function showTooltip(coin, event) {
    if (!currentTooltip) return;
    
    // Clear any existing timeout
    clearTimeout(tooltipTimeout);
    
    // Delay showing tooltip slightly
    tooltipTimeout = setTimeout(async () => {
        try {
            // Fetch detailed token information
            const response = await fetch(`/api/market/token/${coin.symbol}`);
            const data = await response.json();
            
            if (data.success && data.data) {
                const details = data.data;
                
                // Build tooltip HTML
                currentTooltip.innerHTML = `
                    <div class="tooltip-header">
                        <img src="${details.logo || 'https://via.placeholder.com/48'}" 
                             alt="${details.name}" 
                             class="tooltip-logo"
                             onerror="this.style.display='none'">
                        <div class="tooltip-title">
                            <h3 class="tooltip-name">${details.name}</h3>
                            <p class="tooltip-symbol">${details.symbol} • Rank #${details.market_cap_rank || coin.rank}</p>
                        </div>
                    </div>
                    
                    <div class="tooltip-price">
                        $${formatPrice(details.price)}
                        ${formatPriceChange(details.percent_change_24h)}
                    </div>
                    
                    <div class="tooltip-stats">
                        <div class="tooltip-stat">
                            <div class="tooltip-stat-label">Market Cap</div>
                            <div class="tooltip-stat-value">$${formatLargeNumber(details.market_cap)}</div>
                        </div>
                        <div class="tooltip-stat">
                            <div class="tooltip-stat-label">24h Volume</div>
                            <div class="tooltip-stat-value">$${formatLargeNumber(details.volume_24h)}</div>
                        </div>
                        <div class="tooltip-stat">
                            <div class="tooltip-stat-label">Circulating Supply</div>
                            <div class="tooltip-stat-value">${formatLargeNumber(details.circulating_supply)}</div>
                        </div>
                        <div class="tooltip-stat">
                            <div class="tooltip-stat-label">Max Supply</div>
                            <div class="tooltip-stat-value">${details.max_supply ? formatLargeNumber(details.max_supply) : '∞'}</div>
                        </div>
                    </div>
                    
                    ${details.description ? `
                        <div class="tooltip-description">
                            ${details.description.substring(0, 200)}${details.description.length > 200 ? '...' : ''}
                        </div>
                    ` : ''}
                `;
                
                // Position and show tooltip
                updateTooltipPosition(event);
                currentTooltip.classList.add('show');
            }
        } catch (error) {
            console.error('Error loading token details:', error);
        }
    }, 300); // 300ms delay before showing
}

function hideTooltip() {
    clearTimeout(tooltipTimeout);
    if (currentTooltip) {
        currentTooltip.classList.remove('show');
    }
}

function updateTooltipPosition(event) {
    if (!currentTooltip || !currentTooltip.classList.contains('show')) return;
    
    const tooltip = currentTooltip;
    const offsetX = 20;
    const offsetY = 20;
    
    let x = event.clientX + offsetX;
    let y = event.clientY + offsetY;
    
    // Keep tooltip within viewport
    const tooltipRect = tooltip.getBoundingClientRect();
    
    if (x + tooltipRect.width > window.innerWidth) {
        x = event.clientX - tooltipRect.width - offsetX;
    }
    
    if (y + tooltipRect.height > window.innerHeight) {
        y = event.clientY - tooltipRect.height - offsetY;
    }
    
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
}

// ============================================
// AUTO-REFRESH
// ============================================

function startAutoRefresh() {
    // Clear existing interval
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Refresh every 30 seconds
    autoRefreshInterval = setInterval(() => {
        console.log('🔄 Auto-refreshing market data...');
        loadMarketData();
    }, 30000);
    
    console.log('✅ Auto-refresh started (every 30 seconds)');
}

function updateTimestamp() {
    const timestampEl = document.getElementById('marketLastUpdate');
    if (timestampEl) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit', second: '2-digit'});
        timestampEl.textContent = `Updated: ${timeStr}`;
    }
}

// ============================================
// CLEANUP
// ============================================

// Clean up when page unloads
window.addEventListener('beforeunload', () => {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});

