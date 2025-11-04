📌 1. Thông tin dự án
Tên đề án:	Trợ lý phân loại cảm xúc tiếng Việt (Vietnamese Sentiment Assistant)  
Mục tiêu	Nhận câu tiếng Việt và phân loại cảm xúc: Tích cực / Trung tính / Tiêu cực  
Công nghệ	Python  
🎯 2. Mục tiêu chức năng  
✅ Nhập câu tiếng Việt tự do  
✅ Phân loại cảm xúc bằng Transformer  
✅ Hiển thị kết quả: POSITIVE / NEUTRAL / NEGATIVE  
✅ Lưu lịch sử vào SQLite (câu, nhãn, thời gian)  
✅ Giao diện thân thiện  
✅ Độ chính xác ≥ 65% trên 10 câu test tiếng Việt   
🧠 3. Kiến trúc hệ thống   

User Input → Preprocessing → Transformer Model → Sentiment Result   
                                     ↓   
                             Save to SQLite DB   

   
🛠️ 4. Hướng dẫn cài đặt   
4.1. Yêu cầu môi trường  
  
Python ≥ 3.8  
  
pip
  
Internet để tải model lần đầu  
4.2. Clone dự án   

git clone https://github.com/yourusername/vietnamese-sentiment-assistant.git   
cd vietnamese-sentiment-assistant   
4.3. Tạo môi trường ảo (Windows)   
python -m venv venv   
  
4.4. Cài đặt thư viện  
pip install -r requirements.txt  

📦 5. Cấu trúc thư mục   
📁 sentiment-assistant  
 ┣ 📂 _pycache/                    # Lưu mô hình tải xuống (cache)  
 ┣ 📂 static/                     # lưu dữ câu hình css giao diện   
 ┣ 📂 templates/                  # Lưu giữ cấu hình html giao diện chính   
 ┣ app.py                         # file chạy chính  
 ┣ sentiments_history.db           # SQLite helper  
 ┣ Emmotion.py                     # mô hình transpose  
 ┣ requirements.txt   
 ┗ README.md  
🚀 6. Chạy ứng dụng  
 
python main.py  
📚 . Tài liệu tham khảo   
  
https://huggingface.co/vinai/phobert-base-v2   
  
https://huggingface.co/docs/transformers   
   
https://github.com/undertheseanlp/underthesea   
👥 10. Thành viên nhóm   
        Họ tên	     
3122410*** Trương Xuân Cảnh  
3122410072 Nguyễn Tấn Đạt     
 
