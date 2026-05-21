import json
import os
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DB_PATH = "nightcare.db"


# ==========================
# DATABASE CONNECTION
# ==========================
def get_db_connection():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


# ==========================
# DATABASE INIT
# ==========================
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DOCTORS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            speciality TEXT NOT NULL,
            rating REAL DEFAULT 0,
            distance_km REAL DEFAULT 0
        )
    """)

    # AMBULANCE BOOKINGS
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

    # BLOOD BANKS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blood_banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            units_available INTEGER NOT NULL,
            distance_km REAL
        )
    """)

    # ==========================
    # SEED DOCTORS
    # ==========================
    cur.execute(
        "SELECT COUNT(*) as count FROM doctors"
    )

    if cur.fetchone()["count"] == 0:
        doctors = [
            (
                "Dr. Aditi Rao",
                "emergency",
                4.9,
                1.2
            ),
            (
                "Dr. Karan Mehta",
                "cardio",
                4.8,
                2.1
            ),
            (
                "Dr. Sana Ali",
                "pediatrics",
                4.7,
                0.9
            ),
        ]

        cur.executemany("""
            INSERT INTO doctors(
                name,
                speciality,
                rating,
                distance_km
            )
            VALUES (?, ?, ?, ?)
        """, doctors)

    # ==========================
    # SEED BLOOD BANKS
    # ==========================
    cur.execute(
        "SELECT COUNT(*) as count FROM blood_banks"
    )

    if cur.fetchone()["count"] == 0:
        blood_rows = [
            (
                "City Blood Center",
                "A+",
                6,
                2.1
            ),
            (
                "City Blood Center",
                "O+",
                4,
                2.1
            ),
            (
                "Metro Blood Bank",
                "A+",
                3,
                3.4
            ),
            (
                "Metro Blood Bank",
                "O+",
                2,
                3.4
            ),
            (
                "Govt. Blood Bank",
                "A+",
                0,
                4.1
            ),
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


# ==========================
# API HANDLER
# ==========================
class ApiHandler(
    BaseHTTPRequestHandler
):

    # -----------------------
    # CORS
    # -----------------------
    def _set_cors_headers(self):
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

    # -----------------------
    # SEND JSON RESPONSE
    # -----------------------
    def send_json(
        self,
        data,
        status=200
    ):
        response = json.dumps(
            data
        ).encode("utf-8")

        self.send_response(status)

        self._set_cors_headers()

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.end_headers()
        self.wfile.write(response)

    # -----------------------
    # READ BODY
    # -----------------------
    def read_json_body(self):
        length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )

        if length == 0:
            return {}

        body = self.rfile.read(
            length
        ).decode("utf-8")

        try:
            return json.loads(body)

        except json.JSONDecodeError:
            return {}

    # -----------------------
    # OPTIONS
    # -----------------------
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    # ==========================
    # POST ROUTES
    # ==========================
    def do_POST(self):
        path = urlparse(
            self.path
        ).path

        routes = {
            "/api/login":
                self.handle_login,

            "/api/symptom-checker":
                self.handle_symptom_checker,

            "/api/ambulance/book":
                self.handle_ambulance_book,

            "/api/blood/check":
                self.handle_blood_check,
        }

        handler = routes.get(path)

        if handler:
            handler()
        else:
            self.send_json(
                {"error": "Not found"},
                status=404
            )

    # ==========================
    # GET ROUTES
    # ==========================
    def do_GET(self):
        path = urlparse(
            self.path
        ).path

        if path == "/api/doctors":
            self.handle_doctors()

        elif path == "/api/users":
            self.handle_users()

        elif path == "/api/bookings":
            self.handle_bookings()

        else:
            self.send_json(
                {"error": "Not found"},
                status=404
            )

    # ==========================
    # LOGIN
    # ==========================
    def handle_login(self):
        data = self.read_json_body()

        phone = str(
            data.get("phone", "")
        ).strip()

        otp = str(
            data.get("otp", "")
        ).strip()

        if not phone or not otp:
            self.send_json(
                {
                    "error":
                    "phone and otp required"
                },
                status=400
            )
            return

        if (
            len(otp) != 6
            or not otp.isdigit()
        ):
            self.send_json(
                {
                    "error":
                    "OTP must be 6 digits"
                },
                status=400
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT OR IGNORE
            INTO users(phone)
            VALUES (?)
        """, (phone,))

        conn.commit()

        cur.execute("""
            SELECT
                id,
                phone,
                created_at
            FROM users
            WHERE phone = ?
        """, (phone,))

        row = cur.fetchone()
        conn.close()

        self.send_json({
            "status": "ok",
            "user": dict(row)
        })

    # ==========================
    # SYMPTOM CHECKER
    # ==========================
    def handle_symptom_checker(
        self
    ):
        data = self.read_json_body()

        text = str(
            data.get(
                "description",
                ""
            )
        ).lower()

        if not text.strip():
            self.send_json({
                "error":
                "description required"
            }, status=400)
            return

        severity = "mild"
        urgency = "normal"
        problem = (
            "General viral condition"
        )

        recommendation = (
            "Rest and hydrate."
        )

        if any(word in text
               for word in [
                   "chest",
                   "stroke",
                   "unconscious"
               ]):
            severity = "critical"
            urgency = "emergency"
            problem = (
                "Possible cardiac emergency"
            )
            recommendation = (
                "Call ambulance immediately."
            )

        elif (
            "fever" in text
            or "temperature" in text
        ):
            severity = "moderate"
            urgency = "normal"
            problem = (
                "Fever / infection"
            )
            recommendation = (
                "Take medicine & rest."
            )

        self.send_json({
            "possible_problem":
                problem,
            "severity":
                severity,
            "urgency":
                urgency,
            "recommendation":
                recommendation
        })

    # ==========================
    # DOCTORS
    # ==========================
    def handle_doctors(self):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM doctors
            ORDER BY distance_km ASC
        """)

        rows = cur.fetchall()
        conn.close()

        doctors = [
            dict(row)
            for row in rows
        ]

        self.send_json({
            "doctors":
                doctors
        })

    # ==========================
    # USERS
    # ==========================
    def handle_users(self):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM users
            ORDER BY id DESC
        """)

        rows = cur.fetchall()
        conn.close()

        users = [
            dict(row)
            for row in rows
        ]

        self.send_json({
            "users":
                users
        })

    # ==========================
    # AMBULANCE BOOK
    # ==========================
    def handle_ambulance_book(
        self
    ):
        data = self.read_json_body()

        phone = str(
            data.get(
                "phone",
                ""
            )
        ).strip()

        pickup = str(
            data.get(
                "pickup_location",
                ""
            )
        ).strip()

        destination = str(
            data.get(
                "destination",
                ""
            )
        ).strip()

        if not pickup:
            self.send_json({
                "error":
                "pickup required"
            }, status=400)
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO
            ambulance_bookings(
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
            "booking_id":
                booking_id,
            "eta_minutes": 5
        })

    # ==========================
    # BOOKINGS
    # ==========================
    def handle_bookings(self):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM ambulance_bookings
            ORDER BY id DESC
        """)

        rows = cur.fetchall()
        conn.close()

        bookings = [
            dict(row)
            for row in rows
        ]

        self.send_json({
            "bookings":
                bookings
        })

    # ==========================
    # BLOOD CHECK
    # ==========================
    def handle_blood_check(
        self
    ):
        data = self.read_json_body()

        group = str(
            data.get(
                "blood_group",
                ""
            )
        ).strip().upper()

        if not group:
            self.send_json({
                "error":
                "blood_group required"
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
        """, (group,))

        rows = cur.fetchall()
        conn.close()

        banks = [
            dict(row)
            for row in rows
        ]

        self.send_json({
            "blood_group":
                group,
            "banks":
                banks
        })


# ==========================
# SERVER RUN
# ==========================
def run_server():
    init_db()

    port = int(
        os.environ.get(
            "PORT",
            8000
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        ApiHandler
    )

    print(
        f"Backend running on port {port}"
    )

    server.serve_forever()


if __name__ == "__main__":
    run_server()
