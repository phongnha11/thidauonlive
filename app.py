import streamlit as st
import random
import time

# --- CẤU HÌNH TRANG (FULL SCREEN MODE) ---
st.set_page_config(
    page_title="Đấu Trường Python",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="collapsed" # Thu gọn sidebar để ưu tiên trình chiếu
)

# --- CSS TÙY CHỈNH CAO CẤP (GIAO DIỆN GAME SHOW) ---
st.markdown("""
<style>
    /* 1. NỀN TRANG WEB: Gradient Xanh Tím Đậm chất Công Nghệ */
    .stApp {
        background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 2. KHUNG CÂU HỎI */
    .question-card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        text-align: center;
        border: 4px solid #3B82F6;
    }
    .question-text {
        font-size: 32px !important;
        font-weight: 900 !important;
        color: #1e3a8a;
        line-height: 1.4;
    }

    /* 3. CODE BLOCK */
    .code-container {
        background-color: #1e293b;
        color: #fbbf24;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 24px;
        font-weight: bold;
        text-align: left;
        margin: 15px 0;
        border-left: 5px solid #fbbf24;
    }

    /* 4. NÚT ĐÁP ÁN (A, B, C, D) */
    div.stButton > button {
        width: 100%;
        height: 80px;
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        border: 2px solid rgba(255,255,255,0.2) !important;
        background-color: rgba(255,255,255,0.9) !important;
        color: #1e3a8a !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translateY(-5px);
        background-color: #ffffff !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }

    /* 5. BẢNG ĐIỂM (TEAM CARD) */
    .team-card-wrapper {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        transition: transform 0.3s;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 10px solid #ccc;
    }
    .team-name-display { font-size: 22px; font-weight: bold; color: #333; }
    .team-score-display { font-size: 28px; font-weight: 900; color: #d32f2f; }
    
    /* 6. TRẠNG THÁI (STATUS BAR) */
    .status-banner {
        padding: 15px;
        border-radius: 50px;
        text-align: center;
        font-size: 28px; 
        font-weight: 900;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 2px;
    }

</style>
""", unsafe_allow_html=True)

# --- LOGIC GAME (GIỮ NGUYÊN TỪ PHIÊN BẢN TRƯỚC) ---
@st.cache_resource
class GameManager:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.teams = {} 
        self.questions = self.generate_questions()
        self.current_q_index = 0
        self.mode = "WAITING" 
        self.buzzer_winner = None
        self.last_result = "" 
        self.turn_index = 0 

    def generate_questions(self):
        qs = []
        # Câu hỏi mẫu
        qs.append({"q": "Kết quả của: print(10 > 5 and not 3 < 1)", "code": None, "ans": "True", "opts": ["True", "False", "Error", "None"]})
        qs.append({"q": "Output vòng lặp?", "code": "for i in range(1, 4):\n    print(i, end='')", "ans": "123", "opts": ["123", "1234", "0123", "1 2 3"]})
        qs.append({"q": "Giá trị k cuối cùng?", "code": "k = 0\nwhile k < 5:\n    k += 2", "ans": "6", "opts": ["4", "5", "6", "Loop"]})
        qs.append({"q": "Phép toán: 16 % 3 ** 2", "code": None, "ans": "7", "opts": ["7", "1", "0", "16"]})
        qs.append({"q": "Hàm nào dùng để nhập dữ liệu?", "code": None, "ans": "input()", "opts": ["print()", "input()", "scan()", "read()"]})
        
        for i in range(20):
            a, b = random.randint(10, 50), random.randint(2, 9)
            res = a % b
            qs.append({
                "q": f"Kết quả của {a} % {b} là?", 
                "code": None, 
                "ans": str(res), 
                "opts": [str(res), str(a//b), str(res+1), str(b)]
            })
        
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
        active_team = self.buzzer_winner if self.mode == "LOCKED" else list(self.teams.keys())[self.turn_index % len(self.teams)]
        
        if selected_opt == correct_ans:
            self.teams[active_team] += 10
            self.last_result = f"CHÍNH XÁC! {active_team} +10 ĐIỂM"
            self.mode = "RESULT" 
        else:
            self.last_result = f"SAI RỒI! ĐÁP ÁN: {correct_ans}"
            if self.mode == "QUESTION":
                self.mode = "STEAL"
                self.buzzer_winner = None
            else:
                self.mode = "RESULT"

    def next_question(self):
        self.current_q_index = (self.current_q_index + 1) % len(self.questions)
        self.turn_index += 1 
        self.mode = "QUESTION"
        self.buzzer_winner = None
        self.last_result = ""

    def start_game(self):
        self.mode = "QUESTION"
        self.turn_index = 0

game = GameManager()

# --- PHÂN QUYỀN HOST/PLAYER ---
params = st.query_params
role = params.get("role", "player")

# ==============================================================================
# GIAO DIỆN GIÁO VIÊN (TRÌNH CHIẾU)
# ==============================================================================
if role == "host":
    
    # 1. SIDEBAR: CÔNG CỤ QUẢN TRỊ (Ẩn đi khi trình chiếu)
    with st.sidebar:
        st.header("⚙️ CÔNG CỤ GIÁO VIÊN")
        if st.button("🔄 Reset Game"):
            game.reset_game()
            st.rerun()
        st.divider()
        st.write("Link cho học sinh:")
        st.code("https://python-arena.streamlit.app/", language="text")
        st.info("Mẹo: Nhấn '>' ở góc trên trái để thu gọn thanh này khi trình chiếu.")

    # 2. MÀN HÌNH CHÍNH (GRID LAYOUT)
    # Chia màn hình: Cột 1 (Điểm số - Nhỏ) | Cột 2 (Sân khấu - Lớn)
    col_score, col_stage = st.columns([1, 3], gap="medium")

    # --- CỘT TRÁI: BẢNG ĐIỂM ---
    with col_score:
        st.markdown("<h2 style='color:white; text-align:center;'>🏆 XẾP HẠNG</h2>", unsafe_allow_html=True)
        if not game.teams:
            st.warning("Chưa có đội...")
        
        # Sắp xếp và hiển thị
        sorted_teams = sorted(game.teams.items(), key=lambda x: x[1], reverse=True)
        colors = ["#FFD700", "#C0C0C0", "#CD7F32", "#FFFFFF"] # Vàng, Bạc, Đồng, Trắng
        
        for idx, (name, score) in enumerate(sorted_teams):
            border_color = colors[idx] if idx < 3 else "#ccc"
            # Highlight đội đang đến lượt
            active_style = "transform: scale(1.05); box-shadow: 0 0 15px yellow;" if idx == game.turn_index % len(game.teams) and game.mode == "QUESTION" else ""
            
            st.markdown(f"""
            <div class="team-card-wrapper" style="border-left-color: {border_color}; {active_style}">
                <div class="team-name-display">{name}</div>
                <div class="team-score-display">{score}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- CỘT PHẢI: SÂN KHẤU CHÍNH ---
    with col_stage:
        
        # A. MÀN HÌNH CHỜ
        if game.mode == "WAITING":
            st.markdown("""
            <div style='text-align:center; padding: 50px; background: rgba(255,255,255,0.1); border-radius: 20px;'>
                <h1 style='font-size: 60px; color: #FBBF24;'>ĐẤU TRƯỜNG PYTHON</h1>
                <h3 style='color: white;'>Đang chờ các đội kết nối...</h3>
                <div style='font-size: 20px; color: #ddd;'>Giáo viên hãy kiểm tra danh sách đội bên trái</div>
            </div>
            """, unsafe_allow_html=True)
            
            if len(game.teams) > 0:
                st.write("") # Spacer
                if st.button("🚀 BẮT ĐẦU TRẬN ĐẤU", type="primary", use_container_width=True):
                    game.start_game()
                    st.rerun()
            time.sleep(1)
            st.rerun()

        # B. MÀN HÌNH THI ĐẤU
        else:
            q_data = game.questions[game.current_q_index]
            team_list = list(game.teams.keys())
            if not team_list: st.stop()
            current_turn_team = team_list[game.turn_index % len(team_list)]

            # 1. THANH TRẠNG THÁI (STATUS BANNER)
            if game.mode == "QUESTION":
                st.markdown(f'<div class="status-banner" style="background: linear-gradient(90deg, #3B82F6, #2563EB);">LƯỢT CỦA: {current_turn_team}</div>', unsafe_allow_html=True)
            elif game.mode == "STEAL":
                st.markdown('<div class="status-banner" style="background: linear-gradient(90deg, #EF4444, #B91C1C); animation: pulse 1s infinite;">🚨 CƯỚP QUYỀN! AI NHANH TAY HƠN?</div>', unsafe_allow_html=True)
                time.sleep(0.5)
                st.rerun()
            elif game.mode == "LOCKED":
                st.markdown(f'<div class="status-banner" style="background: linear-gradient(90deg, #F59E0B, #D97706);">⚡ {game.buzzer_winner} GIÀNH QUYỀN!</div>', unsafe_allow_html=True)
            elif game.mode == "RESULT":
                bg = "linear-gradient(90deg, #10B981, #059669)" if "CHÍNH XÁC" in game.last_result else "linear-gradient(90deg, #EF4444, #B91C1C)"
                st.markdown(f'<div class="status-banner" style="background: {bg};">{game.last_result}</div>', unsafe_allow_html=True)

            # 2. KHUNG CÂU HỎI (QUESTION CARD)
            st.markdown(f"""
            <div class="question-card">
                <div style="font-size: 20px; color: #666; margin-bottom: 10px;">CÂU HỎI {game.current_q_index + 1}/80</div>
                <div class="question-text">{q_data['q']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if q_data['code']:
                st.markdown(f'<div class="code-container">{q_data["code"]}</div>', unsafe_allow_html=True)

            # 3. LƯỚI ĐÁP ÁN (4 BUTTONS)
            st.write("") # Spacer
            
            # Xử lý hiển thị nút bấm
            if game.mode == "RESULT":
                # Nút chuyển câu (Full width)
                if st.button("CÂU TIẾP THEO ➡️", type="primary", use_container_width=True):
                    game.next_question()
                    st.rerun()
            elif game.mode == "STEAL":
                if st.button("BỎ QUA (KHÔNG AI TRẢ LỜI ĐƯỢC)", use_container_width=True):
                    game.next_question()
                    st.rerun()
            else:
                # Hiển thị 4 đáp án dạng lưới 2x2
                c1, c2 = st.columns(2, gap="small")
                opts = q_data['opts']
                
                with c1:
                    if st.button(f"A. {opts[0]}", use_container_width=True): game.check_answer(opts[0]); st.rerun()
                    if st.button(f"C. {opts[2]}", use_container_width=True): game.check_answer(opts[2]); st.rerun()
                with c2:
                    if st.button(f"B. {opts[1]}", use_container_width=True): game.check_answer(opts[1]); st.rerun()
                    if st.button(f"D. {opts[3]}", use_container_width=True): game.check_answer(opts[3]); st.rerun()

            # Footer
            st.markdown("<div style='text-align: right; color: rgba(255,255,255,0.5); margin-top: 20px;'>Python Arena v2.0</div>", unsafe_allow_html=True)

# ==============================================================================
# GIAO DIỆN HỌC SINH (PLAYER) - MOBILE OPTIMIZED
# ==============================================================================
else:
    # Ẩn sidebar trên mobile
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            .mobile-header { background: white; padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        </style>
    """, unsafe_allow_html=True)

    if "team_name" not in st.session_state:
        st.markdown("<h1 style='color: white; text-align: center;'>📱 THAM GIA</h1>", unsafe_allow_html=True)
        name = st.text_input("Tên đội:", placeholder="VD: Team 1")
        if st.button("VÀO PHÒNG NGAY", type="primary", use_container_width=True) and name:
            if game.register_team(name):
                st.session_state.team_name = name
                st.rerun()
            else:
                st.error("Tên này đã có người dùng!")
    else:
        my_team = st.session_state.team_name
        
        # Header Info Mobile
        st.markdown(f"""
        <div class="mobile-header">
            <div style="font-size: 14px; color: #666;">ĐỘI CỦA BẠN</div>
            <div style="font-size: 24px; font-weight: 900; color: #1E3A8A;">{my_team}</div>
            <div style="font-size: 18px; font-weight: bold; color: #EF4444;">{game.teams.get(my_team, 0)} điểm</div>
        </div>
        """, unsafe_allow_html=True)

        # BUTTON AREA
        if game.mode == "STEAL":
            st.markdown("""
            <style>
                div.stButton > button:first-child {
                    height: 300px !important;
                    background: radial-gradient(circle, #ff4b4b 0%, #b91c1c 100%) !important;
                    color: white !important;
                    font-size: 40px !important;
                    border: 8px solid white !important;
                    border-radius: 50% !important;
                    box-shadow: 0 0 30px #ff4b4b;
                    animation: pulse 0.5s infinite;
                }
            </style>
            """, unsafe_allow_html=True)
            if st.button("BẤM!"):
                if game.buzz(my_team):
                    st.balloons()
                st.rerun()
        
        elif game.mode == "LOCKED":
            if game.buzzer_winner == my_team:
                st.success("🎉 BẠN ĐÃ GIÀNH QUYỀN! TRẢ LỜI ĐI!")
            else:
                st.error(f"🔒 CHẬM MẤT RỒI! ({game.buzzer_winner})")
        
        elif game.mode == "QUESTION":
            st.info("👀 HÃY NHÌN LÊN BẢNG...")
        
        elif game.mode == "RESULT":
            st.write(f"Kết quả: {game.last_result}")
        
        else:
            st.write("Đang chờ...")

        time.sleep(1)
        st.rerun()
