import streamlit as st
import random
import time
import qrcode
from PIL import Image
from io import BytesIO

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Đấu Trường Python", page_icon="🐍", layout="wide")

# --- QUẢN LÝ TRẠNG THÁI TOÀN CỤC (GLOBAL STATE) ---
# Dùng st.cache_resource để lưu dữ liệu game trên RAM của Server
# Dữ liệu này sẽ được CHIA SẺ giữa tất cả người dùng (Giáo viên & Học sinh)

@st.cache_resource
class GameManager:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.teams = {} # { "Tên Đội": điểm }
        self.questions = self.generate_questions()
        self.current_q_index = 0
        self.mode = "WAITING" # WAITING, QUESTION, STEAL, LOCKED
        self.buzzer_winner = None
        self.last_updated = time.time()

    def generate_questions(self):
        # Ngân hàng câu hỏi vận dụng (Logic, Vòng lặp, Toán)
        qs = []
        # Dạng 1: Dự đoán Output
        qs.append({"q": "Kết quả của: print(10 > 5 and not 3 < 1)", "code": None, "ans": "True", "opts": ["True", "False", "Error", "None"]})
        qs.append({"q": "Vòng lặp sau in ra bao nhiêu số?", "code": "for i in range(10, 5, -2):\n    print(i)", "ans": "3", "opts": ["2", "3", "5", "0"]})
        qs.append({"q": "Giá trị cuối cùng của k?", "code": "k = 0\nwhile k < 5:\n    k += 2", "ans": "6", "opts": ["4", "5", "6", "Loop"]})
        qs.append({"q": "Kết quả phép toán: 16 % 3 ** 2", "code": None, "ans": "7", "opts": ["7", "1", "0", "Error"]})
        qs.append({"q": "List a = [1, 2]. a * 2 là?", "code": None, "ans": "[1, 2, 1, 2]", "opts": "[1, 2, 2, 4]", "opts": ["[2, 4]", "[1, 2, 1, 2]", "Lỗi", "[1, 2]"]})
        
        # Sinh thêm câu hỏi ngẫu nhiên
        for i in range(15):
            a, b = random.randint(10, 50), random.randint(2, 9)
            qs.append({
                "q": f"Kết quả của {a} // {b} + {a} % {b}?", 
                "code": None, 
                "ans": str(a//b + a%b), 
                "opts": [str(a//b + a%b), str(a//b), str(a%b), str(a+b)]
            })
        return qs

    def register_team(self, name):
        if name not in self.teams:
            self.teams[name] = 0
    
    def buzz(self, team_name):
        # Chỉ chấp nhận đội bấm đầu tiên khi đang ở chế độ STEAL
        if self.mode == "STEAL":
            self.mode = "LOCKED"
            self.buzzer_winner = team_name
            self.last_updated = time.time()
            return True
        return False

    def next_question(self):
        self.current_q_index = (self.current_q_index + 1) % len(self.questions)
        self.mode = "QUESTION"
        self.buzzer_winner = None
        self.last_updated = time.time()

    def start_steal(self):
        self.mode = "STEAL"
        self.buzzer_winner = None
        self.last_updated = time.time()

    def add_score(self, team_name, points=10):
        if team_name in self.teams:
            self.teams[team_name] += points
        self.mode = "ANSWERED" # Tạm dừng để giáo viên thao tác tiếp

# Khởi tạo Global Manager
game = GameManager()

# --- GIAO DIỆN ---

# CSS Tùy chỉnh cho đẹp
st.markdown("""
<style>
    .big-btn { width: 100%; height: 100px !important; font-size: 30px !important; font-weight: bold; border-radius: 15px; }
    .status-box { padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; color: white; font-weight: bold; font-size: 24px; }
    .st-emotion-cache-16idsys p { font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

# Lấy tham số URL để phân biệt Host/Player
# ?role=host -> Giáo viên
# Mặc định -> Học sinh
params = st.query_params
role = params.get("role", "player")

# --- GIAO DIỆN GIÁO VIÊN (HOST) ---
if role == "host":
    st.title("👨‍🏫 BẢNG ĐIỀU KHIỂN (HOST)")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📡 Kết Nối")
        # Tạo mã QR để học sinh quét
        # Lấy URL hiện tại (trong thực tế cần copy URL trên trình duyệt)
        # Ở đây ta giả lập hiển thị hướng dẫn
        st.info("Học sinh truy cập link ứng dụng này để tham gia.")
        
        st.subheader("🏆 Bảng Điểm")
        if not game.teams:
            st.warning("Chưa có đội nào tham gia.")
        else:
            sorted_teams = sorted(game.teams.items(), key=lambda x: x[1], reverse=True)
            for name, score in sorted_teams:
                st.write(f"**{name}**: {score} điểm")
        
        if st.button("🔄 Reset Game Mới"):
            game.reset_game()
            st.rerun()

    with col2:
        q = game.questions[game.current_q_index]
        
        # Hiển thị trạng thái
        status_color = "#3B82F6" # Blue
        status_text = "ĐANG ĐỌC CÂU HỎI"
        if game.mode == "STEAL":
            status_color = "#EF4444" # Red
            status_text = "ĐANG CHỜ CƯỚP QUYỀN..."
        elif game.mode == "LOCKED":
            status_color = "#F59E0B" # Orange
            status_text = f"🔒 {game.buzzer_winner} ĐÃ GIÀNH QUYỀN!"
        
        st.markdown(f'<div class="status-box" style="background-color: {status_color};">{status_text}</div>', unsafe_allow_html=True)

        # Hiển thị câu hỏi
        st.markdown(f"### Câu {game.current_q_index + 1}: {q['q']}")
        if q['code']:
            st.code(q['code'], language="python")
        
        st.divider()
        
        # Khu vực điều khiển
        if game.mode == "LOCKED":
            st.success(f"🔔 Đội **{game.buzzer_winner}** bấm nhanh nhất!")
            c1, c2 = st.columns(2)
            if c1.button("✅ Trả lời ĐÚNG (+10đ)", use_container_width=True):
                game.add_score(game.buzzer_winner, 10)
                st.rerun()
            if c2.button("❌ Trả lời SAI (0đ)", use_container_width=True):
                game.mode = "ANSWERED" # Quay về trạng thái chờ
                st.rerun()
                
        elif game.mode == "STEAL":
            st.warning("Đang đợi tín hiệu từ điện thoại học sinh...")
            # Nút hủy nếu không ai trả lời
            if st.button("Bỏ qua (Không ai trả lời)", use_container_width=True):
                game.mode = "ANSWERED"
                st.rerun()
            # Auto-refresh cho Host để cập nhật khi có người bấm
            time.sleep(1) 
            st.rerun()

        else: # QUESTION or ANSWERED or WAITING
            c1, c2 = st.columns(2)
            with c1:
                # Nếu đang đọc câu hỏi -> Cho phép mở cướp quyền
                if st.button("🚨 MỞ CƯỚP QUYỀN", type="primary", use_container_width=True):
                    game.start_steal()
                    st.rerun()
            with c2:
                if st.button("➡️ Câu tiếp theo", use_container_width=True):
                    game.next_question()
                    st.rerun()
            
            # Đáp án tham khảo cho giáo viên
            with st.expander("Xem đáp án đúng"):
                st.write(f"Đáp án: **{q['ans']}**")

# --- GIAO DIỆN HỌC SINH (PLAYER) ---
else:
    st.title("📱 Màn Hình Thi Đấu")
    
    # Bước 1: Đăng nhập tên đội
    if "my_team" not in st.session_state:
        name = st.text_input("Nhập tên đội của bạn:", placeholder="Ví dụ: Đội 1")
        if st.button("VÀO GAME") and name:
            st.session_state.my_team = name
            game.register_team(name)
            st.rerun()
    
    # Bước 2: Màn hình chờ bấm chuông
    else:
        team_name = st.session_state.my_team
        st.write(f"Đội: **{team_name}** | Điểm: **{game.teams.get(team_name, 0)}**")
        
        # Logic hiển thị theo trạng thái Server
        if game.mode == "STEAL":
            st.markdown('<div class="status-box" style="background-color: #EF4444; animation: pulse 1s infinite;">🔥 BẤM NGAY! 🔥</div>', unsafe_allow_html=True)
            
            # Nút bấm chuông khổng lồ
            if st.button("GIÀNH QUYỀN TRẢ LỜI", key="buzz_btn"):
                success = game.buzz(team_name)
                if success:
                    st.balloons()
                st.rerun()
            
            # Thêm style cho nút bấm to ra
            st.markdown("""
            <style>
                div.stButton > button:first-child {
                    height: 200px !important;
                    font-size: 40px !important;
                    background-color: #EF4444 !important;
                    color: white !important;
                    border: 4px solid white !important;
                    box-shadow: 0 0 20px #EF4444;
                }
            </style>
            """, unsafe_allow_html=True)

        elif game.mode == "LOCKED":
            if game.buzzer_winner == team_name:
                st.success("🎉 BẠN ĐÃ GIÀNH ĐƯỢC QUYỀN TRẢ LỜI!")
                st.info("Hãy trả lời to cho giáo viên nghe.")
            else:
                st.warning(f"🔒 Chậm tay rồi! Đội {game.buzzer_winner} đã giành quyền.")
        
        elif game.mode == "QUESTION":
            st.info("👀 Hãy nhìn lên màn hình máy chiếu và đợi hiệu lệnh...")
            
        else:
            st.write("Đang chờ giáo viên...")

        # Cơ chế Polling (Tự động cập nhật trạng thái mỗi giây)
        # Đây là thay thế cho Real-time Socket
        time.sleep(1)
        st.rerun()