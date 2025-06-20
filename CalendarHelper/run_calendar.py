from calendar_manager import CalendarManager

if __name__ =="__main__":
    calendar = CalendarManager()

    calendar.add_event("Dentist", "2025-06-20", "14:00", "Annual cleaning")
    calendar.add_event("Team Meeting", "2025-06,21", "10:30", "Project update")

    # view events
    calendar.list_events()

    # Cancel an event
    #calendar.cancel_event(1)

    #View events
    #calendar.list_events()

    calendar.close()