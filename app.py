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

# --- CSS TÙY CHỈNH (GIAO DIỆN LỚP HỌC XANH TƯƠI) ---
st.markdown("""
<style>
    /* 1. NỀN TRANG WEB */
    .stApp {
        background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
        background-attachment: fixed;
    }

    /* 2. KHUNG CÂU HỎI */
    .question-card {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        text-align: center;
        border: 4px solid #00acc1;
    }
    .question-text {
        font-size: 36px !important;
        font-weight: 900 !important;
        color: #006064;
        line-height: 1.4;
    }

    /* 3. CODE BLOCK */
    .code-container {
        background-color: #263238;
        color: #ffeb3b;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Consolas', monospace;
        font-size: 28px;
        font-weight: bold;
        text-align: left;
        margin: 15px auto;
        width: 95%;
        border-left: 8px solid #ffca28;
        white-space: pre-wrap;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }

    /* 4. NÚT ĐÁP ÁN (A, B, C, D) */
    div.stButton > button {
        width: 100%;
        height: 100px;
        font-size: 30px !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        border: 3px solid #ffffff !important;
        background-color: #0277bd !important; /* Xanh dương đậm */
        color: #ffffff !important;
        box-shadow: 0 6px 0 #01579b, 0 10px 10px rgba(0,0,0,0.2);
        transition: all 0.1s;
        margin-bottom: 10px;
    }
    div.stButton > button:hover {
        transform: translateY(-3px);
        background-color: #0288d1 !important;
        box-shadow: 0 8px 0 #01579b, 0 15px 15px rgba(0,0,0,0.2);
    }
    div.stButton > button:active {
        transform: translateY(3px);
        box-shadow: 0 0 0 #01579b, 0 0 0 rgba(0,0,0,0);
    }
    div.stButton > button p { font-size: 30px !important; }
    
    /* 5. BẢNG ĐIỂM */
    .team-card-wrapper {
        background: #ffffff;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 10px solid #ccc;
    }
    .team-name-display { font-size: 22px; font-weight: bold; color: #37474f; }
    .team-score-display { font-size: 30px; font-weight: 900; color: #d84315; }
    
    /* 6. THANH TRẠNG THÁI */
    .status-banner {
        padding: 15px;
        border-radius: 50px;
        text-align: center;
        font-size: 28px; 
        font-weight: 900;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        text-transform: uppercase;
        border: 3px solid white;
    }
    
    .setup-box {
        background: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 20px;
    }

    /* Ẩn header mặc định */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI GAME (GLOBAL - SHARED MEMORY) ---
@st.cache_resource
class GameManager:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.teams = {} # { "Tên Đội": điểm }
        self.questions = [] 
        self.current_q_index = 0
        self.mode = "WAITING" # WAITING, QUESTION, STEAL, LOCKED, RESULT
        self.buzzer_winner = None
        self.last_result = "" 
        self.turn_index = 0 # Chỉ số để xác định đội đến lượt (Round Robin)
        self.blocked_team = None # Đội bị cấm bấm chuông (do vừa trả lời sai)

    def load_questions_from_file(self, uploaded_file):
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            new_qs = []
            for index, row in df.iterrows():
                # Xử lý dữ liệu thô
                code_val = str(row['Code']) if 'Code' in row and not pd.isna(row['Code']) else None
                
                # Tạo danh sách đáp án
                opts = [str(row['A']), str(row['B']), str(row['C']), str(row['D'])]
                
                # Xáo trộn vị trí hiển thị của đáp án (để A, B, C, D không cố định)
                display_opts = opts.copy()
                random.shuffle(display_opts)

                new_qs.append({
                    "q": str(row['CauHoi']),
                    "code": code_val,
                    "ans": str(row['DapAnDung']).strip(), # Đáp án gốc để đối chiếu
                    "opts": display_opts # Danh sách đã xáo trộn để hiển thị
                })
            
            if len(new_qs) > 0:
                # Xáo trộn thứ tự câu hỏi trong ngân hàng
                random.shuffle(new_qs)
                self.questions = new_qs
                self.current_q_index = 0
                return True, f"Đã tải và xáo trộn {len(new_qs)} câu hỏi."
            return False, "File không có dữ liệu hợp lệ."
        except Exception as e:
            return False, f"Lỗi đọc file: {e}"

    def use_sample_questions(self):
        qs = []
        qs.append({"q": "Kết quả của: print(10 > 5 and not 3 < 1)", "code": None, "ans": "True", "opts": ["True", "False", "Error", "None"]})
        qs.append({"q": "Vòng lặp sau in ra kết quả gì?", "code": "for i in range(1, 4):\n    print(i, end=' ')", "ans": "1 2 3", "opts": ["1 2 3", "1 2 3 4", "0 1 2", "123"]})
        qs.append({"q": "Giá trị cuối cùng của k?", "code": "k = 0\nwhile k < 6:\n    k = k + 2", "ans": "6", "opts": ["4", "5", "6", "Loop"]})
        
        random.shuffle(qs) # Xáo trộn câu hỏi mẫu
        self.questions = qs
        return len(qs)

    def register_team(self, name):
        # Tính năng Reconnect: Nếu tên đã có, vẫn cho vào (coi như vào lại)
        if name:
            if name not in self.teams:
                self.teams[name] = 0 # Đội mới -> Điểm = 0
            return True
        return False
    
    def adjust_score(self, team_name, points):
        if team_name in self.teams:
            self.teams[team_name] += points

    def buzz(self, team_name):
        # Nếu đang ở chế độ Cướp quyền VÀ đội này không bị cấm
        if self.mode == "STEAL":
            if team_name == self.blocked_team:
                return False # Bị chặn do trả lời sai trước đó
            
            self.mode = "LOCKED"
            self.buzzer_winner = team_name
            return True
        return False

    def check_answer(self, selected_opt):
        current_q = self.questions[self.current_q_index]
        correct_ans = current_q['ans']
        
        # Xác định đội đang trả lời
        # 1. Nếu là vòng chính: Lấy theo thứ tự vòng tròn
        # 2. Nếu là vòng cướp: Lấy đội bấm chuông thắng
        team_list = list(self.teams.keys())
        if not team_list: return

        if self.mode == "LOCKED":
            active_team = self.buzzer_winner
        else:
            active_team = team_list[self.turn_index % len(team_list)]
        
        # So sánh đáp án
        if str(selected_opt).strip() == str(correct_ans).strip():
            # ĐÚNG
            self.teams[active_team] += 10
            self.last_result = f"🎉 CHÍNH XÁC! {active_team} +10 ĐIỂM"
            self.mode = "RESULT" 
        else:
            # SAI
            self.last_result = f"😓 SAI RỒI! ĐÁP ÁN: {correct_ans}"
            
            if self.mode == "QUESTION":
                # Đội chính trả lời sai -> Chặn đội đó -> Mở cướp quyền
                self.blocked_team = active_team
                self.mode = "STEAL"
                self.buzzer_winner = None
            else:
                # Đội cướp quyền trả lời sai -> Kết thúc câu hỏi
                self.mode = "RESULT"

    def next_question(self):
        # Chuyển sang câu tiếp theo
        self.current_q_index = (self.current_q_index + 1) % len(self.questions)
        
        # Chuyển lượt (Round Robin) cho đội kế tiếp trong danh sách
        self.turn_index += 1
        
        # Reset trạng thái
        self.mode = "QUESTION"
        self.buzzer_winner = None
        self.blocked_team = None
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
    
    # --- MÀN HÌNH 1: PHÒNG CHỜ & SETUP ---
    if game.mode == "WAITING":
        st.markdown("<h1 style='text-align: center; color: #006064; font-size: 50px;'>🛠️ THIẾT LẬP TRẬN ĐẤU</h1>", unsafe_allow_html=True)
        
        col_setup, col_lobby = st.columns([1, 1], gap="large")
        
        with col_setup:
            st.markdown('<div class="setup-box">', unsafe_allow_html=True)
            st.subheader("1. Nạp Ngân Hàng Câu Hỏi")
            
            tab1, tab2 = st.tabs(["📂 Tải File Excel/CSV", "⚡ Dùng Câu Hỏi Mẫu"])
            
            with tab1:
                uploaded_file = st.file_uploader("Chọn file (Cột: CauHoi, Code, DapAnDung, A, B, C, D)", type=['csv', 'xlsx'])
                if uploaded_file is not None:
                    success, msg = game.load_questions_from_file(uploaded_file)
                    if success: st.success(msg)
                    else: st.error(msg)
            
            with tab2:
                if st.button("Sử dụng bộ câu hỏi mẫu"):
                    count = game.use_sample_questions()
                    st.success(f"Đã nạp {count} câu hỏi mẫu ngẫu nhiên!")
            
            if game.questions:
                st.info(f"✅ Đã có: **{len(game.questions)}** câu hỏi.")
            else:
                st.warning("⚠️ Chưa có câu hỏi.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_lobby:
            st.markdown('<div class="setup-box">', unsafe_allow_html=True)
            st.subheader("2. Danh Sách Đội")
            st.write("Link cho học sinh: `https://python-arena.streamlit.app/`") # Thay bằng link thật khi deploy
            
            st.markdown("---")
            
            if not game.teams:
                st.info("Đang chờ học sinh kết nối...")
            else:
                # Hiển thị dạng lưới các đội đã vào
                cols = st.columns(2)
                for i, team in enumerate(game.teams):
                    cols[i%2].success(f"📍 {team}")
            
            st.markdown("---")
            
            # Chỉ hiện nút bắt đầu khi đủ điều kiện
            start_disabled = (len(game.questions) == 0 or len(game.teams) == 0)
            if st.button("🚀 BẮT ĐẦU TRẬN ĐẤU", type="primary", disabled=start_disabled, use_container_width=True):
                game.start_game()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        time.sleep(1)
        st.rerun()

    # --- MÀN HÌNH 2: TRẬN ĐẤU (GAME BOARD) ---
    else:
        # Sidebar: Quản lý điểm thủ công
        with st.sidebar:
            st.header("⚙️ QUẢN LÝ")
            if st.button("🔄 Reset Game"):
                game.reset_game()
                st.rerun()
            
            st.divider()
            st.subheader("Chỉnh điểm thủ công")
            sorted_teams_ctrl = sorted(game.teams.items(), key=lambda x: x[0]) 
            for name, score in sorted_teams_ctrl:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{name}**: {score}")
                if c2.button("➕", key=f"add_{name}"):
                    game.adjust_score(name, 10)
                    st.rerun()
                if c3.button("➖", key=f"sub_{name}"):
                    game.adjust_score(name, -10)
                    st.rerun()

        # Layout chính: 25% Bảng điểm - 75% Sân khấu
        col_score, col_stage = st.columns([1, 3], gap="large")

        # --- CỘT TRÁI: BẢNG ĐIỂM ---
        with col_score:
            st.markdown("<h2 style='color:#006064; text-align:center;'>🏆 XẾP HẠNG</h2>", unsafe_allow_html=True)
            
            # Sắp xếp theo điểm giảm dần
            sorted_teams = sorted(game.teams.items(), key=lambda x: x[1], reverse=True)
            colors = ["#FFD700", "#C0C0C0", "#CD7F32", "#FFFFFF"] 
            team_list = list(game.teams.keys())

            for idx, (name, score) in enumerate(sorted_teams):
                border_color = colors[idx] if idx < 3 else "#ccc"
                
                # Highlight đội đang đến lượt (chỉ ở mode QUESTION)
                is_active = False
                if team_list and game.mode == "QUESTION":
                    current_turn_team = team_list[game.turn_index % len(team_list)]
                    if name == current_turn_team: is_active = True
                
                active_style = "transform: scale(1.05); border: 4px solid #F59E0B;" if is_active else ""
                
                st.markdown(f"""
                <div class="team-card-wrapper" style="border-left-color: {border_color}; {active_style}">
                    <div class="team-name-display">{name}</div>
                    <div class="team-score-display">{score}</div>
                </div>
                """, unsafe_allow_html=True)

        # --- CỘT PHẢI: SÂN KHẤU CHÍNH ---
        with col_stage:
            q_data = game.questions[game.current_q_index]
            current_turn_team = team_list[game.turn_index % len(team_list)]

            # 1. THANH TRẠNG THÁI
            if game.mode == "QUESTION":
                st.markdown(f'<div class="status-banner" style="background: #0288d1;">LƯỢT CỦA: {current_turn_team}</div>', unsafe_allow_html=True)
            
            elif game.mode == "STEAL":
                # Hiển thị ai bị cấm
                blocked_msg = f"<br><span style='font-size:20px'>(Đội {game.blocked_team} trả lời sai - Mất quyền bấm)</span>" if game.blocked_team else ""
                st.markdown(f'<div class="status-banner" style="background: #d32f2f; animation: pulse 1s infinite;">🚨 CƯỚP QUYỀN! AI NHANH TAY? {blocked_msg}</div>', unsafe_allow_html=True)
                time.sleep(0.5) # Refresh nhanh để bắt tín hiệu
                st.rerun()
            
            elif game.mode == "LOCKED":
                st.markdown(f'<div class="status-banner" style="background: #f57c00;">⚡ {game.buzzer_winner} GIÀNH QUYỀN!</div>', unsafe_allow_html=True)
            
            elif game.mode == "RESULT":
                bg = "#2e7d32" if "CHÍNH XÁC" in game.last_result else "#c62828"
                st.markdown(f'<div class="status-banner" style="background: {bg};">{game.last_result}</div>', unsafe_allow_html=True)

            # 2. KHUNG CÂU HỎI
            st.markdown(f"""
            <div class="question-card">
                <div style="font-size: 24px; color: #546e7a; margin-bottom: 10px; font-weight:bold;">CÂU HỎI {game.current_q_index + 1}/{len(game.questions)}</div>
                <div class="question-text">{q_data['q']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if q_data['code']:
                st.markdown(f'<div class="code-container">{q_data["code"]}</div>', unsafe_allow_html=True)

            st.write("") 
            
            # 3. NÚT ĐÁP ÁN / ĐIỀU KHIỂN
            if game.mode == "RESULT":
                if st.button("CÂU TIẾP THEO ➡️", type="primary", use_container_width=True):
                    game.next_question()
                    st.rerun()
            
            elif game.mode == "STEAL":
                if st.button("BỎ QUA (KHÔNG AI TRẢ LỜI ĐƯỢC)", use_container_width=True):
                    game.next_question()
                    st.rerun()
            
            else:
                # Layout 2x2 cho đáp án
                c1, c2 = st.columns(2, gap="medium")
                opts = q_data['opts']
                # Xử lý an toàn nếu thiếu đáp án
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
    # Ẩn các thành phần thừa trên mobile
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            header {visibility: hidden;}
            .mobile-header { background: white; padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); border-bottom: 5px solid #00acc1; }
        </style>
    """, unsafe_allow_html=True)

    if "team_name" not in st.session_state:
        st.markdown("<h1 style='color: #006064; text-align: center; margin-top: 50px;'>📱 THAM GIA</h1>", unsafe_allow_html=True)
        name = st.text_input("Tên đội:", placeholder="VD: Team 1")
        
        # Nút vào phòng
        if st.button("VÀO PHÒNG NGAY", type="primary", use_container_width=True) and name:
            game.register_team(name) # Luôn gọi để đăng ký hoặc xác nhận tồn tại
            st.session_state.team_name = name
            st.rerun()
            
    else:
        my_team = st.session_state.team_name
        # Lấy điểm hiện tại
        current_score = game.teams.get(my_team, 0)
        
        # Header Info Mobile
        st.markdown(f"""
        <div class="mobile-header">
            <div style="font-size: 16px; color: #546e7a; font-weight:bold;">ĐỘI CỦA BẠN</div>
            <div style="font-size: 32px; font-weight: 900; color: #00838f;">{my_team}</div>
            <div style="font-size: 24px; font-weight: bold; color: #d84315;">{current_score} điểm</div>
        </div>
        """, unsafe_allow_html=True)

        # KHU VỰC NÚT BẤM
        if game.mode == "STEAL":
            # Kiểm tra xem đội mình có bị cấm không
            if my_team == game.blocked_team:
                st.error("🚫 ĐỘI BẠN VỪA TRẢ LỜI SAI, KHÔNG ĐƯỢC CƯỚP QUYỀN NÀY!")
            else:
                # Nút bấm chuông siêu to
                st.markdown("""
                <style>
                    div.stButton > button:first-child {
                        height: 300px !important;
                        background: radial-gradient(circle, #ff5252 0%, #b71c1c 100%) !important;
                        color: white !important;
                        font-size: 40px !important;
                        border: 8px solid white !important;
                        border-radius: 50% !important;
                        box-shadow: 0 0 40px #ff5252;
                        animation: pulse 0.6s infinite;
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
                st.error(f"🔒 CHẬM MẤT RỒI! ({game.buzzer_winner} ĐÃ GIÀNH)")
        
        elif game.mode == "QUESTION":
            st.info("👀 HÃY NHÌN LÊN BẢNG VÀ SUY NGHĨ...")
        
        elif game.mode == "RESULT":
            if "CHÍNH XÁC" in game.last_result:
                st.success(game.last_result)
            else:
                st.error(game.last_result)
        
        else:
            st.write("Đang chờ giáo viên...")

        # Auto-refresh cho học sinh
        time.sleep(1)
        st.rerun()
