import sqlite3
from datetime import datetime

class CalendarManager:
    #change this to the actual path where you want to store the calendar
    def __init__(self, db_path = "data\calendarData\calendar.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_events_table()


    def _create_events_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS Events (
        id INTEGER PRIMARY kEY AUTOINCREMENT,
        title TEXT NOT NULL,
        date TEXT NOT NULL,     --Format: YYYY-MM-DD
        time TEXT NOT NULL,     --Format: HH:MM
        description TEXT
        );
        """
        self.conn.execute(query)
        self.conn.commit()

    def add_event(self, title, date, time, specialist, description=""):
        query = """
        INSERT INTO Events (title, date, time, specialist, description)
        VALUES (?, ?, ?, ?, ?)
        """

        self.conn.execute(query, (title, date, time, specialist, description))
        self.conn.commit()
        print(f"Event '{title}' added on {date} at {time} with specialist {specialist}.")

    def cancel_event(self, event_id):
        query = "DELETE FROM Events WHERE id = ?"
        self.conn.execute(query, (event_id,))
        self.conn.commit()
        print(f"Event ID {event_id} canceld.")

    def list_events(self, date=None):
        if date:
            query = "SELECT * FORM Events WHERE date = ? ORDER BY time"
            rows = self.conn.execute(query, (date,)).fetchall()
        else:
            query = "SELECT * FROM Events ORDER BY date, time"
            rows = self.conn.execute(query).fetchall()
        
        print("Upcoming Events:")
        for row in rows:
            print(f"[{row[0]}] {row[1]} - {row[2]} at {row[3]} | {row[4]}")
        if not rows:
            print("No events found.")
        
    def close(self):
        self.conn.close()

