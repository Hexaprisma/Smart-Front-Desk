from flask import Flask, render_template, request
from datetime import datetime, timedelta
from calendar_manager import CalendarManager
from config import OPEN_TIME, CLOSE_TIME, SPECIALISTS

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

    schedule = []
    for time in time_slots:
        row = {"time": time, "specialists": []}
        for specialist in SPECIALISTS:
            appt = calendar.conn.execute("""
                SELECT service, customer_name FROM Appointments
                WHERE date = ? AND time = ? AND specialist = ?
            """, (date_str, time, specialist)).fetchone()
            if appt:
                row["specialists"].append({"status": "booked", "text": f"{appt[0]} ({appt[1]})"})
            else:
                row["specialists"].append({"status": "available", "text": ""})
        schedule.append(row)

    return render_template("calendar.html", schedule=schedule, date=date_str, specialists=SPECIALISTS)

if __name__ == "__main__":
    app.run(debug=True)
