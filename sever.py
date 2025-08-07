from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

# --- CẤU HÌNH ---
# !!! QUAN TRỌNG: BẠN PHẢI THAY THẾ DÒNG DƯỚI ĐÂY BẰNG API KEY THẬT CỦA BẠN !!!
# Lấy API Key miễn phí tại: https://aistudio.google.com/
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') 


app = Flask(__name__)
# CORS cho phép trang web của bạn (chạy ở địa chỉ khác) có thể gọi đến máy chủ này
CORS(app) 

@app.route('/ask-gemini', methods=['POST'])
def ask_gemini():
    """
    Endpoint này nhận câu hỏi từ người dùng, gửi đến Gemini và trả về câu trả lời.
    """
    data = request.json
    user_question = data.get('question', '')

    if not user_question:
        return jsonify({'error': 'Câu hỏi không được để trống'}), 400
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'GEMINI_API_KEY':
        print("LỖI: API Key của Gemini chưa được cấu hình.")
        return jsonify({'error': 'API Key của Gemini chưa được cấu hình trên máy chủ.'}), 500

    # Prompt được thiết kế để AI đóng vai trợ lý của EduGames
    prompt = f"""
    Bạn là một trợ lý ảo thân thiện và chuyên nghiệp của EduGames, một công ty chuyên thiết kế slide và game giáo dục theo yêu cầu. 
    Hãy trả lời câu hỏi của người dùng một cách ngắn gọn, hữu ích và luôn giữ thái độ tích cực.
    - Nếu người dùng hỏi về giá hoặc cách đặt hàng, hãy hướng dẫn họ nhấp vào các nút "Nhận báo giá ngay" trên trang web để bắt đầu quy trình tư vấn tự động.
    - Nếu người dùng hỏi về các gói dịch vụ (Premium, Pro, Ultra), hãy tóm tắt các quyền lợi chính của gói đó.
    - Với các câu hỏi khác, hãy trả lời một cách tốt nhất có thể.
    
    Câu hỏi của người dùng: "{user_question}"
    """

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Báo lỗi nếu có vấn đề về kết nối hoặc xác thực
        response_data = response.json()

        # Kiểm tra xem có phản hồi bị chặn vì lý do an toàn không
        if 'promptFeedback' in response_data and response_data['promptFeedback'].get('blockReason'):
            block_reason = response_data['promptFeedback']['blockReason']
            print(f"LỖI: Yêu cầu bị chặn bởi Google vì lý do an toàn: {block_reason}")
            return jsonify({'answer': 'Rất tiếc, câu hỏi của bạn vi phạm chính sách an toàn của chúng tôi.'}), 400

        # Lấy câu trả lời từ cấu trúc JSON của Gemini
        answer_text = response_data['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'answer': answer_text.strip()})

    except requests.exceptions.HTTPError as http_err:
        print(f"Lỗi HTTP khi gọi Gemini API: {http_err.response.text}")
        return jsonify({'error': 'Lỗi từ máy chủ AI của Google. Vui lòng kiểm tra lại API Key.'}), 500
    except Exception as e:
        print(f"Một lỗi không xác định đã xảy ra: {e}")
        return jsonify({'error': 'Lỗi không xác định xảy ra trên máy chủ.'}), 500

if __name__ == '__main__':
    # Chạy máy chủ ở chế độ debug để dễ dàng kiểm tra
    app.run(host='0.0.0.0', port=5000, debug=True)