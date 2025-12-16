import streamlit as st
import random
import time
import pandas as pd

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Đấu Trường Python",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(120deg, #d4fc79 0%, #96e6a1 100%);
        background-attachment: fixed;
    }
    .question-card {
        background-color: #ffffff; border-radius: 25px; padding: 40px;
        margin-bottom: 30px; box-shadow: 0 15px 30px rgba(0,0,0,0.1);
        text-align: center; border: 5px solid #10B981;
    }
    .question-text {
        font-size: 40px !important; font-weight: 900 !important;
        color: #064E3B; line-height: 1.4;
    }
    .code-container {
        background-color: #1E293B; color: #FACC15; padding: 25px;
        border-radius: 15px; font-family: 'Consolas', 'Courier New', monospace;
        font-size: 32px; font-weight: bold; text-align: left;
        margin: 20px auto; width: 90%; border-left: 10px solid #F59E0B;
        white-space: pre-wrap; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }
    div.stButton > button {
        width: 100%; height: 120px; font-size: 35px !important;
        font-weight: 900 !important; border-radius: 20px !important;
        border: 4px solid #ffffff !important; background-color: #3B82F6 !important;
        color: #ffffff !important; box-shadow: 0 8px 0 #1D4ED8, 0 15px 20px rgba(0,0,0,0.2);
        transition: all 0.1s; margin-bottom: 15px;
    }
    div.stButton > button:hover {
        transform: translateY(-4px); background-color: #2563EB !important;
        box-shadow: 0 10px 0 #1D4ED8, 0 20px 25px rgba(0,0,0,0.2);
    }
    div.stButton > button:active {
        transform: translateY(4px); box-shadow: 0 0 0 #1D4ED8, 0 0 0 rgba(0,0,0,0);
    }
    div.stButton > button p { font-size: 35px !important; }
    
    .team-card-wrapper {
        background: #ffffff; border-radius: 15px; padding: 20px;
        margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        display: flex; justify-content: space-between; align-items: center;
        border-left: 15px solid #ccc;
    }
    .team-name-display { font-size: 26px; font-weight: bold; color: #333; }
    .team-score-display { font-size: 36px; font-weight: 900; color: #EF4444; }
    
    .status-banner {
        padding: 20px; border-radius: 50px; text-align: center;
        font-size: 32px; font-weight: 900; color: white;
        margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        text-transform: uppercase; letter-spacing: 2px; border: 4px solid white;
    }
    
    .setup-box {
        background: white; padding: 30px; border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1); margin-bottom: 20px;
    }

    /* CSS cho nút chỉnh điểm nhỏ gọn */
    .small-btn button {
        height: 40px !important;
        width: 40px !important;
        font-size: 18px !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 50% !important;
    }

    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ GAME ---
@st.cache_resource
class GameManager:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.teams = {} 
        self.questions = [] 
        self.current_q_index = 0
        self.mode = "WAITING" 
        self.buzzer_winner = None
        self.last_result = "" 
        self.turn_index = 0
        self.blocked_team = None

    def load_questions_from_file(self, uploaded_file):
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            new_qs = []
            for index, row in df.iterrows():
                code_val = str(row['Code']) if not pd.isna(row['Code']) else None
                opts = [str(row['A']), str(row['B']), str(row['C']), str(row['D'])]
                display_opts = opts.copy()
                random.shuffle(display_opts)

                new_qs.append({
                    "q": str(row['CauHoi']),
                    "code": code_val,
                    "ans": str(row['DapAnDung']),
                    "opts": display_opts
                })
            
            if len(new_qs) > 0:
                self.questions = new_qs
                self.current_q_index = 0
                return True, f"Đã tải {len(new_qs)} câu hỏi."
            return False, "File rỗng."
        except Exception as e:
            return False, f"Lỗi: {e}"

    def use_sample_questions(self):
        qs = []
        qs.append({"q": "Kết quả của biểu thức logic sau?", "code": "print(10 > 5 and not 3 < 1)", "ans": "True", "opts": ["True", "False", "Error", "None"]})
        qs.append({"q": "Vòng lặp sau in ra kết quả gì?", "code": "for i in range(1, 4):\n    print(i, end=' ')", "ans": "1 2 3", "opts": ["1 2 3", "1 2 3 4", "0 1 2", "123"]})
        qs.append({"q": "Giá trị cuối cùng của k là bao nhiêu?", "code": "k = 0\nwhile k < 6:\n    k = k + 2", "ans": "6", "opts": ["4", "5", "6", "Loop vô hạn"]})
        self.questions = qs
        return len(qs)

    def register_team(self, name):
        # Cho phép đăng ký lại (Reconnect) nếu tên đã tồn tại
        if name:
            if name not in self.teams:
                self.teams[name] = 0 # Đội mới
            # Nếu tên đã có, vẫn trả về True để học sinh vào lại được (giữ nguyên điểm)
            return True
        return False
    
    def adjust_score(self, team_name, points):
        if team_name in self.teams:
            self.teams[team_name] += points

    def buzz(self, team_name):
        if team_name == self.blocked_team: return False
        if self.mode == "STEAL":
            self.mode = "LOCKED"
            self.buzzer_winner = team_name
            return True
        return False

    def check_answer(self, selected_opt):
        current_q = self.questions[self.current_q_index]
        correct_ans = current_q['ans']
        team_list = list(self.teams.keys())
        active_team = self.buzzer_winner if self.mode == "LOCKED" else team_list[self.turn_index % len(team_list)]
        
        if str(selected_opt).strip() == str(correct_ans).strip():
            self.teams[active_team] += 10
            self.last_result = f"🎉 CHÍNH XÁC! {active_team} +10 ĐIỂM"
            self.mode = "RESULT" 
        else:
            self.last_result = f"😓 SAI RỒI! ĐÁP ÁN: {correct_ans}"
            if self.mode == "QUESTION":
                self.mode = "STEAL"
                self.buzzer_winner = None
                self.blocked_team = active_team
            else:
                self.mode = "RESULT"

    def next_question(self):
        self.current_q_index = (self.current_q_index + 1) % len(self.questions)
        self.turn_index += 1
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
    
    # 1. GIAO DIỆN PHÒNG CHỜ & SETUP
    if game.mode == "WAITING":
        st.markdown("<h1 style='text-align: center; color: #064E3B; font-size: 50px;'>🛠️ THIẾT LẬP TRẬN ĐẤU</h1>", unsafe_allow_html=True)
        
        col_setup, col_lobby = st.columns([1, 1], gap="large")
        
        with col_setup:
            st.markdown('<div class="setup-box">', unsafe_allow_html=True)
            st.subheader("1. Nạp Ngân Hàng Câu Hỏi")
            
            tab1, tab2 = st.tabs(["📂 Tải File Excel/CSV", "⚡ Dùng Câu Hỏi Mẫu"])
            
            with tab1:
                uploaded_file = st.file_uploader("Chọn file câu hỏi", type=['csv', 'xlsx'])
                if uploaded_file is not None:
                    success, msg = game.load_questions_from_file(uploaded_file)
                    if success: st.success(msg)
                    else: st.error(msg)
            
            with tab2:
                if st.button("Sử dụng bộ câu hỏi mẫu"):
                    count = game.use_sample_questions()
                    st.success(f"Đã nạp {count} câu hỏi mẫu!")
            
            if game.questions:
                st.info(f"✅ Đã sẵn sàng: **{len(game.questions)}** câu hỏi.")
            else:
                st.warning("⚠️ Chưa có câu hỏi.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_lobby:
            st.markdown('<div class="setup-box">', unsafe_allow_html=True)
            st.subheader("2. Kết Nối Đội Chơi")
            st.write("Học sinh truy cập vào:")
            st.code("https://python-arena.streamlit.app/", language="text")
            
            st.markdown("---")
            st.write(f"**Danh sách đội ({len(game.teams)}):**")
            
            if not game.teams:
                st.info("Đang chờ kết nối...")
            else:
                cols = st.columns(2)
                for i, team in enumerate(game.teams):
                    cols[i%2].success(f"📍 {team}")
            
            st.markdown("---")
            start_disabled = (len(game.questions) == 0 or len(game.teams) == 0)
            
            if st.button("🚀 BẮT ĐẦU TRẬN ĐẤU", type="primary", disabled=start_disabled, use_container_width=True):
                game.start_game()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        time.sleep(1)
        st.rerun()

    # 2. GIAO DIỆN TRÌNH CHIẾU
    else:
        # SIDEBAR: Quản lý điểm thủ công
        with st.sidebar:
            st.header("⚙️ QUẢN LÝ ĐIỂM")
            if st.button("🔄 Reset Game"):
                game.reset_game()
                st.rerun()
            st.divider()
            st.write("Cập nhật điểm thủ công:")
            
            # Danh sách đội với nút +/-
            sorted_teams_ctrl = sorted(game.teams.items(), key=lambda x: x[0]) # Sắp xếp theo tên để dễ tìm
            for name, score in sorted_teams_ctrl:
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{name}**: {score}")
                # Sử dụng container css class 'small-btn' nếu cần chỉnh style
                if c2.button("➕", key=f"add_{name}"):
                    game.adjust_score(name, 10)
                    st.rerun()
                if c3.button("➖", key=f"sub_{name}"):
                    game.adjust_score(name, -10)
                    st.rerun()
            st.divider()

        col_score, col_stage = st.columns([1, 3], gap="large")

        # --- BẢNG ĐIỂM (HIỂN THỊ) ---
        with col_score:
            st.markdown("<h2 style='color:#064E3B; text-align:center;'>🏆 XẾP HẠNG</h2>", unsafe_allow_html=True)
            sorted_teams = sorted(game.teams.items(), key=lambda x: x[1], reverse=True)
            colors = ["#F59E0B", "#94A3B8", "#B45309", "#FFFFFF"] 
            team_list = list(game.teams.keys())

            for idx, (name, score) in enumerate(sorted_teams):
                border_color = colors[idx] if idx < 3 else "#ccc"
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

        # --- SÂN KHẤU CHÍNH ---
        with col_stage:
            q_data = game.questions[game.current_q_index]
            current_turn_team = team_list[game.turn_index % len(team_list)]

            if game.mode == "QUESTION":
                st.markdown(f'<div class="status-banner" style="background: #3B82F6;">LƯỢT CỦA: {current_turn_team}</div>', unsafe_allow_html=True)
            elif game.mode == "STEAL":
                blocked_msg = f"<br><span style='font-size:18px'>(Đội {game.blocked_team} mất lượt)</span>" if game.blocked_team else ""
                st.markdown(f'<div class="status-banner" style="background: #EF4444; animation: pulse 1s infinite;">🚨 CƯỚP QUYỀN! {blocked_msg}</div>', unsafe_allow_html=True)
                time.sleep(0.5)
                st.rerun()
            elif game.mode == "LOCKED":
                st.markdown(f'<div class="status-banner" style="background: #F59E0B;">⚡ {game.buzzer_winner} GIÀNH QUYỀN!</div>', unsafe_allow_html=True)
            elif game.mode == "RESULT":
                bg = "#10B981" if "CHÍNH XÁC" in game.last_result else "#EF4444"
                st.markdown(f'<div class="status-banner" style="background: {bg};">{game.last_result}</div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="question-card">
                <div style="font-size: 24px; color: #64748B; margin-bottom: 10px; font-weight:bold;">CÂU HỎI {game.current_q_index + 1}/{len(game.questions)}</div>
                <div class="question-text">{q_data['q']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if q_data['code']:
                st.markdown(f'<div class="code-container">{q_data["code"]}</div>', unsafe_allow_html=True)

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
        name = st.text_input("Tên đội (Nếu vào lại hãy nhập đúng tên cũ):", placeholder="VD: Team 1")
        if st.button("VÀO PHÒNG NGAY", type="primary", use_container_width=True) and name:
            # Luôn trả về True để cho phép Reconnect
            game.register_team(name)
            st.session_state.team_name = name
            st.rerun()
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
            if my_team == game.blocked_team:
                st.error("🚫 ĐỘI BẠN VỪA TRẢ LỜI SAI, KHÔNG ĐƯỢC CƯỚP!")
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
