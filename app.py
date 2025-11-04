from flask import Flask, request, jsonify, render_template
from transformers import AutoModel, AutoTokenizer, pipeline
import sqlite3
import underthesea
from datetime import datetime

DB_PATH = "sentiment_history.db"

# -------------------------
# DATABASE
# -------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_result(text, sentiment):
    conn = get_conn()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO sentiments (text, sentiment, timestamp) VALUES (?, ?, ?)",
        (text, sentiment, timestamp)
    )
    conn.commit()
    conn.close()

def load_history(limit=50):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT text, sentiment, timestamp FROM sentiments ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    data = cursor.fetchall()
    conn.close()
    # trả về list dict cho dễ dùng ở frontend
    return [{"text": r[0], "sentiment": r[1], "timestamp": r[2]} for r in data]


# -------------------------
# LOAD MODELS
# -------------------------
def load_models():
    base_tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base-v2")
    base_model = AutoModel.from_pretrained("vinai/phobert-base-v2")

    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="wonrax/phobert-base-vietnamese-sentiment",
        tokenizer="wonrax/phobert-base-vietnamese-sentiment"
    )
    return base_model, base_tokenizer, sentiment_pipeline

base_model, base_tokenizer, sentiment_pipe = load_models()


# -------------------------
# PREPROCESS + RULES
# -------------------------
NEUTRAL_KEYWORDS = [
    "ổn định", "ổn", "bình thường", "ổn thôi", "khá ổn", "ổn thôi",
    "thuận lợi vừa phải", "tạm ổn", "bình thường thôi"
]

POSITIVE_KEYWORDS = [
    "tuyệt", "tốt", "hạnh phúc", "vui", "yêu", "hài lòng", "xuất sắc", "tuyệt vời"
]

NEGATIVE_KEYWORDS = [
    "tệ", "không tốt", "buồn", "bực", "ghét", "tồi", "khổ", "mệt"
]

def preprocess_text(text):
    text = text.lower()
    text = text.replace("ko", "không").replace("k", "không")
    text = text.replace("bt", "bình thường").replace("rat", "rất")
    return underthesea.word_tokenize(text, format="text")

def contains_any_keyword(text_lower, keywords):
    for k in keywords:
        if k in text_lower:
            return True
    return False

def map_sentiment_label(label):
    label = label.upper()
    if label == "LABEL_0": return "NEGATIVE"
    if label == "LABEL_1": return "NEUTRAL"
    if label == "LABEL_2": return "POSITIVE"
    if label in ["POS", "POSITIVE"]: return "POSITIVE"
    if label in ["NEG", "NEGATIVE"]: return "NEGATIVE"
    return "NEUTRAL"


# -------------------------
# CLASSIFY (với rule từ khóa trung tính ưu tiên)
# -------------------------
def classify_sentiment(raw_text, base_model, base_tokenizer, sentiment_pipe, confidence_threshold=0.65):
    raw_trim = (raw_text or "").strip()
    if len(raw_trim) < 5:
        return "ERROR", "CÂU QUÁ NGẮN!", 0.0

    text_lower = raw_trim.lower()

    # --- Rule 1 (ưu tiên): nếu chứa từ khóa NEUTRAL -> trả NEUTRAL ngay
    if contains_any_keyword(text_lower, NEUTRAL_KEYWORDS):
        save_result(raw_trim, "NEUTRAL")
        return "SUCCESS", "NEUTRAL", 1.0  # score 1.0 ở đây chỉ để hiển thị, thực tế là rule

    # --- Rule 2 (từ khóa positive/negative trước khi pipeline, nếu muốn)
    if contains_any_keyword(text_lower, POSITIVE_KEYWORDS):
        save_result(raw_trim, "POSITIVE")
        return "SUCCESS", "POSITIVE", 1.0
    if contains_any_keyword(text_lower, NEGATIVE_KEYWORDS):
        save_result(raw_trim, "NEGATIVE")
        return "SUCCESS", "NEGATIVE", 1.0

    # --- fallback: gọi pipeline (mô hình phụ)
    processed = preprocess_text(raw_trim)
    try:
        res = sentiment_pipe(processed)[0]
        label = map_sentiment_label(res.get("label", "LABEL_1"))
        score = float(res.get("score", 0.0))
    except Exception:
        label, score = "NEUTRAL", 0.0

    # theo đề: nếu score < threshold => NEUTRAL
    if score < confidence_threshold:
        label = "NEUTRAL"

    save_result(raw_trim, label)
    return "SUCCESS", label, score


# -------------------------
# FLASK APP
# -------------------------
app = Flask(__name__)
init_db()

sentiment_map = {
    "POSITIVE": "Tích cực",
    "NEUTRAL": "Trung tính",
    "NEGATIVE": "Tiêu cực",
    "ERROR": "Lỗi"
}

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", sentiment_map=sentiment_map)

@app.route("/classify", methods=["POST"])
def classify_api():
    data = request.json or {}
    text = data.get("text", "")
    status, sentiment, score = classify_sentiment(text, base_model, base_tokenizer, sentiment_pipe)
    return jsonify({
        "status": status,
        "sentiment": sentiment_map.get(sentiment, sentiment),
        "score": score
    })

@app.route("/history", methods=["GET"])
def history_api():
    limit = int(request.args.get("limit", 50))
    data = load_history(limit)
    # convert sentiment code -> display label
    for item in data:
        item["sentiment_display"] = sentiment_map.get(item["sentiment"], item["sentiment"])
    return jsonify({"history": data})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
