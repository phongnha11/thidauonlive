import streamlit as st
import random
import time
import pandas as pd

# --- CẤU HÌNH TRANG (FULL SCREEN MODE) ---
st.set_page_config(
    page_title="Đấu Trường Python",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TÙY CHỈNH CAO CẤP (GIAO DIỆN LỚP HỌC TƯƠI SÁNG) ---
st.markdown("""
<style>
    /* 1. NỀN TRANG WEB: Gradient Xanh Tươi Sáng */
    .stApp {
        background: linear-gradient(120deg, #d4fc79 0%, #96e6a1 100%);
        background-attachment: fixed;
    }

    /* 2. KHUNG CÂU HỎI */
    .question-card {
        background-color: #ffffff;
        border-radius: 25px;
        padding: 40px;
        margin-bottom: 30px;
        box-shadow: 0 15px 30px rgba(0,0,0,0.1);
        text-align: center;
        border: 5px solid #10B981;
    }
    .question-text {
        font-size: 40px !important;
        font-weight: 900 !important;
        color: #064E3B;
        line-height: 1.4;
    }

    /* 3. CODE BLOCK */
    .code-container {
        background-color: #1E293B;
        color: #FACC15;
        padding: 25px;
        border-radius: 15px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 32px;
        font-weight: bold;
        text-align: left;
        margin: 20px auto;
        width: 90%;
        border-left: 10px solid #F59E0B;
        white-space: pre-wrap;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }

    /* 4. NÚT ĐÁP ÁN */
    div.stButton > button {
        width: 100%;
        height: 120px;
        font-size: 35px !important;
        font-weight: 900 !important;
        border-radius: 20px !important;
        border: 4px solid #ffffff !important;
        background-color: #3B82F6 !important;
        color: #ffffff !important;
        box-shadow: 0 8px 0 #1D4ED8, 0 15px 20px rgba(0,0,0,0.2);
        transition: all 0.1s;
        margin-bottom: 15px;
    }
    div.stButton > button:hover {
        transform: translateY(-4px);
        background-color: #2563EB !important;
        box-shadow: 0 10px 0 #1D4ED8, 0 20px 25px rgba(0,0,0,0.2);
    }
    div.stButton > button:active {
        transform: translateY(4px);
        box-shadow: 0 0 0 #1D4ED8, 0 0 0 rgba(0,0,0,0);
    }
    div.stButton > button p {
        font-size: 35px !important;
    }

    /* 5. BẢNG ĐIỂM */
    .team-card-wrapper {
        background: #ffffff;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 15px solid #ccc;
    }
    .team-name-display { font-size: 26px; font-weight: bold; color: #333; }
    .team-score-display { font-size: 36px; font-weight: 900; color: #EF4444; }
    
    /* 6. TRẠNG THÁI */
    .status-banner {
        padding: 20px;
        border-radius: 50px;
        text-align: center;
        font-size: 32px; 
        font-weight: 900;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        text-transform: uppercase;
        letter-spacing: 2px;
        border: 4px solid white;
    }

    /* Ẩn header mặc định */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI GAME (GLOBAL) ---
@st.cache_resource
class GameManager:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.teams = {} 
        self.questions = self.generate_default_questions() # Mặc định dùng câu hỏi mẫu
        self.current_q_index = 0
        self.mode = "WAITING" 
        self.buzzer_winner = None
        self.last_result = "" 
        self.turn_index = 0
        self.blocked_team = None # Đội bị cấm bấm chuông (do trả lời sai trước đó)

    def load_questions_from_file(self, uploaded_file):
        try:
            # Đọc file CSV hoặc Excel
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            new_qs = []
            # Duyệt qua từng dòng trong file
            # Cấu trúc file cần có: CauHoi, Code, DapAnDung, A, B, C, D
            for index, row in df.iterrows():
                # Xử lý code (nếu ô trống thì là None)
                code_val = str(row['Code']) if not pd.isna(row['Code']) else None
                
                # Tạo danh sách đáp án
                opts = [str(row['A']), str(row['B']), str(row['C']), str(row['D'])]
                # Xáo trộn đáp án để hiển thị ngẫu nhiên
                display_opts = opts.copy()
                random.shuffle(display_opts)

                new_qs.append({
                    "q": str(row['CauHoi']),
                    "code": code_val,
                    "ans": str(row['DapAnDung']), # Đáp án đúng để so sánh
                    "opts": display_opts # Đáp án để hiển thị
                })
            
            if len(new_qs) > 0:
                self.questions = new_qs
                self.current_q_index = 0
                return f"Đã tải thành công {len(new_qs)} câu hỏi!"
            else:
                return "File không có dữ liệu."
        except Exception as e:
            return f"Lỗi đọc file: {e}"

    def generate_default_questions(self):
        qs = []
        qs.append({"q": "Kết quả của biểu thức logic sau?", "code": "print(10 > 5 and not 3 < 1)", "ans": "True", "opts": ["True", "False", "Error", "None"]})
        qs.append({"q": "Vòng lặp sau in ra kết quả gì?", "code": "for i in range(1, 4):\n    print(i, end=' ')", "ans": "1 2 3", "opts": ["1 2 3", "1 2 3 4", "0 1 2", "123"]})
        return qs

    def register_team(self, name):
        if name and name not in self.teams:
            self.teams[name] = 0
            return True
        return False
    
    def buzz(self, team_name):
        # Đội bị chặn (trả lời sai) không được bấm
        if team_name == self.blocked_team:
            return False

        if self.mode == "STEAL":
            self.mode = "LOCKED"
            self.buzzer_winner = team_name
            return True
        return False

    def check_answer(self, selected_opt):
        current_q = self.questions[self.current_q_index]
        correct_ans = current_q['ans']
        
        # Xác định đội đang trả lời
        # Nếu là vòng chính: Lấy theo turn_index
        # Nếu là cướp quyền: Lấy đội buzzer_winner
        team_list = list(self.teams.keys())
        active_team = self.buzzer_winner if self.mode == "LOCKED" else team_list[self.turn_index % len(team_list)]
        
        # Chuẩn hóa về string để so sánh
        if str(selected_opt).strip() == str(correct_ans).strip():
            self.teams[active_team] += 10
            self.last_result = f"🎉 CHÍNH XÁC! {active_team} +10 ĐIỂM"
            self.mode = "RESULT" 
        else:
            self.last_result = f"😓 SAI RỒI! ĐÁP ÁN: {correct_ans}"
            
            if self.mode == "QUESTION":
                # Vòng chính sai -> Chuyển sang cướp quyền
                self.mode = "STEAL"
                self.buzzer_winner = None
                self.blocked_team = active_team # Chặn đội vừa sai không được bấm chuông
            else:
                # Cướp quyền mà vẫn sai -> Kết thúc câu
                self.mode = "RESULT"

    def next_question(self):
        self.current_q_index = (self.current_q_index + 1) % len(self.questions)
        self.turn_index += 1 # Xoay vòng lượt chơi
        self.mode = "QUESTION"
        self.buzzer_winner = None
        self.blocked_team = None # Reset chặn
        self.last_result = ""

    def start_game(self):
        self.mode = "QUESTION"
        self.turn_index = 0
        self.blocked_team = None

game = GameManager()

# --- PHÂN QUYỀN HOST/PLAYER ---
params = st.query_params
role = params.get("role", "player")

# ==============================================================================
# GIAO DIỆN GIÁO VIÊN (HOST)
# ==============================================================================
if role == "host":
    
    # 1. SIDEBAR: CÔNG CỤ QUẢN TRỊ
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ")
        
        # Upload File Câu Hỏi
        st.subheader("📂 Thư viện câu hỏi")
        st.markdown("Tải file CSV/Excel (Cột: `CauHoi`, `Code`, `DapAnDung`, `A`, `B`, `C`, `D`)")
        uploaded_file = st.file_uploader("Chọn file", type=['csv', 'xlsx'])
        if uploaded_file is not None:
            msg = game.load_questions_from_file(uploaded_file)
            st.success(msg)

        if st.button("🔄 Reset Game Mới"):
            game.reset_game()
            st.rerun()
            
        st.divider()
        st.write("Link HS:")
        st.code("https://python-arena.streamlit.app/", language="text")

    # 2. MÀN HÌNH CHÍNH
    col_score, col_stage = st.columns([1, 3], gap="large")

    # --- CỘT TRÁI: BẢNG ĐIỂM ---
    with col_score:
        st.markdown("<h2 style='color:#064E3B; text-align:center;'>🏆 XẾP HẠNG</h2>", unsafe_allow_html=True)
        if not game.teams:
            st.info("Chưa có đội...")
        
        # Sắp xếp điểm
        sorted_teams = sorted(game.teams.items(), key=lambda x: x[1], reverse=True)
        colors = ["#F59E0B", "#94A3B8", "#B45309", "#FFFFFF"] 
        team_list = list(game.teams.keys())

        for idx, (name, score) in enumerate(sorted_teams):
            border_color = colors[idx] if idx < 3 else "#ccc"
            
            # Highlight đội đang có lượt (chỉ ở mode QUESTION)
            is_active = False
            if team_list and game.mode == "QUESTION":
                current_turn_team = team_list[game.turn_index % len(team_list)]
                if name == current_turn_team:
                    is_active = True
            
            active_style = "transform: scale(1.05); border: 4px solid #F59E0B;" if is_active else ""
            
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
            <div style='text-align:center; padding: 80px; background: rgba(255,255,255,0.8); border-radius: 30px;'>
                <h1 style='font-size: 70px; color: #059669; margin-bottom: 20px;'>🐍 ĐẤU TRƯỜNG PYTHON</h1>
                <h2 style='color: #374151;'>Đang chờ các đội kết nối...</h2>
            </div>
            """, unsafe_allow_html=True)
            
            if len(game.teams) > 0:
                st.write("") 
                if st.button("🚀 BẮT ĐẦU TRẬN ĐẤU", type="primary", use_container_width=True):
                    game.start_game()
                    st.rerun()
            time.sleep(1)
            st.rerun()

        # B. MÀN HÌNH THI ĐẤU
        else:
            if not game.questions:
                st.error("Chưa có câu hỏi! Hãy tải file lên.")
                st.stop()

            q_data = game.questions[game.current_q_index]
            
            if not team_list: 
                st.error("Chưa có đội nào đăng ký!")
                st.stop()
                
            current_turn_team = team_list[game.turn_index % len(team_list)]

            # 1. THANH TRẠNG THÁI
            if game.mode == "QUESTION":
                st.markdown(f'<div class="status-banner" style="background: #3B82F6;">LƯỢT CỦA: {current_turn_team}</div>', unsafe_allow_html=True)
            elif game.mode == "STEAL":
                # Hiển thị thông báo ai bị cấm
                blocked_msg = f"(Đội {game.blocked_team} không được bấm)" if game.blocked_team else ""
                st.markdown(f'<div class="status-banner" style="background: #EF4444; animation: pulse 1s infinite;">🚨 CƯỚP QUYỀN! {blocked_msg}</div>', unsafe_allow_html=True)
                time.sleep(0.5)
                st.rerun()
            elif game.mode == "LOCKED":
                st.markdown(f'<div class="status-banner" style="background: #F59E0B;">⚡ {game.buzzer_winner} GIÀNH QUYỀN!</div>', unsafe_allow_html=True)
            elif game.mode == "RESULT":
                bg = "#10B981" if "CHÍNH XÁC" in game.last_result else "#EF4444"
                st.markdown(f'<div class="status-banner" style="background: {bg};">{game.last_result}</div>', unsafe_allow_html=True)

            # 2. KHUNG CÂU HỎI & CODE
            st.markdown(f"""
            <div class="question-card">
                <div style="font-size: 24px; color: #64748B; margin-bottom: 10px; font-weight:bold;">CÂU HỎI {game.current_q_index + 1}/{len(game.questions)}</div>
                <div class="question-text">{q_data['q']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if q_data['code']:
                st.markdown(f'<div class="code-container">{q_data["code"]}</div>', unsafe_allow_html=True)

            # 3. LƯỚI ĐÁP ÁN
            st.write("") 
            
            if game.mode == "RESULT":
                if st.button("CÂU TIẾP THEO ➡️", type="primary", use_container_width=True):
                    game.next_question()
                    st.rerun()
            elif game.mode == "STEAL":
                if st.button("BỎ QUA (KHÔNG AI TRẢ LỜI ĐƯỢC)", use_container_width=True):
                    game.next_question()
                    st.rerun()
            else:
                c1, c2 = st.columns(2, gap="medium")
                opts = q_data['opts']
                # Đảm bảo có đủ 4 lựa chọn (nếu file thiếu thì cần handle, ở đây giả định đủ)
                safe_opts = opts + [""] * (4 - len(opts))
                
                with c1:
                    if st.button(f"A. {safe_opts[0]}", use_container_width=True): game.check_answer(safe_opts[0]); st.rerun()
                    if st.button(f"C. {safe_opts[2]}", use_container_width=True): game.check_answer(safe_opts[2]); st.rerun()
                with c2:
                    if st.button(f"B. {safe_opts[1]}", use_container_width=True): game.check_answer(safe_opts[1]); st.rerun()
                    if st.button(f"D. {safe_opts[3]}", use_container_width=True): game.check_answer(safe_opts[3]); st.rerun()

# ==============================================================================
# GIAO DIỆN HỌC SINH (PLAYER)
# ==============================================================================
else:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            header {visibility: hidden;}
            .mobile-header { background: white; padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); border-bottom: 5px solid #10B981; }
        </style>
    """, unsafe_allow_html=True)

    if "team_name" not in st.session_state:
        st.markdown("<h1 style='color: #064E3B; text-align: center; margin-top: 50px;'>📱 THAM GIA</h1>", unsafe_allow_html=True)
        name = st.text_input("Tên đội:", placeholder="VD: Team 1")
        if st.button("VÀO PHÒNG NGAY", type="primary", use_container_width=True) and name:
            if game.register_team(name):
                st.session_state.team_name = name
                st.rerun()
            else:
                st.error("Tên này đã có người dùng!")
    else:
        my_team = st.session_state.team_name
        
        st.markdown(f"""
        <div class="mobile-header">
            <div style="font-size: 16px; color: #64748B; font-weight:bold;">ĐỘI CỦA BẠN</div>
            <div style="font-size: 32px; font-weight: 900; color: #059669;">{my_team}</div>
            <div style="font-size: 24px; font-weight: bold; color: #EF4444;">{game.teams.get(my_team, 0)} điểm</div>
        </div>
        """, unsafe_allow_html=True)

        if game.mode == "STEAL":
            # Kiểm tra xem đội này có bị cấm không
            if my_team == game.blocked_team:
                st.error("🚫 BẠN ĐÃ TRẢ LỜI SAI, KHÔNG ĐƯỢC CƯỚP QUYỀN!")
            else:
                st.markdown("""
                <style>
                    div.stButton > button:first-child {
                        height: 350px !important;
                        background: radial-gradient(circle, #EF4444 0%, #B91C1C 100%) !important;
                        color: white !important;
                        font-size: 50px !important;
                        border: 10px solid white !important;
                        border-radius: 50% !important;
                        box-shadow: 0 0 40px #EF4444;
                        animation: pulse 0.5s infinite;
                    }
                    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
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
            st.info("👀 HÃY NHÌN LÊN BẢNG VÀ SUY NGHĨ...")
        
        elif game.mode == "RESULT":
            if "CHÍNH XÁC" in game.last_result:
                st.success(game.last_result)
            else:
                st.error(game.last_result)
        
        else:
            st.write("Đang chờ giáo viên...")

        time.sleep(1)
        st.rerun()
