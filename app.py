import streamlit as st
import random
import time
import qrcode
from PIL import Image
from io import BytesIO

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Đấu Trường Python", page_icon="🐍", layout="wide")

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .big-btn { width: 100%; height: 80px !important; font-size: 24px !important; font-weight: bold; border-radius: 10px; }
    .status-box { padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px; color: white; font-weight: bold; font-size: 20px; }
    .team-card { background-color: #f0f2f6; padding: 10px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 5px; }
    div[data-testid="stButton"] button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI GAME (GLOBAL) ---
@st.cache_resource
class GameManager:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.teams = {} # { "Tên Đội": điểm }
        self.questions = self.generate_questions()
        self.current_q_index = 0
        self.mode = "WAITING" # WAITING, QUESTION, STEAL, LOCKED, RESULT
        self.buzzer_winner = None
        self.last_result = "" # Lưu thông báo kết quả (Đúng/Sai)
        self.turn_index = 0 # Chỉ số đội đến lượt trả lời (Round Robin)

    def generate_questions(self):
        # Ngân hàng câu hỏi
        qs = []
        # Dạng 1: Code logic
        qs.append({"q": "Kết quả: print(10 > 5 and not 3 < 1)", "code": None, "ans": "True", "opts": ["True", "False", "Error", "None"]})
        qs.append({"q": "Output vòng lặp?", "code": "for i in range(1, 4):\n    print(i, end='')", "ans": "123", "opts": ["123", "1234", "0123", "1 2 3"]})
        qs.append({"q": "Giá trị k cuối cùng?", "code": "k = 0\nwhile k < 5:\n    k += 2", "ans": "6", "opts": ["4", "5", "6", "Loop"]})
        qs.append({"q": "Phép toán: 16 % 3 ** 2", "code": None, "ans": "7", "opts": ["7", "1", "0", "16"]})
        
        # Sinh câu hỏi toán ngẫu nhiên
        for i in range(20):
            a, b = random.randint(10, 50), random.randint(2, 9)
            # Chọn phép tính ngẫu nhiên
            op_type = random.choice(['div_mod', 'compare'])
            
            if op_type == 'div_mod':
                res = a % b
                qs.append({
                    "q": f"Kết quả của {a} % {b} là?", 
                    "code": None, 
                    "ans": str(res), 
                    "opts": [str(res), str(a//b), str(res+1), str(b)]
                })
            else:
                target = random.randint(a-5, a+5)
                res = str(a > target)
                qs.append({
                    "q": f"Biểu thức: {a} > {target}", 
                    "code": None, 
                    "ans": res, 
                    "opts": ["True", "False", "Error", "None"]
                })
        
        # Xáo trộn đáp án cho mỗi câu hỏi
        for q in qs:
            random.shuffle(q["opts"])
            
        return qs

    def register_team(self, name):
        if name and name not in self.teams:
            self.teams[name] = 0
            return True
        return False
    
    def buzz(self, team_name):
        if self.mode == "STEAL":
            self.mode = "LOCKED"
            self.buzzer_winner = team_name
            return True
        return False

    def check_answer(self, selected_opt):
        current_q = self.questions[self.current_q_index]
        correct_ans = current_q['ans']
        
        # Xác định đội đang trả lời
        active_team = self.buzzer_winner if self.mode == "LOCKED" else list(self.teams.keys())[self.turn_index % len(self.teams)]
        
        if selected_opt == correct_ans:
            # ĐÚNG
            self.teams[active_team] += 10
            self.last_result = f"✅ CHÍNH XÁC! {active_team} +10 điểm"
            self.mode = "RESULT" # Chuyển sang màn hình kết quả
        else:
            # SAI
            self.last_result = f"❌ SAI RỒI! Đáp án đúng: {correct_ans}"
            
            if self.mode == "QUESTION":
                # Nếu đang là lượt chính mà sai -> Chuyển sang cướp quyền
                self.mode = "STEAL"
                self.buzzer_winner = None
            else:
                # Nếu đã cướp quyền mà vẫn sai -> Kết thúc câu
                self.mode = "RESULT"

    def next_question(self):
        self.current_q_index = (self.current_q_index + 1) % len(self.questions)
        self.turn_index += 1 # Chuyển lượt cho đội tiếp theo
        self.mode = "QUESTION"
        self.buzzer_winner = None
        self.last_result = ""

    def start_game(self):
        self.mode = "QUESTION"
        self.turn_index = 0

game = GameManager()

# --- XỬ LÝ URL ---
params = st.query_params
role = params.get("role", "player")

# --- GIAO DIỆN GIÁO VIÊN (HOST) ---
if role == "host":
    st.header("👨‍🏫 BẢNG ĐIỀU KHIỂN GIÁO VIÊN")
    
    # 1. SIDEBAR: Quản lý đội & QR
    with st.sidebar:
        st.subheader("Link tham gia:")
        # Lấy URL cơ bản (cắt bỏ phần ?role=host)
        # Lưu ý: Trên localhost có thể cần điều chỉnh tay, trên cloud sẽ tự động đúng
        base_url = "https://python-arena.streamlit.app/" # Thay bằng link thật khi deploy
        st.code(base_url, language="text")
        
        st.divider()
        st.subheader(f"👥 Danh sách đội ({len(game.teams)})")
        
        sorted_teams = sorted(game.teams.items(), key=lambda x: x[1], reverse=True)
        for name, score in sorted_teams:
            st.markdown(f"""
            <div class="team-card">
                <b>{name}</b><br>
                <span style="font-size: 24px; font-weight: bold; color: #1E3A8A">{score}</span> điểm
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("🔄 Reset Game Mới"):
            game.reset_game()
            st.rerun()

    # 2. KHU VỰC CHÍNH
    if game.mode == "WAITING":
        st.info("Đang chờ học sinh tham gia... (Màn hình tự làm mới mỗi giây)")
        if len(game.teams) > 0:
            if st.button("BẮT ĐẦU GAME NGAY", type="primary", use_container_width=True):
                game.start_game()
                st.rerun()
        
        # Auto-refresh cho màn hình chờ
        time.sleep(1)
        st.rerun()

    else:
        # Lấy dữ liệu câu hỏi hiện tại
        q_data = game.questions[game.current_q_index]
        team_list = list(game.teams.keys())
        
        if not team_list:
            st.error("Không có đội nào!")
            st.stop()
            
        current_turn_team = team_list[game.turn_index % len(team_list)]

        # --- THANH TRẠNG THÁI ---
        if game.mode == "QUESTION":
            st.markdown(f'<div class="status-box" style="background-color: #3B82F6;">Lượt của: {current_turn_team}</div>', unsafe_allow_html=True)
        elif game.mode == "STEAL":
            st.markdown('<div class="status-box" style="background-color: #EF4444; animation: pulse 1s infinite;">🚨 ĐANG CƯỚP QUYỀN! Đợi học sinh bấm chuông...</div>', unsafe_allow_html=True)
            # Auto-refresh để bắt tín hiệu bấm chuông
            time.sleep(0.5)
            st.rerun()
        elif game.mode == "LOCKED":
            st.markdown(f'<div class="status-box" style="background-color: #F59E0B;">⚡ {game.buzzer_winner} GIÀNH ĐƯỢC QUYỀN!</div>', unsafe_allow_html=True)
        elif game.mode == "RESULT":
            color = "#10B981" if "✅" in game.last_result else "#EF4444"
            st.markdown(f'<div class="status-box" style="background-color: {color};">{game.last_result}</div>', unsafe_allow_html=True)

        # --- HIỂN THỊ CÂU HỎI ---
        col_q, col_ans = st.columns([2, 1])
        
        with col_q:
            st.markdown(f"### Câu {game.current_q_index + 1}/80")
            st.info(q_data['q'])
            if q_data['code']:
                st.code(q_data['code'], language="python")

        # --- BẢNG CHẤM ĐIỂM (BUTTONS) ---
        with col_ans:
            st.write("### Giáo viên chọn đáp án:")
            
            if game.mode == "RESULT":
                if st.button("Câu tiếp theo ➡️", type="primary", use_container_width=True):
                    game.next_question()
                    st.rerun()
            elif game.mode == "STEAL":
                if st.button("Bỏ qua (Không ai trả lời)", use_container_width=True):
                    game.next_question() # Hoặc xử lý logic khác
                    st.rerun()
            else:
                # Hiển thị 4 nút đáp án
                # Dùng index để tạo key duy nhất tránh lỗi Streamlit
                for idx, opt in enumerate(q_data['opts']):
                    # Nút bấm sẽ gọi check_answer
                    if st.button(f"{chr(65+idx)}. {opt}", key=f"ans_{idx}", use_container_width=True):
                        game.check_answer(opt)
                        st.rerun()

        # Hiển thị đáp án đúng (chỉ giáo viên thấy)
        with st.expander("👁️ Xem đáp án đúng"):
            st.write(f"Đáp án: **{q_data['ans']}**")

# --- GIAO DIỆN HỌC SINH (PLAYER) ---
else:
    st.header("📱 HỌC SINH")
    
    if "team_name" not in st.session_state:
        name = st.text_input("Nhập tên đội:", placeholder="Ví dụ: Đội 1")
        if st.button("Vào Phòng") and name:
            if game.register_team(name):
                st.session_state.team_name = name
                st.rerun()
            else:
                st.error("Tên đội đã tồn tại hoặc không hợp lệ.")
    else:
        my_team = st.session_state.team_name
        score = game.teams.get(my_team, 0)
        
        # Header Info
        st.markdown(f"### Đội: {my_team}")
        st.metric("Điểm số", score)
        st.divider()

        # Logic hiển thị theo trạng thái Game
        if game.mode == "WAITING":
            st.info("Đang chờ giáo viên bắt đầu...")
            
        elif game.mode == "QUESTION":
            st.write("👀 Nhìn lên bảng. Đang đợi câu trả lời...")
            
        elif game.mode == "STEAL":
            # Nút bấm chuông KHỔNG LỒ
            st.markdown("""
            <style>
                div.stButton > button:first-child {
                    height: 250px !important;
                    background-color: #ff4b4b !important;
                    color: white !important;
                    font-size: 40px !important;
                    border: 5px solid white !important;
                    box-shadow: 0 0 20px #ff4b4b;
                    animation: pulse 0.5s infinite;
                }
                @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
            </style>
            """, unsafe_allow_html=True)
            
            if st.button("🔔 GIÀNH QUYỀN!"):
                if game.buzz(my_team):
                    st.balloons()
                st.rerun()
                
        elif game.mode == "LOCKED":
            if game.buzzer_winner == my_team:
                st.success("🎉 BẠN ĐÃ GIÀNH ĐƯỢC QUYỀN! TRẢ LỜI NGAY!")
            else:
                st.warning(f"🔒 Đội {game.buzzer_winner} đã giành quyền.")
                
        elif game.mode == "RESULT":
            st.info(f"Kết quả: {game.last_result}")

        # Auto-refresh cho học sinh để cập nhật trạng thái liên tục
        time.sleep(1)
        st.rerun()
