import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px

# ------------------- SETTINGS -------------------
st.set_page_config(page_title="Steam Cracker Allocation Methods", layout="wide")
st.title("Steam Cracker Allocation Methods")

# Sidebar navigation
view = st.sidebar.selectbox("Select View:", (
    "Mass Balance",
    "Allocation to HVC only",
    "Allocation to all",
    "Overview Comparison"
))

# Product mass and emissions
# ------------------- USER INPUTS -------------------
st.sidebar.header("Product Mass Inputs (t)")
ethylene = st.sidebar.number_input("Ethylene (HVC)", value=500, min_value=0)
propylene = st.sidebar.number_input("Propylene (HVC)", value=300, min_value=0)
fuel = st.sidebar.number_input("Fuel (non-HVC)", value=200, min_value=0)
total_mass = ethylene + propylene + fuel


emission_naphtha = 2.0  # t CO2
emission_energy = 1.0   # t CO2

# Sidebar: colors
st.sidebar.markdown("**Color Settings**")
color_eth = st.sidebar.color_picker("Ethylene (HVC)", "#FF6B6B")
color_pro = st.sidebar.color_picker("Propylene (HVC)", "#C44D58")
color_fuel = st.sidebar.color_picker("Fuel (non-HVC)", "#666666")
color_energy = st.sidebar.color_picker("Energy Input", "#FFD700")
color_naphtha = st.sidebar.color_picker("Naphtha", "#FFA500")


# ------------------ Shared Helpers ------------------
def format_table(naphtha_list, energy_list):
    total = [n + e for n, e in zip(naphtha_list, energy_list)]
    df = pd.DataFrame({
        "Product": ["Ethylene (HVC)", "Propylene (HVC)", "Fuel (non-HVC)"],
        "Mass (t)": [ethylene, propylene, fuel],
        "Emission from Naphtha (t CO₂)": naphtha_list,
        "Emission from Energy (t CO₂)": energy_list,
        "Total Emission (t CO₂)": total
    })
    total_row = pd.DataFrame({
        "Product": ["Total"],
        "Mass (t)": [total_mass],
        "Emission from Naphtha (t CO₂)": [sum(naphtha_list)],
        "Emission from Energy (t CO₂)": [sum(energy_list)],
        "Total Emission (t CO₂)": [sum(total)]
    })
    return pd.concat([df, total_row], ignore_index=True)

def draw_mass_sankey():
    labels = ["Naphtha", "Energy Input (10 GJ)", "Steam Cracking", "Ethylene (HVC)", "Propylene (HVC)", "Fuel (non-HVC)"]
    source = [0, 1, 2, 2, 2]
    target = [2, 2, 3, 4, 5]
    values = [1000, 10, ethylene, propylene, fuel]
    node_colors = [color_naphtha, color_energy, "#EF553B", color_eth, color_pro, color_fuel]
    link_colors = [color_energy, color_energy, color_eth, color_pro, color_fuel]

    fig = go.Figure(go.Sankey(
        node=dict(pad=20, thickness=30, label=labels, color=node_colors, line=dict(color="gray")),
        link=dict(source=source, target=target, value=values, color=link_colors)
    ))
    fig.update_layout(title_text="Material & Energy Flow", font=dict(size=14))
    return fig

def draw_co2_sankey(naphtha_alloc, energy_alloc):
    labels = ["Naphtha Emission (2t)", "Energy Emission (1t)", "Ethylene (HVC)", "Propylene (HVC)", "Fuel (non-HVC)"]
    source = [0, 0, 0, 1, 1, 1]
    target = [2, 3, 4, 2, 3, 4]
    values = [naphtha_alloc[0], naphtha_alloc[1], naphtha_alloc[2],
              energy_alloc[0], energy_alloc[1], energy_alloc[2]]
    colors = [color_eth, color_pro, color_fuel, color_eth, color_pro, color_fuel]

    fig = go.Figure(go.Sankey(
        node=dict(pad=20, thickness=30, label=labels,
                  color=[color_naphtha, color_energy, color_eth, color_pro, color_fuel],
                  line=dict(color="gray")),
        link=dict(source=source, target=target, value=values, color=colors)
    ))
    fig.update_layout(title_text="CO₂ Allocation Flow", font=dict(size=14))
    return fig

# ------------------ PAGE: MASS BALANCE ------------------
if view == "Mass Balance":
    st.header("Mass Balance View")
    st.markdown("Mass and energy input/output without CO₂ allocation.")
    st.plotly_chart(draw_mass_sankey(), use_container_width=True)

    st.subheader("Input Table")
    df_input = pd.DataFrame({
        "Input": ["Naphtha", "Energy"],
        "Amount": ["1000 t", "10 GJ"],
        "Carbon Emission (t CO₂)": [emission_naphtha, emission_energy]
    })
    st.dataframe(df_input)

    st.subheader("Output Table")
    df_output = pd.DataFrame({
        "Product": ["Ethylene (HVC)", "Propylene (HVC)", "Fuel (non-HVC)"],
        "Mass (t)": [ethylene, propylene, fuel]
    })
    st.dataframe(df_output)

# ------------------ PAGE: ALLOCATION TO HVC ONLY ------------------
elif view == "Allocation to HVC only":
    st.header("CO₂ Allocation: HVC Only")

    naphtha_alloc = [1.0, 0.6, 0.4]
    total_hvc = ethylene + propylene
    energy_alloc = [
        emission_energy * ethylene / total_hvc,
        emission_energy * propylene / total_hvc,
        0.0
    ]

    df = format_table(naphtha_alloc, energy_alloc)
    st.dataframe(df.style.format({
        "Mass (t)": "{:.0f}",
        "Emission from Naphtha (t CO₂)": "{:.2f}",
        "Emission from Energy (t CO₂)": "{:.3f}",
        "Total Emission (t CO₂)": "{:.3f}"
    }))
    st.plotly_chart(draw_co2_sankey(naphtha_alloc, energy_alloc), use_container_width=True)

# ------------------ PAGE: ALLOCATION TO ALL ------------------
elif view == "Allocation to all":
    st.header("CO₂ Allocation: To All Products (Mass-based)")

    naphtha_alloc = [
        emission_naphtha * ethylene / total_mass,
        emission_naphtha * propylene / total_mass,
        emission_naphtha * fuel / total_mass
    ]
    energy_alloc = [
        emission_energy * ethylene / total_mass,
        emission_energy * propylene / total_mass,
        emission_energy * fuel / total_mass
    ]

    df = format_table(naphtha_alloc, energy_alloc)
    st.dataframe(df.style.format({
        "Mass (t)": "{:.0f}",
        "Emission from Naphtha (t CO₂)": "{:.2f}",
        "Emission from Energy (t CO₂)": "{:.3f}",
        "Total Emission (t CO₂)": "{:.3f}"
    }))
    st.plotly_chart(draw_co2_sankey(naphtha_alloc, energy_alloc), use_container_width=True)

# ------------------ PAGE: OVERVIEW COMPARISON ------------------
elif view == "Overview Comparison":
    st.header("Overview: Comparison of Product PCFs")

    hvc_naphtha = [1.0, 0.6, 0.4]
    hvc_energy = [emission_energy * ethylene / 800, emission_energy * propylene / 800, 0.0]
    all_naphtha = [emission_naphtha * x / total_mass for x in [ethylene, propylene, fuel]]
    all_energy = [emission_energy * x / total_mass for x in [ethylene, propylene, fuel]]

    df_comp = pd.DataFrame({
        "Product": ["Ethylene", "Propylene", "Fuel"] * 2,
        "Allocation": ["HVC Only"] * 3 + ["To All"] * 3,
        "Total Emissions (t CO₂)": [hvc_naphtha[i]+hvc_energy[i] for i in range(3)] +
                                   [all_naphtha[i]+all_energy[i] for i in range(3)]
    })

    fig = px.bar(
        df_comp,
        x="Product",
        y="Total Emissions (t CO₂)",
        color="Allocation",
        barmode="group",
        text_auto=True,
        color_discrete_map={
            "HVC Only": "#FF6B6B",
            "To All": "#222222"
        },
        title="Comparison of Product Carbon Footprints (PCF) by Allocation Method"
    )
    fig.update_traces(marker_line_width=1.5, marker_line_color="black")
    fig.update_layout(font=dict(size=14), title_font_size=18)

    # ✅ Burden 계산 및 annotation
    burdens = [
        (hvc_naphtha[i] + hvc_energy[i]) - (all_naphtha[i] + all_energy[i])
        for i in range(3)
    ]
    products = ["Ethylene", "Propylene", "Fuel"]

    for i, burden in enumerate(burdens):
        if abs(burden) > 0.001:
            fig.add_annotation(
                x=products[i],
                y=max(hvc_naphtha[i] + hvc_energy[i], all_naphtha[i] + all_energy[i]),
                text=(
                    f"⬇ Reduced burden: {burden:.3f} t CO₂" if burden > 0 else
                    f"⬆ Gained burden: {abs(burden):.3f} t CO₂"
                ),
                showarrow=False,
                font=dict(color="gray", size=12),
                yshift=20
            )

    st.plotly_chart(fig, use_container_width=True)