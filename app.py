
import os
import uuid
from io import BytesIO
from flask import Flask, request, render_template_string
from pypdf import PdfReader

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_PAGES = 200

BW_PRICE_PER_PAGE = 5
COLOR_PRICE_PER_PAGE = None  # রঙিনের দাম পরে বসাবে

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

PAGE = """
<!doctype html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JARVIS PRINT</title>
<style>
body {
  font-family: Arial, sans-serif;
  max-width: 540px;
  margin: 30px auto;
  padding: 18px;
  background: #f4f6f8;
}
main {
  background: white;
  padding: 22px;
  border-radius: 12px;
}
h1 { color: #174ea6; }
input, select, button {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  margin: 10px 0;
}
button {
  background: #174ea6;
  color: white;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
}
.note { color: #555; font-size: 14px; }
</style>
</head>
<body>
<main>
<h1>JARVIS PRINT</h1>
<p>PDF আপলোড করে প্রিন্টের দাম হিসাব করুন।</p>

<form method="post" enctype="multipart/form-data">
  <label>প্রিন্টের ধরন বেছে নাও:</label>
  <select name="mode" required>
    <option value="bw">সাদা-কালো — ₹৫ প্রতি পৃষ্ঠা</option>
    <option value="color">রঙিন — দাম পরে নির্ধারণ হবে</option>
  </select>

  <label>PDF ফাইল বেছে নাও:</label>
  <input type="file" name="pdf" accept=".pdf,application/pdf" required>

  <button type="submit">পৃষ্ঠা গুনে দাম হিসাব করো</button>
</form>

{% if message %}
<hr>
<h3>{{ message }}</h3>
{% endif %}

<p class="note">
সর্বোচ্চ ফাইলের আকার ২০ MB এবং সর্বোচ্চ ২০০ পৃষ্ঠা।
এখন এটি শুধু দাম হিসাব করে; পেমেন্ট বা প্রিন্ট শুরু করে না।
</p>
</main>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        uploaded_file = request.files.get("pdf")
        mode = request.form.get("mode")

        if not uploaded_file or not uploaded_file.filename:
            message = "আগে একটি PDF ফাইল বেছে নাও।"
            return render_template_string(PAGE, message=message)

        if not uploaded_file.filename.lower().endswith(".pdf"):
            message = "শুধু PDF ফাইল আপলোড করা যাবে।"
            return render_template_string(PAGE, message=message)

        try:
            file_bytes = uploaded_file.read()

            if not file_bytes:
                message = "ফাইলটি খালি। অন্য PDF বেছে নাও।"
                return render_template_string(PAGE, message=message)

            reader = PdfReader(BytesIO(file_bytes), strict=True)

            if reader.is_encrypted:
                message = "পাসওয়ার্ড-লক করা PDF আপাতত নেওয়া যাবে না।"
                return render_template_string(PAGE, message=message)

            page_count = len(reader.pages)

            if page_count < 1:
                message = "PDF-এ কোনো পৃষ্ঠা পাওয়া যায়নি।"
                return render_template_string(PAGE, message=message)

            if page_count > MAX_PAGES:
                message = f"সর্বোচ্চ {MAX_PAGES} পৃষ্ঠা পর্যন্ত নেওয়া যাবে।"
                return render_template_string(PAGE, message=message)

        except Exception:
            message = "PDF পড়া যায়নি। ফাইলটি ঠিক আছে কি না পরীক্ষা করো।"
            return render_template_string(PAGE, message=message)

        if mode == "bw":
            total = page_count * BW_PRICE_PER_PAGE

            # অস্থায়ীভাবে PDF রাখা হচ্ছে; এখনও প্রিন্ট হবে না।
            filename = f"{uuid.uuid4().hex}.pdf"
            path = os.path.join(UPLOAD_FOLDER, filename)

            with open(path, "wb") as f:
                f.write(file_bytes)

            message = (
                f"পৃষ্ঠা: {page_count} | "
                f"দাম: ₹{BW_PRICE_PER_PAGE} প্রতি পৃষ্ঠা | "
                f"মোট: ₹{total}। "
                "এটি শুধু হিসাব; পেমেন্ট এখনও চালু হয়নি।"
            )

        elif mode == "color":
            if COLOR_PRICE_PER_PAGE is None:
                message = (
                    f"PDF-এ {page_count} পৃষ্ঠা আছে। "
                    "রঙিন প্রিন্টের দাম এখনও নির্ধারিত হয়নি।"
                )
            else:
                total = page_count * COLOR_PRICE_PER_PAGE
                message = (
                    f"পৃষ্ঠা: {page_count} | "
                    f"রঙিনের দাম: ₹{COLOR_PRICE_PER_PAGE} প্রতি পৃষ্ঠা | "
                    f"মোট: ₹{total}"
                )
        else:
            message = "প্রিন্টের ধরন সঠিকভাবে বেছে নাও।"

    return render_template_string(PAGE, message=message)


@app.errorhandler(413)
def file_too_large(error):
    return render_template_string(
        PAGE, message="ফাইল ২০ MB-এর চেয়ে বড়। ছোট PDF আপলোড করো।"
    ), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
