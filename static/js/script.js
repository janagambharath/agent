// Global variables
let currentTrends = [];

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
});

// Run AI Agent
async function runAgent() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <p>🤖 AI Agent is running... This may take 1-2 minutes.</p>
            <p><small>Scraping trends → AI categorization → Content generation → Updating sheets</small></p>
        </div>
    `;
    
    try {
        const response = await fetch('/run-agent', { 
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`✅ ${data.message}`);
            
            if (data.results && data.results.length > 0) {
                displayResults(data.results);
            } else {
                resultsDiv.innerHTML = '<div class="result-item"><p>No relevant trends found in this batch.</p></div>';
            }
        } else {
            showError(`❌ Error: ${data.error}`);
        }
    } catch (error) {
        showError(`❌ Network error: ${error.message}`);
    }
    
    updateStats();
}

// Display results
function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<h2>🎯 AI Agent Results</h2>';
    
    results.forEach((result, index) => {
        const resultHTML = `
            <div class="result-item">
                <h3>${result.trend}</h3>
                <p><strong>Category:</strong> ${result.category}</p>
                
                <div class="content-preview">
                    <h5>📷 Instagram Post</h5>
                    <p>${result.instagram_post || 'No content generated'}</p>
                </div>
                
                <div class="content-preview">
                    <h5>📝 Blog Draft</h5>
                    <p>${result.blog_draft ? result.blog_draft.substring(0, 150) + '...' : 'No content generated'}</p>
                </div>
                
                <p><strong>Status:</strong> <span class="status-badge status-pending">${result.status}</span></p>
                
                <div class="action-buttons">
                    <button class="btn btn-success" onclick="updateStatus('${result.trend}', 'Approved')">
                        ✅ Approve
                    </button>
                    <button class="btn btn-danger" onclick="updateStatus('${result.trend}', 'Rejected')">
                        ❌ Reject
                    </button>
                </div>
            </div>
        `;
        resultsDiv.innerHTML += resultHTML;
    });
}

// Get all trends
async function getTrends() {
    const trendsDiv = document.getElementById('trendsList');
    trendsDiv.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Loading trends...</p></div>';
    
    try {
        const response = await fetch('/get-trends');
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            currentTrends = data.data;
            displayAllTrends(data.data);
        } else {
            trendsDiv.innerHTML = '<div class="result-item"><p>No trends generated yet. Run the AI Agent first.</p></div>';
        }
    } catch (error) {
        showError(`Error loading trends: ${error.message}`);
    }
    
    updateStats();
}

// Display all trends
function displayAllTrends(trends) {
    const trendsDiv = document.getElementById('trendsList');
    trendsDiv.innerHTML = '<h2>📈 All Generated Content</h2>';
    
    trends.forEach(trend => {
        const statusClass = `status-${trend.status.toLowerCase().replace(' ', '-')}`;
        const trendHTML = `
            <div class="trend-item">
                <h4>${trend.trend}</h4>
                <p>
                    <strong>Category:</strong> ${trend.category} | 
                    <strong>Status:</strong> <span class="status-badge ${statusClass}">${trend.status}</span> |
                    <strong>Time:</strong> ${trend.timestamp}
                </p>
                
                <div class="content-preview">
                    <h5>📷 Instagram</h5>
                    <p>${trend.instagram_post || 'No content'}</p>
                </div>
                
                <div class="content-preview">
                    <h5>📝 Blog</h5>
                    <p>${trend.blog_draft ? trend.blog_draft.substring(0, 100) + '...' : 'No content'}</p>
                </div>
                
                <div class="content-preview">
                    <h5>🎥 YouTube Script</h5>
                    <p>${trend.youtube_script || 'No content'}</p>
                </div>
                
                <div class="content-preview">
                    <h5>🖼️ Thumbnail Idea</h5>
                    <p>${trend.thumbnail_idea || 'No content'}</p>
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-success" onclick="updateStatus('${trend.trend}', 'Approved')">
                        ✅ Approve
                    </button>
                    <button class="btn btn-danger" onclick="updateStatus('${trend.trend}', 'Rejected')">
                        ❌ Reject
                    </button>
                    <button class="btn btn-info" onclick="viewFullContent('${trend.trend}')">
                        👁️ View Full
                    </button>
                </div>
            </div>
        `;
        trendsDiv.innerHTML += trendHTML;
    });
}

// Update status
async function updateStatus(trend, newStatus) {
    try {
        const response = await fetch('/update-status', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ trend: trend, status: newStatus })
        });
        
        const data = await response.json();
        if (data.success) {
            showSuccess(`Status updated to: ${newStatus}`);
            getTrends(); // Refresh the list
        } else {
            showError('Error updating status');
        }
    } catch (error) {
        showError('Network error while updating status');
    }
}

// View full content
function viewFullContent(trend) {
    const trendData = currentTrends.find(t => t.trend === trend);
    if (trendData) {
        const content = `
Trend: ${trendData.trend}
Category: ${trendData.category}
Status: ${trendData.status}
Timestamp: ${trendData.timestamp}

📷 INSTAGRAM POST:
${trendData.instagram_post}

📝 BLOG DRAFT:
${trendData.blog_draft}

🎥 YOUTUBE SCRIPT:
${trendData.youtube_script}

🖼️ THUMBNAIL IDEA:
${trendData.thumbnail_idea}
        `;
        alert(content);
    }
}

// Update statistics
function updateStats() {
    const pending = currentTrends.filter(t => t.status === 'Pending Review').length;
    const approved = currentTrends.filter(t => t.status === 'Approved').length;
    
    document.getElementById('totalTrends').textContent = currentTrends.length;
    document.getElementById('pendingTrends').textContent = pending;
    document.getElementById('approvedTrends').textContent = approved;
}

// Clear results
function clearResults() {
    document.getElementById('results').innerHTML = '';
    document.getElementById('trendsList').innerHTML = '';
    showSuccess('Results cleared');
}

// Utility functions
function showSuccess(message) {
    alert(message); // In production, replace with toast notification
    console.log('✅', message);
}

function showError(message) {
    alert(message); // In production, replace with toast notification
    console.error('❌', message);
}

// Export functionality (for future enhancement)
function exportToCSV() {
    // Implementation for CSV export
    console.log('Export to CSV functionality');
}

function exportToJSON() {
    // Implementation for JSON export
    console.log('Export to JSON functionality');
}
