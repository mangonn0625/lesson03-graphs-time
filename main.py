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
    "graph_3": "",
    "graph_4": "",
    "graph_5": "",
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
        df.groupby(["영화코드", "영화명"], as_index=False)
        .agg(일관객=("일관객", "sum"), 십위권일수=("날짜", "nunique"))
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
# 구역 3: 날짜별 10위권 일관객 합계 (영역 그래프)
# ─────────────────────────────────────────────
PEAK_DAYS = 3


def section_daily_total(df: pd.DataFrame) -> None:
    st.header("3. 날짜별 10위권 일관객 합계")

    daily = df.groupby("날짜", as_index=False)["일관객"].sum()
    peaks = daily.nlargest(PEAK_DAYS, "일관객").reset_index(drop=True)
    peaks["순위"] = peaks.index + 1

    fig = go.Figure()

    # 영역 그래프
    fig.add_trace(
        go.Scatter(
            x=daily["날짜"],
            y=daily["일관객"],
            mode="lines",
            fill="tozeroy",
            name="일관객 합계",
            hovertemplate="날짜: %{x|%Y-%m-%d}<br>합계: %{y:,}명<extra></extra>",
        )
    )

    # 합계가 가장 컸던 날 표시 (점)
    fig.add_trace(
        go.Scatter(
            x=peaks["날짜"],
            y=peaks["일관객"],
            mode="markers",
            name=f"합계 최고 {PEAK_DAYS}일",
            marker=dict(color="red", size=10, line=dict(color="white", width=1)),
            hovertemplate=(
                "%{customdata}위<br>날짜: %{x|%Y-%m-%d}"
                "<br>합계: %{y:,}명<extra></extra>"
            ),
            customdata=peaks["순위"],
        )
    )

    # 날짜 글씨 (가까운 날끼리는 왼쪽/오른쪽으로 벌려서 겹치지 않게 함)
    order = peaks.sort_values("날짜").reset_index(drop=True)
    for i, row in order.iterrows():
        ax = 0
        if i > 0 and (row["날짜"] - order.loc[i - 1, "날짜"]).days < 30:
            ax = 55  # 앞 날짜와 가까우면 오른쪽으로
        elif i < len(order) - 1 and (order.loc[i + 1, "날짜"] - row["날짜"]).days < 30:
            ax = -55  # 뒤 날짜와 가까우면 왼쪽으로
        fig.add_annotation(
            x=row["날짜"],
            y=row["일관객"],
            text=f"{row['순위']}위 {row['날짜']:%Y-%m-%d}<br>{row['일관객']:,}명",
            showarrow=True,
            arrowhead=2,
            ax=ax,
            ay=-45,
            font=dict(color="red"),
            bgcolor="rgba(255,255,255,0.8)",
        )

    fig.update_layout(
        title="날짜별 10위권 일관객 합계",
        xaxis_title="날짜",
        yaxis_title="일관객 합계 (명)",
        yaxis_range=[0, daily["일관객"].max() * 1.25],  # 글씨 들어갈 위쪽 여백
        hovermode="closest",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption("※ 그날 박스오피스 10위권 영화의 일관객을 모두 더한 값이에요.")

    show_insight("graph_3")


# ─────────────────────────────────────────────
# 구역 4: 일관객 합계 TOP 10 (가로 막대그래프)
# ─────────────────────────────────────────────
BAR_TOP_N = 10


def section_top10_bar(df: pd.DataFrame) -> None:
    st.header("4. 영화별 일관객 합계 TOP 10")

    top = movie_table(df).head(BAR_TOP_N)  # 이미 관객이 많은 순

    fig = go.Figure(
        go.Bar(
            x=top["일관객"],
            y=top["표시명"],
            orientation="h",
            text=top["일관객"].map("{:,}".format),
            textposition="outside",
            cliponaxis=False,
            customdata=top["십위권일수"],
            hovertemplate=(
                "%{y}<br>"
                "일관객 합계: %{x:,}명<br>"
                "10위권에 든 날수: %{customdata}일<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=f"이 기간 일관객 합계 TOP {BAR_TOP_N}",
        xaxis_title="일관객 합계 (명)",
        yaxis_title=None,
        yaxis=dict(autorange="reversed", automargin=True),  # 1위가 맨 위로
        xaxis_range=[0, top["일관객"].max() * 1.15],  # 막대 끝 글씨 들어갈 여백
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "※ 이 데이터에 담긴 기간(10위권에 든 날의 기록)만 더한 값이에요. "
        "'10위권에 든 날수'도 이 기간 안에서 센 값이에요."
    )

    show_insight("graph_4")


# ─────────────────────────────────────────────
# 구역 5: 월 × 요일별 일관객 합계 (히트맵)
# ─────────────────────────────────────────────
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]  # dayofweek: 월=0 … 일=6


def section_month_weekday_heatmap(df: pd.DataFrame) -> None:
    st.header("5. 월 × 요일별 일관객 합계")

    # 날짜에서 월(연-월)과 요일을 뽑아요.
    # 기간이 1년을 넘어 9월이 두 번 나오므로 '2025-09'처럼 연-월로 구분해요.
    work = df[["날짜", "일관객"]].copy()
    work["월"] = work["날짜"].dt.strftime("%Y-%m")
    work["요일"] = work["날짜"].dt.dayofweek

    pivot = (
        work.pivot_table(index="월", columns="요일", values="일관객", aggfunc="sum")
        .reindex(columns=range(7))  # 월요일부터 일요일 순서로 고정
        .fillna(0)
        .sort_index()
    )

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=WEEKDAYS,
            y=pivot.index.tolist(),
            colorscale="Blues",  # 색이 진할수록 관객이 많아요
            colorbar=dict(title="일관객 합계 (명)"),
            hovertemplate="%{y} %{x}요일<br>일관객 합계: %{z:,}명<extra></extra>",
        )
    )
    fig.update_layout(
        title="월 × 요일별 일관객 합계",
        xaxis=dict(title="요일", type="category", side="top"),
        yaxis=dict(title="월", type="category", autorange="reversed"),  # 이른 달이 위로
        margin=dict(l=20, r=20, t=90, b=20),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "※ 합계라서 그 달에 해당 요일이 며칠 있었는지에 따라 값이 달라져요. "
        "마지막 달은 데이터가 끝나는 날까지만 들어 있어요."
    )

    show_insight("graph_5")


# ─────────────────────────────────────────────
# 화면 구성 (그래프를 추가할 때는 아래에 구역을 이어 붙이세요)
# ─────────────────────────────────────────────
st.title("영화 데이터 그래프 도감 1 - 시간")

data = load_data()

section_daily_audience(data)
st.divider()

section_top5_compare(data)
st.divider()

section_daily_total(data)
st.divider()

section_top10_bar(data)
st.divider()

section_month_weekday_heatmap(data)
st.divider()

# 구역 6: (다음 그래프를 여기에 추가)
# section_xxx(data)
# st.divider()
