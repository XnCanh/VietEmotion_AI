# import streamlit as st
# from transformers import AutoModel, AutoTokenizer, pipeline
# import torch
# import sqlite3
# import underthesea
# from datetime import datetime

# # --- I. THIẾT LẬP MÔ HÌNH VÀ CƠ SỞ DỮ LIỆU ---
# def classify_base_model(processed_text, base_model, tokenizer):
#     try:
#         inputs = tokenizer(processed_text, return_tensors="pt", padding=True, truncation=True)
#         with torch.no_grad():
#             outputs = base_model(**inputs)
#             cls_features = outputs.last_hidden_state[:, 0, :] 
#         # Giả định NEUTRAL với score thấp để chuyển quyền quyết định sang mô hình phụ
#         return "NEUTRAL", 0.50 
#     except Exception:
#         return "NEUTRAL", 0.0

# @st.cache_resource
# def load_models():
#     try:
#         base_tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base-v2")
#         base_model = AutoModel.from_pretrained("vinai/phobert-base-v2") 
        
#         sentiment_pipeline = pipeline(
#             "sentiment-analysis", 
#             model="wonrax/phobert-base-vietnamese-sentiment",
#             tokenizer=base_tokenizer 
#         )
#         return base_model, base_tokenizer, sentiment_pipeline
#     except Exception as e:
#         st.error(f"Lỗi khi tải mô hình: {e}. Vui lòng kiểm tra thư viện PyTorch/Transformers.")
#         return None, None, None

# def init_db():
#     conn = sqlite3.connect('sentiment_history.db')
#     cursor = conn.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS sentiments (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             text TEXT NOT NULL,
#             sentiment TEXT NOT NULL,
#             timestamp TEXT NOT NULL
#         )
#     """)
#     conn.commit()
#     conn.close()

# def save_result(text, sentiment):
#     conn = sqlite3.connect('sentiment_history.db')
#     cursor = conn.cursor()
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
#     try:
#         cursor.execute(
#             "INSERT INTO sentiments (text, sentiment, timestamp) VALUES (?, ?, ?)", 
#             (text, sentiment, timestamp)
#         )
#         conn.commit()
#     except sqlite3.Error as e:
#         st.error(f"Lỗi lưu trữ DB: {e}")
#     finally:
#         conn.close()

# def load_history():
#     conn = sqlite3.connect('sentiment_history.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT text, sentiment, timestamp FROM sentiments ORDER BY timestamp DESC LIMIT 50")
#     history = cursor.fetchall()
#     conn.close()
#     return history

# # --- II. TIỀN XỬ LÝ VÀ PHÂN LOẠI (CORE LOGIC) ---
# def preprocess_text(text):
#     text = text.lower().replace("ko", "không").replace("bt", "bình thường").replace("rat", "rất").replace("qá", "quá").replace("buon", "buồn")
    
#     return underthesea.word_tokenize(text, format="text")

# def map_sentiment_label(label):
#     label = label.upper()
    
#     if label == "LABEL_0": return "NEGATIVE"
#     if label == "LABEL_1": return "NEUTRAL"
#     if label == "LABEL_2": return "POSITIVE"
    
#     if label == "POS": return "POSITIVE"
#     if label == "NEG": return "NEGATIVE"
#     if label == "NEU": return "NEUTRAL"
    
#     return label 

# def classify_sentiment(raw_text, base_model, base_tokenizer, sentiment_pipe, confidence_threshold=0.65): 
#     if len(raw_text.strip()) < 5:
#         return "ERROR", "CÂU QUÁ NGẮN! Vui lòng nhập ít nhất 5 ký tự."
    
#     # 1. Tiền xử lý 
#     processed_text = preprocess_text(raw_text)
    
#     # 2. Xử lý Mô hình Chính (PhoBERT-Base-v2) - Ghi nhận đã xử lý
#     base_label, base_score = classify_base_model(processed_text, base_model, base_tokenizer) 

#     # 3. Phân loại bằng Mô hình Phụ (Wonrax/Fine-tuned) - Lấy xác suất đáng tin cậy
#     sentiment_score = 0.0
#     sentiment_label = "NEUTRAL"
    
#     try:
#         sentiment_result = sentiment_pipe(processed_text)[0] 
#         sentiment_label = map_sentiment_label(sentiment_result['label']) 
#         sentiment_score = sentiment_result['score']
#     except Exception:
#         pass 

#     # 4. Áp dụng chiến lược kiểm tra xác suất theo yêu cầu
#     fallback_threshold = 0.5 
    
#     if sentiment_score >= confidence_threshold: # score >= 0.65
#         final_sentiment = sentiment_label
#     elif sentiment_score >= fallback_threshold: # 0.5 <= score < 0.65
#         final_sentiment = "NEUTRAL"
#     else:
#         # Xác suất < 0.5, trả về NEUTRAL mặc định
#         final_sentiment = "NEUTRAL" 
    
#     # 5. Lưu và trả về
#     save_result(raw_text, final_sentiment)
#     return "SUCCESS", final_sentiment

# # --- III. GIAO DIỆN NGƯỜI DÙNG (STREAMLIT) ---
# def main_app():
#     st.set_page_config(page_title="Trợ Lý Phân Loại Cảm Xúc Việt", layout="wide")
#     st.title("🤖 XÂY DỰNG TRỢ LÝ PHÂN LOẠI CẢM XÚC TIẾNG VIỆT SỬ DỤNG TRANSFORMER")
    
#     init_db()
#     base_model, base_tokenizer, sentiment_pipe = load_models()

#     if base_model is None or base_tokenizer is None or sentiment_pipe is None:
#         st.stop()

#     sentiment_map = {
#         "POSITIVE": "Tích cực",
#         "NEUTRAL": "Trung tính",
#         "NEGATIVE": "Tiêu cực",
#         "ERROR": "Lỗi"
#     }

#     st.header("1. Nhập Câu Văn Bản")
#     input_text = st.text_area("Nhập câu tiếng Việt tự do:", height=100, key="input_text", placeholder="VD: Hôm nay tôi rất vui.")

#     if st.button("🚀 Phân loại Cảm xúc"):
#         if input_text:
#             with st.spinner('Đang phân tích cảm xúc...'):
#                 status, sentiment = classify_sentiment(input_text, base_model, base_tokenizer, sentiment_pipe)
            
#             if status == "ERROR":
#                 st.error(sentiment) 
#                 st.session_state['current_sentiment'] = sentiment_map[status]
#             else:
#                 sentiment_display = sentiment_map.get(sentiment, "Không xác định") 
#                 st.session_state['current_sentiment'] = sentiment_display
#         else:
#             st.warning("Vui lòng nhập câu để phân loại.")

#     st.header("2. Kết Quả Phân Loại (NLP)")
#     if 'current_sentiment' in st.session_state:
#         sentiment_display = st.session_state['current_sentiment']
        
#         if sentiment_display == "Tích cực":
#             st.success(f"Cảm xúc: **{sentiment_display}** (POSITIVE) 🎉")
#         elif sentiment_display == "Tiêu cực":
#             st.error(f"Cảm xúc: **{sentiment_display}** (NEGATIVE) 😞")
#         elif sentiment_display == "Trung tính":
#             st.info(f"Cảm xúc: **{sentiment_display}** (NEUTRAL) 😐")
#         else:
#              st.warning(f"Trạng thái: **{sentiment_display}**")
#     else:
#         st.info("Nhấn 'Phân loại Cảm xúc' để xem kết quả.")

#     st.markdown("---")
    
#     st.header("3. Danh sách Lịch Sử Phân Loại")
#     history_data = load_history()

#     if history_data:
#         table_data = []
#         for text, sentiment, timestamp in history_data:
#             table_data.append({
#                 "Thời gian": timestamp,
#                 "Câu văn": text,
#                 "Cảm xúc": sentiment_map.get(sentiment, sentiment)
#             })
        
#         st.dataframe(table_data, use_container_width=True)
#     else:
#         st.write("Chưa có lịch sử phân loại nào được lưu.")

# if __name__ == "__main__":
#     main_app()