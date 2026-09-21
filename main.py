import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="영화 데이터 그래프 도감 1 - 시간", layout="wide")

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"
)

# 그래프마다 아래에 보여 줄 '이 그래프로 알 수 있는 것' 문구.
# 문장을 채우면 화면에 나타나고, 비워 두면 안내 문구가 보여요.
INSIGHTS = {
    "graph_1": "",
    "graph_2": "",
}


# ─────────────────────────────────────────────
# 데이터 불러오기
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="데이터를 불러오는 중...")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_URL)
    # 하이픈 없는 8자리 숫자(예: 20250901)를 진짜 날짜로 변환
    df["날짜"] = pd.to_datetime(df["날짜"].astype(str), format="%Y%m%d")
    return df.sort_values(["날짜", "순위"]).reset_index(drop=True)


def show_insight(key: str) -> None:
    """그래프 아래 '이 그래프로 알 수 있는 것' 한 문장 자리."""
    text = INSIGHTS.get(key, "").strip()
    if text:
        st.markdown(f"**💡 이 그래프로 알 수 있는 것**  \n{text}")
    else:
        st.markdown(
            "**💡 이 그래프로 알 수 있는 것**  \n"
            f"<span style='color:gray'>(여기에 한 문장을 적어 주세요 → "
            f"main.py 위쪽 INSIGHTS['{key}'])</span>",
            unsafe_allow_html=True,
        )


def movie_table(df: pd.DataFrame) -> pd.DataFrame:
    """영화별 일관객 합계 표 (합계가 큰 순). 여러 구역에서 함께 사용해요.

    영화코드를 기준으로 구분하고, 이름이 같은 영화가 있으면 코드를 덧붙여 '표시명'으로 써요.
    """
    movies = (
        df.groupby(["영화코드", "영화명"], as_index=False)["일관객"]
        .sum()
        .sort_values("일관객", ascending=False)
        .reset_index(drop=True)
    )
    dup_names = movies["영화명"].duplicated(keep=False)
    movies["표시명"] = movies["영화명"].where(
        ~dup_names, movies["영화명"] + " (" + movies["영화코드"].astype(str) + ")"
    )
    return movies


# ─────────────────────────────────────────────
# 구역 1: 영화별 일관객 변화
# ─────────────────────────────────────────────
def section_daily_audience(df: pd.DataFrame) -> None:
    st.header("1. 영화별 일관객 변화")

    movies = movie_table(df)
    label_to_code = dict(zip(movies["표시명"], movies["영화코드"]))

    selected = st.selectbox(
        "영화를 골라 보세요 (10위권 누적 관객이 많은 순)",
        options=list(label_to_code.keys()),
    )

    movie_df = df[df["영화코드"] == label_to_code[selected]].sort_values("날짜")

    fig = go.Figure(
        go.Scatter(
            x=movie_df["날짜"],
            y=movie_df["일관객"],
            mode="lines+markers",
            name=selected,
            hovertemplate="날짜: %{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"{selected} - 날짜별 일관객",
        xaxis_title="날짜",
        yaxis_title="일관객 (명)",
        hovermode="closest",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption("※ 박스오피스 10위권에 든 날의 기록만 있어요.")

    show_insight("graph_1")


# ─────────────────────────────────────────────
# 구역 2: 일관객 합계 상위 5편 비교
# ─────────────────────────────────────────────
TOP_N = 5


def section_top5_compare(df: pd.DataFrame) -> None:
    st.header("2. 일관객 합계 상위 5편 비교")

    top = movie_table(df).head(TOP_N)

    fig = go.Figure()
    for _, row in top.iterrows():
        movie_df = df[df["영화코드"] == row["영화코드"]].sort_values("날짜")
        fig.add_trace(
            go.Scatter(
                x=movie_df["날짜"],
                y=movie_df["일관객"],
                mode="lines",
                name=row["표시명"],  # 범례 이름 → 클릭하면 켜고 끌 수 있어요
                hovertemplate=(
                    "%{fullData.name}<br>"
                    "날짜: %{x|%Y-%m-%d}<br>"
                    "일관객: %{y:,}명<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"일관객 합계 상위 {TOP_N}편 - 날짜별 일관객",
        xaxis_title="날짜",
        yaxis_title="일관객 (명)",
        hovermode="closest",
        legend_title_text="영화 (클릭해서 켜고 끄기)",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "※ 범례의 영화 이름을 한 번 누르면 숨겨지고, 다시 누르면 나타나요. "
        "더블클릭하면 그 영화만 보여요. 10위권에 든 날의 기록만 있어요."
    )

    show_insight("graph_2")


# ─────────────────────────────────────────────
# 화면 구성 (그래프를 추가할 때는 아래에 구역을 이어 붙이세요)
# ─────────────────────────────────────────────
st.title("영화 데이터 그래프 도감 1 - 시간")

data = load_data()

section_daily_audience(data)
st.divider()

section_top5_compare(data)
st.divider()

# 구역 3: (다음 그래프를 여기에 추가)
# section_xxx(data)
# st.divider()
