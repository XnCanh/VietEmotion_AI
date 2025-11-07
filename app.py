from flask import Flask, request, jsonify, render_template
from transformers import pipeline
import sqlite3
from underthesea import word_tokenize
from datetime import datetime
import re

app = Flask(__name__)
DB_PATH = "sentiment_history.db"

# DATABASE
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sentiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            processed_text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            confidence REAL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_result(original, processed, sentiment, confidence):
    conn = get_conn()
    c = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO sentiments 
        (original_text, processed_text, sentiment, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (original, processed, sentiment, confidence, ts))
    conn.commit()
    conn.close()

def load_history(limit=50):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT original_text, sentiment, confidence, timestamp 
        FROM sentiments ORDER BY id DESC LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "text": r[0],
            "sentiment": r[1],
            "sentiment_display": {
                "POSITIVE": "Tích cực",
                "NEGATIVE": "Tiêu cực",
                "NEUTRAL": "Trung tính"
            }.get(r[1], r[1]),
            "sentiment_class": {
                "POSITIVE": "positive",
                "NEGATIVE": "negative",
                "NEUTRAL": "neutral"
            }.get(r[1], "neutral"),
            "confidence": round(r[2], 4) if r[2] is not None else None,
            "timestamp": r[3]
        } for r in rows
    ]

# MODEL
sentiment_pipe = pipeline(
    "sentiment-analysis",
    model="wonrax/phobert-base-vietnamese-sentiment",
    tokenizer="vinai/phobert-base-v2",
    device=0 if __import__('torch').cuda.is_available() else -1
)

# PREPROCESS: ≤50 ký tự + chuẩn hóa
NORMALIZE_MAP = {
    "rat": "rất", "rât": "rất", "rắt": "rất",
    "hom": "hôm", "hok": "hông",
    "dc": "được", "đc": "được",
    "k": "không", "ko": "không",
    "bt": "bình thường"
}

def normalize_text(text):
    text = text.lower()
    for wrong, correct in NORMALIZE_MAP.items():
        text = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, text)
    return text

def preprocess_vietnamese(text):
    # B1: Chuẩn hóa
    text = normalize_text(text)

    # B2: GIỚI HẠN ≤50 KÝ TỰ
    if len(text) > 50:
        text = text[:50]
        last_space = text.rfind(' ')
        if last_space > 35:
            text = text[:last_space]

    original_trim = text.strip()

    if len(original_trim) < 5:
        return None, None, None

    # Word tokenize
    tokens = word_tokenize(original_trim)
    processed = " ".join(tokens)
    return original_trim, processed, tokens

# CLASSIFY: ≥5 ký tự + ≤50 ký tự + POP-UP
def map_label(label):
    label = label.upper()
    if label in ["POS", "LABEL_2"]: return "POSITIVE"
    if label in ["NEG", "LABEL_0"]: return "NEGATIVE"
    if label in ["NEU", "LABEL_1"]: return "NEUTRAL"
    return "NEUTRAL"

def classify_sentiment(raw_text):
    raw_text = (raw_text or "").strip()

    # KIỂM TRA RỖNG HOẶC < 5 KÝ TỰ
    if not raw_text:
        return "ERROR", "Câu không hợp lệ, thử lại", None
    if len(raw_text) < 5:
        return "ERROR", "Câu không hợp lệ, thử lại", None
    if len(raw_text) > 50:
        return "ERROR", "Câu không hợp lệ, thử lại", None

    # Tiền xử lý + GIỚI HẠN ≤50 ký tự
    original_trim, processed_text, _ = preprocess_vietnamese(raw_text)
    if not original_trim:
        return "ERROR", "Câu không hợp lệ, thử lại", None

    try:
        result = sentiment_pipe(processed_text, truncation=True, max_length=256)[0]
        label = map_label(result["label"])
        score = result["score"]
    except Exception:
        return "ERROR", "Lỗi hệ thống, thử lại sau", None

    if score < 0.5:
        label = "NEUTRAL"

    save_result(raw_text, processed_text, label, score)
    return "SUCCESS", label, score

# ROUTES
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/classify", methods=["POST"])
def classify():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    status, message, score = classify_sentiment(text)
    
    if status == "ERROR":
        return jsonify({"status": "ERROR", "message": message})

    display_sentiment = {
        "POSITIVE": "Tích cực",
        "NEGATIVE": "Tiêu cực",
        "NEUTRAL": "Trung tính"
    }.get(message, message)

    return jsonify({
        "status": "SUCCESS",
        "sentiment": display_sentiment,
        "confidence": round(score, 4) if score is not None else None
    })

@app.route("/history", methods=["GET"])
def history():
    limit = min(int(request.args.get("limit", 50)), 100)
    data = load_history(limit)
    return jsonify({"history": data})

# KHỞI TẠO
if __name__ == "__main__":
    init_db()
    print("Server chạy tại: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)