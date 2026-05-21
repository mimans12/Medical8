import json
import os
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DB_PATH = "nightcare.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Doctors table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            speciality TEXT NOT NULL,
            rating REAL,
            distance_km REAL
        )
    """)

    # Ambulance bookings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ambulance_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT,
            pickup_location TEXT,
            destination TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Blood banks
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blood_banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            units_available INTEGER NOT NULL,
            distance_km REAL
        )
    """)

    # Seed doctors
    cur.execute("SELECT COUNT(*) as count FROM doctors")
    if cur.fetchone()["count"] == 0:
        doctors = [
            ("Dr. Aditi Rao", "emergency", 4.9, 1.2),
            ("Dr. Karan Mehta", "cardio", 4.8, 2.1),
            ("Dr. Sana Ali", "pediatrics", 4.7, 0.9),
        ]

        cur.executemany("""
            INSERT INTO doctors(name, speciality, rating, distance_km)
            VALUES (?, ?, ?, ?)
        """, doctors)

    # Seed blood banks
    cur.execute("SELECT COUNT(*) as count FROM blood_banks")
    if cur.fetchone()["count"] == 0:
        blood_rows = [
            ("City Blood Center", "A+", 6, 2.1),
            ("City Blood Center", "O+", 4, 2.1),
            ("Metro Blood Bank", "A+", 3, 3.4),
            ("Metro Blood Bank", "O+", 2, 3.4),
            ("Govt. Blood Bank", "A+", 0, 4.1),
        ]

        cur.executemany("""
            INSERT INTO blood_banks(
                name,
                blood_group,
                units_available,
                distance_km
            )
            VALUES (?, ?, ?, ?)
        """, blood_rows)

    conn.commit()
    conn.close()


class ApiHandler(BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data, status=200):
        response = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()

        self.wfile.write(response)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))

        if length == 0:
            return {}

        body = self.rfile.read(length).decode("utf-8")

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path

        routes = {
            "/api/login": self.handle_login,
            "/api/symptom-checker": self.handle_symptom_checker,
            "/api/ambulance/book": self.handle_ambulance_book,
            "/api/blood/check": self.handle_blood_check,
        }

        handler = routes.get(path)

        if handler:
            handler()
        else:
            self.send_json({"error": "Not found"}, status=404)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/doctors":
            self.handle_doctors()
        else:
            self.send_json({"error": "Not found"}, status=404)

    def handle_login(self):
        data = self.read_json_body()

        phone = str(data.get("phone", "")).strip()
        otp = str(data.get("otp", "")).strip()

        if not phone or not otp:
            self.send_json(
                {"error": "phone and otp required"},
                status=400
            )
            return

        if len(otp) != 6 or not otp.isdigit():
            self.send_json(
                {"error": "invalid otp, must be 6 digits"},
                status=400
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT OR IGNORE INTO users(phone) VALUES (?)",
            (phone,)
        )

        conn.commit()

        cur.execute(
            "SELECT id, phone, created_at FROM users WHERE phone = ?",
            (phone,)
        )

        row = cur.fetchone()
        conn.close()

        self.send_json({
            "status": "ok",
            "user": dict(row)
        })

    def handle_symptom_checker(self):
        data = self.read_json_body()
        text = str(data.get("description", "")).lower()

        if not text.strip():
            self.send_json({
                "error": "description required",
                "message": "Please describe at least one symptom"
            }, status=400)
            return

        severity = "mild"
        urgency = "normal"
        problem = "General viral / mild condition"

        recommendation = (
            "Monitor at home, hydrate well and "
            "consult doctor if symptoms persist."
        )

        if any(word in text for word in [
            "chest", "stroke", "unconscious"
        ]):
            severity = "critical"
            urgency = "emergency"
            problem = (
                "Possible cardiac or neurological emergency"
            )
            recommendation = (
                "Immediate ambulance required. "
                "Do NOT drive yourself. "
                "Start CPR if not breathing."
            )

        elif any(word in text for word in [
            "breath", "difficulty breathing", "asthma"
        ]):
            severity = "high"
            urgency = "urgent"
            problem = "Breathing difficulty"

            recommendation = (
                "Use inhaler if prescribed and "
                "seek emergency care if worsening."
            )

        elif "bleeding" in text or "blood" in text:
            severity = "high"
            urgency = "urgent"
            problem = "Significant bleeding"

            recommendation = (
                "Apply firm pressure and "
                "visit nearest emergency."
            )

        elif "fever" in text or "temperature" in text:
            severity = "moderate"
            urgency = "normal"
            problem = "Fever / infection-like symptoms"

            recommendation = (
                "Hydrate and use paracetamol "
                "if advised by doctor."
            )

        self.send_json({
            "possible_problem": problem,
            "severity": severity,
            "urgency": urgency,
            "recommendation": recommendation
        })

    def handle_doctors(self):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                name,
                speciality,
                rating,
                distance_km
            FROM doctors
            ORDER BY distance_km ASC
        """)

        rows = cur.fetchall()   # FIXED BUG
        conn.close()

        doctors = [dict(row) for row in rows]

        self.send_json({
            "doctors": doctors
        })

    def handle_ambulance_book(self):
        data = self.read_json_body()

        phone = str(data.get("phone", "")).strip()
        pickup = str(
            data.get("pickup_location", "")
        ).strip()

        destination = str(
            data.get("destination", "")
        ).strip()

        if not pickup:
            self.send_json({
                "error": "pickup_location required"
            }, status=400)
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO ambulance_bookings(
                user_phone,
                pickup_location,
                destination,
                status
            )
            VALUES (?, ?, ?, ?)
        """, (
            phone,
            pickup,
            destination,
            "BOOKED"
        ))

        booking_id = cur.lastrowid

        conn.commit()
        conn.close()

        self.send_json({
            "status": "ok",
            "booking_id": booking_id,
            "eta_minutes": 5,
            "message":
                "Ambulance booked successfully."
        })

    def handle_blood_check(self):
        data = self.read_json_body()

        blood_group = str(
            data.get("blood_group", "")
        ).strip().upper()

        if not blood_group:
            self.send_json({
                "error": "blood_group required"
            }, status=400)
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                name,
                units_available,
                distance_km
            FROM blood_banks
            WHERE blood_group = ?
            ORDER BY distance_km ASC
        """, (blood_group,))

        rows = cur.fetchall()
        conn.close()

        self.send_json({
            "blood_group": blood_group,
            "banks": [dict(row) for row in rows]
        })


def run_server():
    init_db()

    port = int(os.environ.get("PORT", 8000))

    server = HTTPServer(
        ("0.0.0.0", port),
        ApiHandler
    )

    print(f"Backend running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()