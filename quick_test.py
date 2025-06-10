"""
Quick test for Market Price Analyzer imports and basic functionality
"""
try:
    print("Testing imports...")
    from market_price_analyzer import MarketPriceAnalyzer, format_price_analysis_for_display
    print("SUCCESS: Imports working")
    
    # Test demo data generation
    analyzer = MarketPriceAnalyzer()
    demo_result = analyzer._generate_demo_data(5, "test_url")
    
    print(f"SUCCESS: Demo data generated - {len(demo_result.get('properties', []))} properties")
    
    # Test formatting
    formatted = format_price_analysis_for_display(demo_result)
    print(f"SUCCESS: Formatting working - {formatted.get('success', False)}")
    
    if formatted.get('success'):
        summary = formatted.get('summary', {})
        print(f"Average price: {summary.get('avg_price', 0):,.0f}₫")
        print(f"Properties: {summary.get('total_found', 0)}")
    
    print("All tests passed!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
