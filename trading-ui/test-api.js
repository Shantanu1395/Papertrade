// Simple test script to verify API endpoints
const API_BASE_URL = 'http://localhost:8001';

async function testEndpoint(endpoint, description) {
  try {
    console.log(`\n🧪 Testing: ${description}`);
    console.log(`📡 Endpoint: ${endpoint}`);
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ Success: ${JSON.stringify(data).substring(0, 100)}...`);
    return data;
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
    return null;
  }
}

async function testPOSTEndpoint(endpoint, body, description) {
  try {
    console.log(`\n🧪 Testing: ${description}`);
    console.log(`📡 Endpoint: ${endpoint}`);
    console.log(`📦 Body: ${JSON.stringify(body)}`);
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ Success: ${JSON.stringify(data).substring(0, 100)}...`);
    return data;
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
    return null;
  }
}

async function runTests() {
  console.log('🚀 Starting API Integration Tests');
  console.log('=' .repeat(50));
  
  // Test all the endpoints our UI will use
  await testEndpoint('/account/usdt-balance', 'USDT Balance');
  await testEndpoint('/account/portfolio', 'Portfolio Holdings');
  await testEndpoint('/trades/history', 'Trade History');
  
  // Test PnL calculation
  await testPOSTEndpoint('/trades/pnl/calculate', {
    start_time: '2025-05-25 12:00:00',
    end_time: '2025-06-07 23:59:59'
  }, 'PnL Calculation');
  
  console.log('\n🏁 Tests completed!');
}

// Run the tests
runTests();
