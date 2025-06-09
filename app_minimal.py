"""
Temporary minimal app for testing Koyeb deployment
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        "status": "OK", 
        "message": "Hotel Booking App is running!",
        "python_version": os.sys.version,
        "test": "import_verification"
    })

@app.route('/test-import')
def test_import():
    try:
        # Test individual imports first
        import logic
        
        # Test specific function import
        from logic import import_from_gsheet
        
        return jsonify({
            "status": "SUCCESS",
            "message": "All imports working correctly",
            "logic_functions": len([name for name in dir(logic) if not name.startswith('_')]),
            "import_from_gsheet": str(type(import_from_gsheet))
        })
        
    except ImportError as e:
        return jsonify({
            "status": "ERROR",
            "error_type": "ImportError", 
            "message": str(e)
        }), 500
        
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error_type": type(e).__name__,
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5001)), debug=False)
