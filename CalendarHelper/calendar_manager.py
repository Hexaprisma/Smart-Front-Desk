from datetime import datetime, timedelta
from .config import WEEKDAYS, OPEN_TIME, CLOSE_TIME, SERVICES, SPECIALISTS
import sqlite3

class CalendarManager:
    def __init__(self, db_path=r"data\calendarData\calendar.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()
        #self._load_service_table()


    def _create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS Appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            date TEXT,
            time TEXT,
            service TEXT,
            phone TEXT,
            specialist TEXT,
            price REAL
        );
        """)
        self.conn.commit()

    #use this function to start service table
    def _load_service_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS Services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,                          
            duration TEXT,
            price REAL,
            discription TEXT
        );
        """)
        self.conn.commit()

    #use this function to write service table
    def _write_service_table(self, service, duration, price, discription):
        self.conn.execute("""
            INSERT INTO Services (service, duration, price, discription)
            VALUES (?, ?, ?, ?)
        """, (service, duration, price, discription))
        self.conn.commit()
        print(f"Service is now added to the database.")



    def is_valid_service(self, service):
        return service in SERVICES

    def find_available_specialist(self, date_str, time_str, duration, preferred=None):
        """Return available specialist or None if unavailable"""
        time_start = datetime.strptime(time_str, "%H:%M")
        time_end = time_start + timedelta(minutes=duration)

        # Get all overlapping appointments on that day
        rows = self.conn.execute("""
        SELECT time, service, specialist FROM Appointments
        WHERE date = ?
        """, (date_str,)).fetchall()

        busy_map = {name: [] for name in SPECIALISTS}

        for row in rows:
            start = datetime.strptime(row[0], "%H:%M")
            end = start + timedelta(minutes=SERVICES.get("duration", 30))
            busy_map[row[2]].append((start, end))

        def is_free(name):
            return all(not (time_start < e and time_end > s) for s, e in busy_map[name])

        if preferred:
            if preferred in SPECIALISTS and is_free(preferred):
                return preferred
            else:
                return None
        else:
            for name in SPECIALISTS:
                if is_free(name):
                    return name
            return None

    def check_business_hours(self, date_str, time_str, duration):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = date_obj.strftime("%A")
            if weekday not in WEEKDAYS:
                return False, f"Closed on {weekday}."

            start = datetime.strptime(time_str, "%H:%M")
            end = start + timedelta(minutes=duration)
            open_time = datetime.strptime(OPEN_TIME, "%H:%M")
            close_time = datetime.strptime(CLOSE_TIME, "%H:%M")

            if start < open_time or end > close_time:
                return False, "Outside business hours."
            return True, ""
        except:
            return False, "Invalid date or time format."

    def add_appointment(self, customer_name, phone, date, time, service, preferred_specialist=None):
        if not self.is_valid_service(service):
            print("Invalid service.")
            return 1

        duration = SERVICES[service]["duration"]
        valid, msg = self.check_business_hours(date, time, duration)
        if not valid:
            print(msg)
            return 2

        assigned = self.find_available_specialist(date, time, duration, preferred=preferred_specialist)
        if not assigned:
            print("No specialist available at that time.")
            return 3

        self.conn.execute("""
            INSERT INTO Appointments (customer_name, date, time, service, phone, specialist)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_name, date, time, service, phone, assigned))
        self.conn.commit()
        print(f"Appointment booked with {assigned} for {service} on {date} at {time}.")
        return 0

    def check_appointment_availability(self, date, time, preferred_specialist=None, service=None):
        duration = SERVICES[service]["duration"]
        if service == None:
            duration = "60"
        elif not self.is_valid_service(service):
            print("Invalid service.")
            return 1

        
        valid, msg = self.check_business_hours(date, time, duration)
        if not valid:
            print(msg)
            return 2

        assigned = self.find_available_specialist(date, time, duration, preferred=preferred_specialist)
        if not assigned:
            print("No specialist available at that time.")
            return 3
        
        return f"service {service} at {time} {date} with {assigned} is available"

    def list_appointments(self):
        rows = self.conn.execute("SELECT * FROM Appointments ORDER BY date, time").fetchall()
        if not rows:
            print("No appointments.")
            return
        for row in rows:
            print(f"[{row[0]}] {row[1]} - {row[2]} at {row[3]} with {row[6]} ({row[4]})")

    def cancel_appointment(self, appointment_id):
        self.conn.execute("DELETE FROM Appointments WHERE id = ?", (appointment_id,))
        self.conn.commit()
        print(f"Appointment ID {appointment_id} canceled.")

    def check_menu(self):
        print(f"We offer:\n")
        print(f"{SERVICES}")

    #OpenAI SQLite methods
    def get_table_names(self):
        """Return a list of table names."""
        table_names = []
        #conn.execute is used to execute an SQL statement. It returns a cursor object 
        #that allows you to interate over the results of a query. 
        tables = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for table in tables.fetchall():
            table_names.append(table[0])
            print(table[0])
        return table_names

    def get_column_names(self, table_name):
        """Return a list of column names."""
        column_names = []
        columns = self.conn.execute(f"PRAGMA table_info('{table_name}');").fetchall()
        for col in columns:
            column_names.append(col[1])
        return column_names


    def get_database_info(self):
        """Return a list of dicts containing the table name and column for each table in the database."""
        table_dicts = []
        for table_name in self.get_table_names():
            column_names = self.get_column_names(table_name)
            table_dicts.append({"table_name": table_name, "column_names": column_names})
        return table_dicts


    def ask_database(self, query):
        """Function to query SQLite database with a provided SQL query."""
        try:
            results = str(self.conn.execute(query).fetchall())
        except Exception as e:
            results = f"query failed with error: (e)"
        return results



    def close(self):
        self.conn.close()
