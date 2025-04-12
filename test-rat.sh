#!/bin/bash

echo "Testing RAT (Retrieval-Augmented Thinking) capabilities..."

# Test the RAT analyze endpoint
echo "Testing RAT analyze endpoint..."
curl -X POST http://localhost:3000/api/ultra-precision/rat/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze potential till skimming behavior in the bar area",
    "context": {
      "zone": "bar-area",
      "staffId": "ESSENCE",
      "timestamp": 1712616000000
    }
  }'

echo -e "\n\n"

# Test adding knowledge to RAT system
echo "Testing adding knowledge to RAT system..."
curl -X POST http://localhost:3000/api/ultra-precision/rat/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "category": "new_patterns",
    "content": "# New Theft Patterns\n\n## Digital Payment Manipulation\nDigital payment manipulation involves manipulating payment apps or digital payment systems to steal funds.\nSigns include unusual device handling during payment, discrepancies between reported and actual payment amounts,\nand suspicious patterns in digital transaction logs.\n\n## Loyalty Program Abuse\nLoyalty program abuse involves manipulating customer loyalty programs for personal gain.\nSigns include unusual patterns in loyalty point redemptions, discrepancies in loyalty program accounts,\nand suspicious timing of loyalty program transactions."
  }'

echo -e "\n\n"

# Test simulating a detection
echo "Testing simulating a detection..."
curl -X POST http://localhost:3000/api/ultra-precision/simulate
