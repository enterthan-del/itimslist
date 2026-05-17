import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 설정 및 시트 연결
SHEET_NAME = "시트1"
st.set_page_config(page_title="스마트 물품 관리자", layout="wide")

# [통합 CSS] 모든 스타일을 한 곳에서 관리합니다.
st.markdown("""
    <style>
    /* 1. 각 카드 칸(Column)의 기준점 설정 */
    [data-testid="column"], [data-testid="stColumn"] {
        position: relative !important;
        display: flex;
        flex-direction: column;
        margin-bottom: 25px !important;
    }

    /* 2. 카드 스타일 */
    .item-card {
        width: 100%;
        border-radius: 12px;
        padding: 18px;
        height: 140px;
        border: 1px solid #eee;
        border-left: 8px solid; 
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.03);
        z-index: 1;
    }

    /* 3. 팝오버(톱니바퀴) 버튼을 카드 우측 상단에 강제 고정 */
    .stPopover, [data-testid="stPopover"] {
        position: absolute !important;
        top: 10px !important;
        right: 10px !important;
        z-index: 10 !important;
    }

    /* 4. 평소에는 버튼을 투명하게 (숨김) */
    .stPopover button, [data-testid="stPopover"] button {
        opacity: 0 !important;
        transition: opacity 0.3s ease-in-out !important;
        border: none !important;
        background-color: rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        width: 32px !important;
        height: 32px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 5. 마우스를 칸(Column) 위에 올렸을 때만 버튼을 보이게 함 */
    [data-testid="column"]:hover .stPopover button,
    [data-testid="stColumn"]:hover .stPopover button,
    [data-testid="column"]:hover [data-testid="stPopover"] button,
    [data-testid="stColumn"]:hover [data-testid="stPopover"] button {
        opacity: 1 !important;
    }

    /* 카드 제목 가독성 향상 */
    .item-title {
        font-size: 1rem;
        font-weight: 800;
        color: #2c3e50;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    data = conn.read(worksheet=SHEET_NAME, ttl=0).fillna("")
    if not data.empty:
        if '번호' in data.columns:
            data['번호'] = pd.to_numeric(data['번호'], errors='coerce')
        data = data.reset_index(drop=True)
    return data

def save_data(df):
    conn.update(worksheet=SHEET_NAME, data=df)
    st.cache_data.clear()

def get_category_theme(cat):
    themes = {
        "케이블 & 잭류": ("#3498db", "#ebf5fb"),
        "전자부품 & 모듈": ("#e67e22", "#fef5e7"),
        "저장장치 & IT 기기": ("#9b59b6", "#f5eef8"),
        "오디오 & 영상 장비": ("#e74c3c", "#fdedec"),
        "아답터 & 전원": ("#f1c40f", "#fef9e7"),
        "납땜 & 전기 작업": ("#1abc9c", "#e8f8f5"),
        "공구류": ("#2ecc71", "#eafaf1"),
        "기타 잡화": ("#7f8c8d", "#f2f4f4")
    }
    return themes.get(cat, ("#bdc3c7", "#f8f9f9"))

# 데이터 불러오기
df = load_data()

st.title("📦 스마트 물품 관리 시스템")

tab1, tab2, tab3 = st.tabs(["🔍 물품 목록", "➕ 신규 등록", "⚙️ 전체 관리"])

# --- Tab 1: 물품 목록 ---
with tab1:
    # 1. 검색 및 필터 UI
    c1, c2 = st.columns([3, 1])
    search_q = c1.text_input("🔍 검색", placeholder="물건 이름 입력...", label_visibility="collapsed", key="main_search")
    cat_filter = c2.multiselect("카테고리 필터", options=sorted(df['카테고리'].unique().tolist()), key="main_filter")

    filtered_df = df.copy()
    if search_q:
        filtered_df = filtered_df[filtered_df.apply(lambda row: row.astype(str).str.contains(search_q).any(), axis=1)]
    if cat_filter:
        filtered_df = filtered_df[filtered_df['카테고리'].isin(cat_filter)]

    existing_locs = sorted([loc for loc in df['보관 위치'].unique() if loc])

    # 2. 카드 출력 (4개씩 행 단위 배치)
    cols_per_row = 4
    for i in range(0, len(filtered_df), cols_per_row):
        cols = st.columns(cols_per_row)
        batch = filtered_df.iloc[i : i + cols_per_row]
        
        for j, (orig_idx, row) in enumerate(batch.iterrows()):
            main_color, bg_color = get_category_theme(row['카테고리'])
            
            with cols[j]:
                # [수정 팝오버]
                with st.popover("⚙️", key=f"t1_pop_{orig_idx}"):
                    st.write(f"**{row['물건 이름']}** 수정")
                    current_loc = row['보관 위치']
                    loc_options = existing_locs if current_loc in existing_locs else [current_loc] + existing_locs
                    
                    new_loc = st.selectbox("보관 위치 변경", options=loc_options, key=f"t1_loc_{orig_idx}")
                    new_memo = st.text_input("메모 수정", value=row.get('메모', ''), key=f"t1_mem_{orig_idx}")
                    
                    if st.button("저장하기", key=f"t1_btn_{orig_idx}", use_container_width=True):
                        df.at[orig_idx, '보관 위치'] = new_loc
                        df.at[orig_idx, '메모'] = new_memo
                        save_data(df)
                        st.success("저장되었습니다.")
                        st.rerun()

                # [카드 디자인]
                st.markdown(f"""
                    <div class="item-card" style="background-color: {bg_color}; border-left-color: {main_color};">
                        <div>
                            <div class="item-title">{row['물건 이름']}</div>
                            <div style="font-size: 0.75rem; color: {main_color}; font-weight: bold;">{row['카테고리']}</div>
                        </div>
                        <div style="font-size: 0.85rem; color: #555; font-weight: 500; background: rgba(255,255,255,0.5); padding: 2px 8px; border-radius: 4px; width: fit-content;">
                            📍 {row['보관 위치'] if row['보관 위치'] else '미지정'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# --- Tab 2: 신규 등록 ---
with tab2:
    st.subheader("새 물품 등록")
    with st.form("new_item_form", clear_on_submit=True):
        f_name = st.text_input("물품명*")
        f_cat = st.selectbox("카테고리", sorted(df['카테고리'].unique().tolist()) + ["직접 입력"])
        f_loc = st.selectbox("보관 위치", sorted([l for l in df['보관 위치'].unique() if l]) + ["직접 입력"])
        f_memo = st.text_area("메모")
        if st.form_submit_button("등록하기") and f_name:
            new_id = int(df['번호'].max()) + 1 if not df.empty else 1
            new_row = pd.DataFrame([{"번호": new_id, "물건 이름": f_name, "카테고리": f_cat, "보관 위치": f_loc, "메모": f_memo}])
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("등록 완료!")
            st.rerun()

# --- Tab 3: 전체 관리 ---
with tab3:
    st.subheader("데이터베이스 관리")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="admin_editor")
    if st.button("💾 모든 변경사항 시트에 반영", key="admin_save_btn"):
        save_data(edited_df)
        st.success("전체 데이터가 업데이트되었습니다.")
        st.rerun()