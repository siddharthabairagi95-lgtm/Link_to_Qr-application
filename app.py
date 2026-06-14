from flask import Flask, render_template, request, send_file, jsonify
from urllib.parse import urlparse
from io import BytesIO
import qrcode

app = Flask(__name__)


def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ["http", "https"] and bool(parsed.netloc)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json(silent=True) or {}
        url = data.get("url") or request.form.get("url")

        if not url:
            return jsonify({"success": False, "message": "URL is required"}), 400

        if not is_valid_url(url):
            return jsonify({"success": False, "message": "Invalid URL"}), 400

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )

        qr.add_data(url)
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color="white")

        memory_buffer = BytesIO()
        image.save(memory_buffer, format="PNG")
        memory_buffer.seek(0)

        return send_file(
            memory_buffer,
            mimetype="image/png",
            as_attachment=True,
            download_name="qr-code.png"
        )

    except Exception as e:
        print("Error:", e)
        return jsonify({
            "success": False,
            "message": "Internal Server Error"
        }), 500

@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)