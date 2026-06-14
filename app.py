from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, session
from urllib.parse import urlparse
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
import logging

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

logging.basicConfig(level=logging.INFO)

users = {}


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"] and bool(parsed.netloc)
    except Exception:
        return False


@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    success = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not username or not password or not confirm_password:
            error = "All fields are required"

        elif password != confirm_password:
            error = "Passwords do not match"

        elif username in users:
            error = "Username already exists"

        else:
            users[username] = generate_password_hash(password)
            success = "Account created successfully. Please login."

    return render_template("signup.html", error=error, success=success)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users and check_password_hash(users[username], password):
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/generate", methods=["POST"])
def generate_qr():
    if not session.get("logged_in"):
        return jsonify({
            "success": False,
            "message": "Unauthorized access"
        }), 401

    try:
        if request.is_json:
            data = request.get_json()
            url = data.get("url")
        else:
            url = request.form.get("url")

        if not url:
            return jsonify({"success": False, "message": "URL is required"}), 400

        if not is_valid_url(url):
            return jsonify({"success": False, "message": "Please enter a valid URL"}), 400

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=4
        )

        qr.add_data(url)
        qr.make(fit=True)

        image = qr.make_image(
            fill_color="#0ea5e9",
            back_color="white"
        ).convert("RGB")

        memory_buffer = BytesIO()
        image.save(memory_buffer, format="PNG")
        memory_buffer.seek(0)

        return send_file(memory_buffer, mimetype="image/png", as_attachment=False)

    except Exception as e:
        logging.error(str(e))
        return jsonify({"success": False, "message": "Internal Server Error"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "UP"})


if __name__ == "__main__":
    app.run(debug=True)