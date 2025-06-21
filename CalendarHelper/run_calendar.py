from calendar_manager import CalendarManager
from config import SERVICES, SPECIALISTS

if __name__ =="__main__":
    calendar = CalendarManager()

    name = "Dolly"
    phone = "1234567890"
    date = "2025-06-23"
    time = "10:30"
    service = "Nail Polish"
    specialist = "Sophia"
    calendar.add_appointment(name, phone, date, time, service, specialist)
    
    name = "Lily"
    phone = "1234567890"
    date = "2025-06-24"
    time = "11:30"
    service = "Nail Polish"
    specialist = "Sophia"
    calendar.add_appointment(name, phone, date, time, service, specialist)

    # view events
    calendar.list_appointments()

    # Cancel an event
    #calendar.cancel_Appointment(1)

    #View events
    #calendar.list_events()

    calendar.close()