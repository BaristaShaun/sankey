import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ------------------- SETTINGS -------------------
st.set_page_config(page_title="Steam Cracker Allocation Methods", layout="wide")
st.title("Steam Cracker Allocation Methods")

# Sidebar navigation
view = st.sidebar.selectbox("Select View:", (
    "Mass Balance",
    "Allocation to HVC only",
    "Allocation to all",
    "Overview Comparison",
))

# ------------------- USER INPUT -------------------
st.sidebar.header("Product Mass Input (in tons)")
ethylene = st.sidebar.number_input("Ethylene (HVC)", min_value=0.0, value=342.2)
propylene = st.sidebar.number_input("Propylene (HVC)", min_value=0.0, value=156.7)
butadiene = st.sidebar.number_input("Butadiene (HVC)", min_value=0.0, value=46.6)
others = st.sidebar.number_input("Others (HVC)", min_value=0.0, value=202.1)
fuel = st.sidebar.number_input("Fuel (non-HVC)", min_value=0.0, value=74.2)

st.sidebar.header("Flow Color Settings")
color_eth = st.sidebar.color_picker("Ethylene Flow (HVC)", "#FF6B6B")
color_pro = st.sidebar.color_picker("Propylene Flow (HVC)", "#C44D58")
color_but = st.sidebar.color_picker("Butadiene Flow (HVC)", "#D46A6A")
color_oth = st.sidebar.color_picker("Others Flow (HVC)", "#FFA07A")
color_fuel = st.sidebar.color_picker("Fuel Flow (non-HVC)", "#222222")
color_feedstock = st.sidebar.color_picker("Feedstock Input", "#FFA500")
color_energy = st.sidebar.color_picker("Energy Input", "#FFD700")

# ------------------- PRODUCT INFO -------------------
products = {
    "Ethylene (HVC)": {"mass": ethylene, "flow_color": color_eth},
    "Propylene (HVC)": {"mass": propylene, "flow_color": color_pro},
    "Butadiene (HVC)": {"mass": butadiene, "flow_color": color_but},
    "Others (HVC)": {"mass": others, "flow_color": color_oth},
    "Fuel (non-HVC)": {"mass": fuel, "flow_color": color_fuel}
}

# Normalize mass
feedstock_mass = 1000.0
original_total = sum(p["mass"] for p in products.values())
scale = feedstock_mass / original_total if original_total > 0 else 0
for p in products.values():
    p["mass"] *= scale

# Emissions
emission_feedstock = 2.0
emission_energy = 1.0

# Allocation calculations
total_mass = sum(p["mass"] for p in products.values())
total_hvc = sum(p["mass"] for k, p in products.items() if "non-HVC" not in k)
for k, v in products.items():
    is_hvc = "non-HVC" not in k
    if is_hvc:
        v["feedstock_alloc_hvc"] = emission_feedstock * v["mass"] / total_hvc
        v["energy_alloc_hvc"] = emission_energy * v["mass"] / total_hvc
    else:
        v["feedstock_alloc_hvc"] = emission_feedstock * v["mass"] / total_mass
        v["energy_alloc_hvc"] = 0.0
    v["feedstock_alloc_all"] = emission_feedstock * v["mass"] / total_mass
    v["energy_alloc_all"] = emission_energy * v["mass"] / total_mass

# DataFrames for charts
df_allocation = pd.DataFrame([
    {
        "Product": k,
        "Mass": v["mass"],
        "Emission_HVC": v["feedstock_alloc_hvc"] + v["energy_alloc_hvc"],
        "Emission_All": v["feedstock_alloc_all"] + v["energy_alloc_all"],
        "Feedstock": v["feedstock_alloc_all"],
        "Energy": v["energy_alloc_all"],
        "Error": abs((v["feedstock_alloc_all"] + v["energy_alloc_all"]) - (v["feedstock_alloc_hvc"] + v["energy_alloc_hvc"]))
    }
    for k, v in products.items()
])

# ------------------- VIEWS -------------------
if view == "Mass Balance":
    st.header("Mass Balance View")
    st.markdown("📝 **Note**: Feedstock mass (1000 t) excludes heat integration losses and represents net usable input.")
    labels = ["Feedstock", "Energy Input", "Steam Cracking"] + list(products.keys())
    source = [0, 1] + [2]*len(products)
    target = [2, 2] + list(range(3, 3+len(products)))
    values = [feedstock_mass, 10] + [v["mass"] for v in products.values()]
    link_colors = [color_feedstock, color_energy] + [v["flow_color"] for v in products.values()]
    node_colors = ["#AAAAAA"] * len(labels)

    fig = go.Figure(go.Sankey(
        node=dict(label=labels, color=node_colors),
        link=dict(source=source, target=target, value=values, color=link_colors)
    ))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Input Table")
    st.dataframe(pd.DataFrame({
        "Input": ["Feedstock", "Energy"],
        "Amount": ["1000 t", "10 GJ"],
        "CO₂ Emissions": [emission_feedstock, emission_energy]
    }))

    st.subheader("Output Table")
    st.dataframe(df_allocation[["Product", "Mass"]])

elif view in ["Allocation to HVC only", "Allocation to all"]:
    st.header(f"CO₂ Allocation: {view}")
    mode = "hvc" if view.endswith("HVC only") else "all"
    df = pd.DataFrame([
        {
            "Product": k,
            "Mass": v["mass"],
            "Feedstock": v[f"feedstock_alloc_{mode}"],
            "Energy": v[f"energy_alloc_{mode}"],
            "Total Emission": v[f"feedstock_alloc_{mode}"] + v[f"energy_alloc_{mode}"]
        }
        for k, v in products.items()
    ])
    st.dataframe(df)

    labels = ["Feedstock Emission", "Energy Emission"] + list(products.keys())
    source = []
    target = []
    value = []
    color = []

    for i, (k, v) in enumerate(products.items()):
        idx = i + 2
        f = v[f"feedstock_alloc_{mode}"]
        e = v[f"energy_alloc_{mode}"]
        if f > 0:
            source.append(0); target.append(idx); value.append(f); color.append(v["flow_color"])
        if e > 0:
            source.append(1); target.append(idx); value.append(e); color.append(v["flow_color"])

    node_colors = ["#AAAAAA"] * len(labels)
    fig = go.Figure(go.Sankey(
        node=dict(label=labels, color=node_colors),
        link=dict(source=source, target=target, value=value, color=color)
    ))
    st.plotly_chart(fig, use_container_width=True)

# ------------------- OVERVIEW COMPARISON -------------------
elif view == "Overview Comparison":
    st.header("Overview Comparison")
    df_bar = df_allocation.copy()
    df_bar["Burden"] = df_bar["Emission_All"] - df_bar["Emission_HVC"]  # <-- 수정된 부분

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_bar["Product"], y=df_bar["Emission_HVC"],
                         name="Allocation to HVC", marker_color="#FF6B6B"))
    fig.add_trace(go.Bar(x=df_bar["Product"], y=df_bar["Emission_All"],
                         name="Allocation to All", marker_color="#444444"))

    for i, row in df_bar.iterrows():
        burden = row["Burden"]
        annotation = "⬆ Gained burden" if burden > 0 else "⬇ Reduced burden"
        fig.add_annotation(x=row["Product"], y=max(row["Emission_HVC"], row["Emission_All"]),
                           text=f"{annotation}: {abs(burden):.3f} kg CO₂-eq/kg",
                           showarrow=False, yshift=20, font=dict(size=12, color="gray"))

    fig.update_layout(title="Allocation Burden Comparison",
                      barmode="group",
                      yaxis_title="kg CO₂-eq/kg product",
                      legend_title="Allocation Method")
    st.plotly_chart(fig, use_container_width=True)

