import pandas as pd
import streamlit as st

st.set_page_config(
    page_title = "Data View",
    page_icon = ":bar_chart",
    layout = "wide")

st.title("CSV Data Viewer")

st.header(":bar_chart: Data from Google Sheets CSV Export")
st.caption("Author: @McCadeP8")

with st.sidebar:
    st.header("Parameters")
    st.divider()
    st.markdown("""
    TEST
    """
    )

name = st.text_input("Enter your name:", "Guest")
st.write(f"Hello, {name}")

age = st.number_input("Enter your age:", min_value=0, max_value=120, value=25)
st.write(f"You are {age} year(s) old")

height = st.slider("Select your height (in cm):", min_value=50, max_value=250, value=170)
st.write(f"Your height is {height} cm")

options = ["Red", "Green", "Blue", "Yellow"]
favorite_color = st.selectbox("Select your favorite color:", options)
st.write(f"Your favorite color is {favorite_color}")

hobbies = ["Boise", "Vegas"]
selected_hobies = st.multiselect("Select your hobbies:", hobbies)
st.write(f"Your hobbies are: {', '.join(selected_hobies)}")

subscribe = st.checkbox("Subscribe to newsletter")
if subscribe:
    st.write("Thank you for subscribing!")
 # hifhd

@st.cache_data
def get_data() -> pd.DataFrame:
    csv_url = "https://docs.google.com/spreadsheets/d/11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE/export?format=csv&gid=1906653859"
    df = pd.read_csv(csv_url)
    return df

df = get_data()

if selected_hobies:
    df = df[df["Team"].isin(selected_hobies)]
else:
    df = df.copy()  # or leave df unchanged

st.dataframe(styled, use_container_width=True)