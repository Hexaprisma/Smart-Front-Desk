from flask import Flask, render_template, request
from datetime import datetime, timedelta
from calendar_manager import CalendarManager
from config import OPEN_TIME, CLOSE_TIME, SPECIALISTS, SERVICES

app = Flask(__name__)
calendar = CalendarManager()

def get_time_slots():
    start = datetime.strptime(OPEN_TIME, "%H:%M")
    end = datetime.strptime(CLOSE_TIME, "%H:%M")
    slots = []
    while start < end:
        slots.append(start.strftime("%H:%M"))
        start += timedelta(minutes=30)
    return slots

@app.route("/", methods=["GET", "POST"])
def show_calendar():
    date_str = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
    time_slots = get_time_slots()

    # Build a map of busy slots per specialist
    busy_map = {spec: [] for spec in SPECIALISTS}
    rows = calendar.conn.execute("""
        SELECT time, service, specialist FROM Appointments
        WHERE date = ?
    """, (date_str,)).fetchall()

    for row in rows:
        start = datetime.strptime(row[0], "%H:%M")
        service_name = row[1]
        duration = SERVICES.get(service_name, {"duration": 30})["duration"]
        end = start + timedelta(minutes=duration)
        busy_map[row[2]].append((start, end))

    # Build the schedule with multi-slot blocking for long services
    schedule = []
    for time in time_slots:
        current_time = datetime.strptime(time, "%H:%M")
        row = {"time": time, "specialists": []}
        for specialist in SPECIALISTS:
            is_booked = False
            for start, end in busy_map[specialist]:
                if start <= current_time < end:
                    is_booked = True
                    break
            if is_booked:
                appt = calendar.conn.execute("""
                    SELECT service, customer_name FROM Appointments
                    WHERE date = ? AND time = ? AND specialist = ?
                """, (date_str, time, specialist)).fetchone()
                if appt:
                    row["specialists"].append({"status": "booked", "text": f"{appt[0]} ({appt[1]})"})
                else:
                    row["specialists"].append({"status": "booked", "text": "Busy"})
            else:
                row["specialists"].append({"status": "available", "text": ""})
        schedule.append(row)

    return render_template("calendar.html", schedule=schedule, date=date_str, specialists=SPECIALISTS)

if __name__ == "__main__":
    app.run(debug=True)
