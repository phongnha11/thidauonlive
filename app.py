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
    
    /* KHUNG CÂU HỎI */
    .question-card {
        background-color: #ffffff; border-radius: 25px; padding: 40px;
        margin-bottom: 30px; box-shadow: 0 15px 30px rgba(0,0,0,0.1);
        text-align: center; border: 5px solid #10B981;
    }
    .question-text {
        font-size: 40px !important; font-weight: 900 !important;
        color: #064E3B; line-height: 1.4;
    }
    
    /* CODE BLOCK */
    .code-container {
        background-color: #1E293B; color: #FACC15; padding: 25px;
        border-radius: 15px; font-family: 'Consolas', 'Courier New', monospace;
        font-size: 32px; font-weight: bold; text-align: left;
        margin: 20px auto; width: 90%; border-left: 10px solid #F59E0B;
        white-space: pre-wrap; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }
    
    /* NÚT ĐÁP ÁN (GIÁO VIÊN) */
    .host-btn button {
        width: 100%; height: 120px; font-size: 35px !important;
        font-weight: 900 !important; border-radius: 20px !important;
        border: 4px solid #ffffff !important; background-color: #3B82F6 !important;
        color: #ffffff !important; box-shadow: 0 8px 0 #1D4ED8, 0 15px 20px rgba(0,0,0,0.2);
        transition: all 0.1s; margin-bottom: 15px;
    }
    .host-btn button:hover {
        transform: translateY(-4px); background-color: #2563EB !important;
        box-shadow: 0 10px 0 #1D4ED8, 0 20px 25px rgba(0,0,0,0.2);
    }
    .host-btn button:active {
        transform: translateY(4px); box-shadow: 0 0 0 #1D4ED8, 0 0 0 rgba(0,0,0,0);
    }
    
    /* BẢNG ĐIỂM */
    .team-card-wrapper {
        background: #ffffff; border-radius: 15px; padding: 20px;
        margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        display: flex; justify-content: space-between; align-items: center;
        border-left: 15px solid #ccc;
    }
    .team-name-display { font-size: 26px; font-weight: bold; color: #333; }
    .team-score-display { font-size: 36px; font-weight: 900; color: #EF4444; }
    
    /* THANH TRẠNG THÁI */
    .status-banner {
        padding: 20px; border-radius: 50px; text-align: center;
        font-size: 32px; font-weight: 900; color: white;
        margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        text-transform: uppercase; letter-spacing: 2px; border: 4px solid white;
    }
    
    /* NÚT CHỈNH ĐIỂM NHỎ */
    div[data-testid="column"] button.small-btn {
        height: 40px !important; width: 40px !important; min-height: 0px !important;
        font-size: 20px !important; padding: 0px !important; line-height: 1 !important;
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
        self.is_teams_created = False

    def init_teams(self, num_teams):
        self.teams = {}
        for i in range(1, num_teams + 1):
            self.teams[f"Đội {i}"] = 0
        self.is_teams_created = True

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
        qs.append({"q": "Kết quả của: print(10 > 5 and not 3 < 1)", "code": None, "ans": "True", "opts": ["True", "False", "Error", "None"]})
        qs.append({"q": "Vòng lặp sau in ra kết quả gì?", "code": "for i in range(1, 4):\n    print(i, end=' ')", "ans": "1 2 3", "opts": ["1 2 3", "1 2 3 4", "0 1 2", "123"]})
        qs.append({"q": "Giá trị cuối cùng của k?", "code": "k = 0\nwhile k < 6:\n    k = k + 2", "ans": "6", "opts": ["4", "5", "6", "Loop vô hạn"]})
        self.questions = qs
        return len(qs)
    
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
                # Đội chính sai -> Chuyển sang cướp quyền
                self.mode = "STEAL"
                self.buzzer_winner = None
                self.blocked_team = active_team
            else:
                # Cướp quyền sai -> Hết lượt
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
    
    # --- MÀN HÌNH 1: SETUP ---
    if game.mode == "WAITING":
        st.markdown("<h1 style='text-align: center; color: #064E3B; font-size: 50px;'>🛠️ THIẾT LẬP TRẬN ĐẤU</h1>", unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.subheader("1. Câu Hỏi")
            uploaded_file = st.file_uploader("Upload file câu hỏi", type=['csv', 'xlsx'])
            if uploaded_file:
                success, msg = game.load_questions_from_file(uploaded_file)
                if success: st.success(msg)
                else: st.error(msg)
            if st.button("Dùng câu hỏi mẫu"):
                c = game.use_sample_questions()
                st.success(f"Đã nạp {c} câu mẫu")

        with col2:
            st.subheader("2. Đội Chơi")
            if not game.is_teams_created:
                n = st.number_input("Số lượng đội:", 1, 20, 4)
                if st.button("Tạo Đội", type="primary"):
                    game.init_teams(n)
                    st.rerun()
            else:
                st.success(f"Đã tạo {len(game.teams)} đội. Link HS: `https://python-arena.streamlit.app/`")
                if st.button("Làm lại đội"):
                    game.is_teams_created = False
                    game.teams = {}
                    st.rerun()
                
            start_disabled = (len(game.questions) == 0 or not game.is_teams_created)
            if st.button("🚀 BẮT ĐẦU", type="primary", disabled=start_disabled, use_container_width=True):
                game.start_game()
                st.rerun()
        time.sleep(2)
        st.rerun()

    # --- MÀN HÌNH 2: TRẬN ĐẤU ---
    else:
        # SIDEBAR: QUẢN LÝ ĐIỂM
        with st.sidebar:
            st.header("⚡ QUẢN LÝ")
            if st.button("🔄 Reset Game"):
                game.reset_game()
                st.rerun()
            
            st.divider()
            st.subheader("Cập nhật điểm")
            
            # Hiển thị nút + - cho từng đội
            for name, score in sorted(game.teams.items()):
                st.write(f"**{name}**: {score}")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"+10", key=f"p_{name}"):
                        game.adjust_score(name, 10)
                        st.rerun()
                with c2:
                    if st.button(f"-10", key=f"m_{name}"):
                        game.adjust_score(name, -10)
                        st.rerun()
                st.divider()

        col_score, col_stage = st.columns([1, 3], gap="large")

        # CỘT TRÁI: BẢNG ĐIỂM
        with col_score:
            st.markdown("<h3 style='color:#064E3B; text-align:center;'>🏆 XẾP HẠNG</h3>", unsafe_allow_html=True)
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

        # CỘT PHẢI: SÂN KHẤU
        with col_stage:
            q_data = game.questions[game.current_q_index]
            current_turn_team = team_list[game.turn_index % len(team_list)]

            # BANNER TRẠNG THÁI
            if game.mode == "QUESTION":
                st.markdown(f'<div class="status-banner" style="background: #3B82F6;">LƯỢT CỦA: {current_turn_team}</div>', unsafe_allow_html=True)
            elif game.mode == "STEAL":
                msg = f"(Đội {game.blocked_team} bị khóa)" if game.blocked_team else ""
                st.markdown(f'<div class="status-banner" style="background: #EF4444; animation: pulse 1s infinite;">🚨 CƯỚP QUYỀN! {msg}</div>', unsafe_allow_html=True)
                time.sleep(0.5)
                st.rerun()
            elif game.mode == "LOCKED":
                st.markdown(f'<div class="status-banner" style="background: #F59E0B;">⚡ {game.buzzer_winner} ĐANG TRẢ LỜI!</div>', unsafe_allow_html=True)
            elif game.mode == "RESULT":
                bg = "#10B981" if "CHÍNH XÁC" in game.last_result else "#EF4444"
                st.markdown(f'<div class="status-banner" style="background: {bg};">{game.last_result}</div>', unsafe_allow_html=True)

            # CÂU HỎI
            st.markdown(f"""
            <div class="question-card">
                <div style="font-size: 24px; color: #64748B; margin-bottom: 10px;">CÂU HỎI {game.current_q_index + 1}/{len(game.questions)}</div>
                <div class="question-text">{q_data['q']}</div>
            </div>
            """, unsafe_allow_html=True)
            if q_data['code']:
                st.markdown(f'<div class="code-container">{q_data["code"]}</div>', unsafe_allow_html=True)

            st.write("")
            
            # NÚT ĐÁP ÁN
            if game.mode == "RESULT":
                if st.button("CÂU TIẾP THEO ➡️", type="primary", use_container_width=True):
                    game.next_question()
                    st.rerun()
            elif game.mode == "STEAL":
                if st.button("BỎ QUA (KHÔNG AI TRẢ LỜI)", use_container_width=True):
                    game.next_question()
                    st.rerun()
            else:
                c1, c2 = st.columns(2, gap="medium")
                opts = q_data['opts']
                safe_opts = opts + [""] * (4 - len(opts))
                
                # Bọc nút trong div class host-btn để style đẹp
                st.markdown('<div class="host-btn">', unsafe_allow_html=True)
                with c1:
                    if st.button(f"A. {safe_opts[0]}", use_container_width=True): game.check_answer(safe_opts[0]); st.rerun()
                    if st.button(f"C. {safe_opts[2]}", use_container_width=True): game.check_answer(safe_opts[2]); st.rerun()
                with c2:
                    if st.button(f"B. {safe_opts[1]}", use_container_width=True): game.check_answer(safe_opts[1]); st.rerun()
                    if st.button(f"D. {safe_opts[3]}", use_container_width=True): game.check_answer(safe_opts[3]); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# GIAO DIỆN HỌC SINH (PLAYER)
# ==============================================================================
else:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            header {visibility: hidden;}
            .mobile-header { background: white; padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); border-bottom: 5px solid #00acc1; }
        </style>
    """, unsafe_allow_html=True)

    if "team_name" not in st.session_state or (game.is_teams_created and st.session_state.team_name not in game.teams):
        st.markdown("<h1 style='color: #064E3B; text-align: center; margin-top: 50px;'>📱 CHỌN ĐỘI</h1>", unsafe_allow_html=True)
        if not game.is_teams_created:
            st.warning("Đang chờ giáo viên tạo đội...")
            time.sleep(2)
            st.rerun()
        else:
            options = list(game.teams.keys())
            team_choice = st.selectbox("Chọn tên đội của bạn:", options)
            if st.button("VÀO PHÒNG NGAY", type="primary", use_container_width=True):
                st.session_state.team_name = team_choice
                st.rerun()
    else:
        my_team = st.session_state.team_name
        
        st.markdown(f"""
        <div class="mobile-header">
            <div style="font-size: 16px; color: #546e7a;">ĐỘI CỦA BẠN</div>
            <div style="font-size: 32px; font-weight: 900; color: #00838f;">{my_team}</div>
            <div style="font-size: 24px; font-weight: bold; color: #d84315;">{game.teams.get(my_team, 0)} điểm</div>
        </div>
        """, unsafe_allow_html=True)

        # Trạng thái nút bấm
        btn_text = "ĐANG ĐỢI..."
        btn_disabled = True
        btn_color = "#9e9e9e" # Grey
        box_shadow = "none"
        animation = "none"

        if game.mode == "STEAL":
            if my_team == game.blocked_team:
                btn_text = "🚫 ĐÃ BỊ KHÓA"
                btn_color = "#607d8b"
            else:
                btn_text = "🔔 GIÀNH QUYỀN!"
                btn_disabled = False
                btn_color = "#ff5252" # Red
                box_shadow = "0 0 40px #ff5252"
                animation = "pulse 0.6s infinite"
        
        elif game.mode == "LOCKED":
            if game.buzzer_winner == my_team:
                btn_text = "🎉 ĐƯỢC TRẢ LỜI!"
                btn_color = "#4caf50" # Green
                animation = "pulse 1s infinite"
            else:
                btn_text = f"🔒 CHẬM TAY ({game.buzzer_winner})"
                btn_color = "#f57c00" # Orange

        elif game.mode == "QUESTION":
            btn_text = "👀 NHÌN LÊN BẢNG"
            btn_color = "#1976d2" # Blue

        # CSS Nút bấm Dynamic
        st.markdown(f"""
        <style>
            div.stButton > button:first-child {{
                height: 300px !important;
                background-color: {btn_color} !important;
                color: white !important;
                font-size: 35px !important;
                border: 8px solid white !important;
                border-radius: 50% !important;
                box-shadow: {box_shadow};
                animation: {animation};
                opacity: {1.0 if not btn_disabled else 0.7};
            }}
            @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} 100% {{ transform: scale(1); }} }}
        </style>
        """, unsafe_allow_html=True)

        # Hiển thị nút (Luôn hiển thị, chỉ thay đổi style/disabled)
        if st.button(btn_text, disabled=btn_disabled, key="buzz_main"):
            if game.buzz(my_team):
                st.balloons()
            st.rerun()

        time.sleep(1)
        st.rerun()
