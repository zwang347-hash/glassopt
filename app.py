import streamlit as st

from geometry import VERTICES, calculate_plan
from visualization import draw_plan

EXAMPLES = {
    "三角形": ((800, 600, 1000), ()),
    "四边形": ((800, 600, 800, 600), (1000,)),
    "五边形": ((800, 300, 500, 400, 600), (854.4003745317531, 721.1102550927978)),
}


def main():
    st.set_page_config(page_title="GlassOpt V1.0", layout="wide")
    st.title("GlassOpt V1.0")
    st.markdown("单片玻璃原片计算")
    inputs, results = st.columns([1, 1.45], gap="large")

    with inputs:
        shape = st.selectbox("玻璃形状", tuple(EXAMPLES), index=1)
        example_sides, example_diagonals = EXAMPLES[shape]
        n = len(example_sides)
        st.caption(f"从 A 点出发，沿轮廓依次标记 {' → '.join(VERTICES[:n])}，最后回到 A。尺寸单位为 mm。")

        def read_lengths(labels, values):
            fields = st.columns(2)
            return [
                fields[i % 2].number_input(
                    label, value=float(value), step=1.0, format="%.6f",
                    key=f"{shape}:{label}",
                )
                for i, (label, value) in enumerate(zip(labels, values))
            ]

        st.subheader("边长")
        sides = read_lengths(
            [VERTICES[i] + VERTICES[(i + 1) % n] for i in range(n)], example_sides
        )
        diagonals = []
        if example_diagonals:
            st.subheader("从 A 点量出的对角线")
            diagonals = read_lengths(["A" + v for v in VERTICES[2:n - 1]], example_diagonals)
        margin = st.number_input("原片加工余量（mm / 单侧）", value=10.0, step=1.0)
        st.caption("四个方向各加一次。左、右共加两倍余量，上、下也是。")

    with results:
        st.subheader("原片计算结果")
        try:
            plan = calculate_plan(sides, diagonals, margin)
        except ValueError as error:
            st.error(str(error))
            return

        length, width = sorted((plan.stock.width, plan.stock.height), reverse=True)
        st.metric("原片长 × 宽", f"{length:,.2f} × {width:,.2f} mm")
        a, b = st.columns(2)
        c, d = st.columns(2)
        a.metric("成品面积", f"{plan.glass_area / 1e6:,.4f} m²")
        b.metric("原片面积", f"{plan.stock.area / 1e6:,.4f} m²")
        c.metric("余料面积", f"{plan.scrap_area / 1e6:,.4f} m²")
        d.metric("材料利用率", f"{plan.efficiency:.2%}")
        st.pyplot(draw_plan(plan))
        st.caption("绿色为成品，灰色矩形为原片，虚线表示输入对角线。图形按比例显示。")


if __name__ == "__main__":
    main()
