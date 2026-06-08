from ai_scrum_master.core.requirement_router import route_requirement

# The actual user's full requirement text (similar to what they paste)
req = """Customer Booking System - Core Appointment Management

As a customer or administrator, I want to create, view, update, and cancel service bookings through the booking system, so that customers can schedule home maintenance appointments and administrators can manage technician assignments and service delivery.

booking creation, technician assignment, notification delivery, status tracking, slot availability"""

r = route_requirement(req)
print(f"domain: {r['domain']}")
print(f"template: {r['template_name']}")
print(f"required_concepts: {r['required_concepts']}")
print(f"reason: {r['reason']}")
print()

# Also test a pure notification requirement still works
req2 = "Add email notification when booking is confirmed"
r2 = route_requirement(req2)
print(f"domain: {r2['domain']}")
print(f"template: {r2['template_name']}")
