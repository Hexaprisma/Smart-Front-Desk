from calendar_manager import CalendarManager
from config import SERVICES, SPECIALISTS

calendar = CalendarManager()

print("Welcome to Herbal Nail Bar Booking System")
print("Available services:")
for name, duration in SERVICES.items():
    print(f"- {name} ({duration} min)")
print("Available specialists:", ", ".join(SPECIALISTS))

while True:
    print("\n1. Add appointment")
    print("2. List appointments")
    print("3. Cancel appointment")
    print("4. Exit")

    choice = input("Your choice: ").strip()

    if choice == "1":
        name = input("Customer name: ")
        phone = input("Phone number: ")
        date = input("Date (YYYY-MM-DD): ")
        time = input("Time (HH:MM 24h): ")
        service = input("Service name: ")
        pref = input(f"Preferred specialist (optional): ")
        pref = pref if pref.strip() else None
        calendar.add_appointment(name, phone, date, time, service, pref)

    elif choice == "2":
        calendar.list_appointments()
    elif choice == "3":
        appt_id = input("Appointment ID to cancel: ")
        calendar.cancel_appointment(appt_id)
    elif choice == "4":
        print("Goodbye!")
        break
    else:
        print("Invalid option.")

calendar.close()
