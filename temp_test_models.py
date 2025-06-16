
try:
    from models import Guest, Booking
    print("SUCCESS: Models imported")
except Exception as e:
    print(f"ERROR: {str(e)}")
