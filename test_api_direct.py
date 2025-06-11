import requests
import json

# Test API directly
base_url = "http://127.0.0.1:8080"

try:
    # Test default URL first
    print("Testing default URL API...")
    response = requests.get(f"{base_url}/api/get_default_booking_url", timeout=5)
    if response.status_code == 200:
        result = response.json()
        print(f"Default URL success: {result.get('success')}")
        
        if result.get('success'):
            # Test market analysis with the default URL
            print("\nTesting market analysis API...")
            default_url = result.get('default_url')
            
            payload = {
                "booking_url": default_url,
                "max_properties": 5
            }
            
            print(f"Payload: {payload}")
            
            analysis_response = requests.post(
                f"{base_url}/api/analyze_market_prices",
                json=payload,
                timeout=30
            )
            
            print(f"Analysis status code: {analysis_response.status_code}")
            
            if analysis_response.status_code == 200:
                analysis_result = analysis_response.json()
                print(f"Analysis success: {analysis_result.get('success')}")
                
                if analysis_result.get('success'):
                    properties = analysis_result.get('properties', [])
                    print(f"Properties found: {len(properties)}")
                    
                    if properties:
                        print(f"Sample property: {properties[0].get('name')} - {properties[0].get('price_display')}")
                        
                        # Test AI analysis
                        print("\nTesting AI analysis API...")
                        ai_payload = {
                            "properties": properties,
                            "price_threshold": 500000
                        }
                        
                        ai_response = requests.post(
                            f"{base_url}/api/ai_pricing_analysis",
                            json=ai_payload,
                            timeout=15
                        )
                        
                        print(f"AI analysis status: {ai_response.status_code}")
                        
                        if ai_response.status_code == 200:
                            ai_result = ai_response.json()
                            print(f"AI analysis success: {ai_result.get('success')}")
                            print(f"AI method: {ai_result.get('method')}")
                        else:
                            print(f"AI analysis error: {ai_response.text}")
                            
                else:
                    print(f"Analysis error: {analysis_result.get('error')}")
            else:
                print(f"Analysis failed: {analysis_response.text}")
    else:
        print(f"Default URL failed: {response.status_code}")
        
except Exception as e:
    print(f"Test error: {e}")
    
print("\nTest completed!")
