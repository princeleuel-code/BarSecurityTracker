// Simple test script for RAT thinking capabilities

import axios from 'axios';

async function testRATThinking() {
  try {
    console.log('Testing RAT (Retrieval-Augmented Thinking) capabilities...');

    // Test the RAT analyze endpoint
    const response = await axios.post('http://localhost:3000/api/ultra-precision/rat/analyze', {
      query: 'Analyze potential till skimming behavior in the bar area',
      context: {
        zone: 'bar-area',
        staffId: 'ESSENCE',
        timestamp: Date.now()
      }
    });

    console.log('RAT Analysis Result:');
    console.log(JSON.stringify(response.data, null, 2));

    // Test adding knowledge to RAT system
    const knowledgeResponse = await axios.post('http://localhost:3000/api/ultra-precision/rat/knowledge', {
      category: 'new_patterns',
      content: `
# New Theft Patterns

## Digital Payment Manipulation
Digital payment manipulation involves manipulating payment apps or digital payment systems to steal funds.
Signs include unusual device handling during payment, discrepancies between reported and actual payment amounts,
and suspicious patterns in digital transaction logs.

## Loyalty Program Abuse
Loyalty program abuse involves manipulating customer loyalty programs for personal gain.
Signs include unusual patterns in loyalty point redemptions, discrepancies in loyalty program accounts,
and suspicious timing of loyalty program transactions.
      `
    });

    console.log('Knowledge Addition Result:');
    console.log(JSON.stringify(knowledgeResponse.data, null, 2));

    // Test simulating a detection
    const simulationResponse = await axios.post('http://localhost:3000/api/ultra-precision/simulate');

    console.log('Simulation Result:');
    console.log(JSON.stringify(simulationResponse.data, null, 2));

  } catch (error) {
    console.error('Error testing RAT capabilities:', error.message);
    if (error.response) {
      console.error('Response data:', error.response.data);
    }
  }
}

testRATThinking();
