from flask import Flask, request, jsonify, render_template
import sqlite3
import qrcode
from io import BytesIO
import base64
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        business_name TEXT,
                        rating INTEGER,
                        comment TEXT,
                        contact TEXT
                    )''')
    conn.commit()
    conn.close()

# QR Code Generation
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return img_str

# Email Notification
def send_email_notification(business_name, rating, comment, contact):
    sender_email = "your_email@example.com"
    receiver_email = "business_owner@example.com"
    subject = f"New Feedback Received for {business_name}"
    body = f"Rating: {rating}\nComment: {comment}\nContact: {contact if contact else 'Not provided'}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login(sender_email, "your_password")
        server.sendmail(sender_email, receiver_email, msg.as_string())

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.json
    business_name = data.get('business_name')
    feedback_url = f"http://localhost:5000/feedback/{business_name}"
    qr_code = generate_qr_code(feedback_url)
    return jsonify({"qr_code": qr_code})

@app.route('/feedback/<business_name>', methods=['GET', 'POST'])
def feedback(business_name):
    if request.method == 'POST':
        data = request.json
        rating = data.get('rating')
        comment = data.get('comment')
        contact = data.get('contact')

        conn = sqlite3.connect('feedback.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO feedback (business_name, rating, comment, contact) 
                          VALUES (?, ?, ?, ?)''', (business_name, rating, comment, contact))
        conn.commit()
        conn.close()

        # Send email notification
        #send_email_notification(business_name, rating, comment, contact)

        return jsonify({"message": "Feedback submitted successfully!"}), 201

    return render_template('feedback_form.html', business_name=business_name)

@app.route('/feedbacks', methods=['GET'])
def get_feedbacks():
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM feedback')
    feedbacks = cursor.fetchall()
    conn.close()

    feedback_list = [
        {
            "id": row[0],
            "business_name": row[1],
            "rating": row[2],
            "comment": row[3],
            "contact": row[4],
        }
        for row in feedbacks
    ]
    return jsonify(feedback_list)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)



