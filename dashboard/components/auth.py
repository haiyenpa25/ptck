import streamlit as st

def check_password(st):
    """Returns True if the user had a correct password."""
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "Abc.1234":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password in plain text state
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Show input for guests
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #00F0FF;'>🏦 CW-QUANT TERMINAL</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #A0AEC0;'>Vui lòng xác thực danh tính để vào Phòng Giao Dịch</p>", unsafe_allow_html=True)
        
        with st.form("Credentials", border=True):
            st.text_input("Tên Quản Trị Hệ Thống (Username)", key="username")
            st.text_input("Mật Khẩu Cấp Phép (Password)", type="password", key="password")
            st.form_submit_button("🔓 Mở Khóa Hệ Thống", on_click=password_entered, use_container_width=True)

        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác. Kích hoạt hệ thống phòng thủ...")
            
    return False
