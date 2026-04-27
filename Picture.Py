import streamlit as st
import numpy as np
from PIL import Image
import pandas as pd
from sklearn.cluster import KMeans
import io
import random

st.set_page_config(page_title="Image K-Means Clustering", layout="wide")

st.title("Image K-Means Clustering")

col1, col2 = st.columns(2)

with col1:
    st.header("Upload & Configure") 
    
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "bmp"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Image", use_column_width=True)
        
        num_clusters = st.number_input(
            "Number of Clusters",
            min_value=2,
            max_value=10,
            value=3
        )
        
        st.subheader("Initial Cluster Colors")

        DEFAULT_COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF",
                          "#00FFFF", "#FF8800", "#8800FF", "#00FF88", "#FF0088"]

        colors = []
        for i in range(num_clusters):
            use_random = st.checkbox(f"Random color for Cluster {i+1}", key=f"rand_{i}")
            if use_random:
                colors.append(None)
            else:
                hex_color = st.color_picker(
                    f"Cluster {i+1} Color",
                    value=DEFAULT_COLORS[i],
                    key=f"color_{i}"
                )
                rgb = tuple(int(hex_color[j:j+2], 16) for j in (1, 3, 5))
                colors.append(rgb)
        
        if st.button("Process Image", type="primary"):
            # Resolve any random colors now
            resolved = []
            for c in colors:
                if c is None:
                    resolved.append((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
                else:
                    resolved.append(c)
            st.session_state.colors = resolved
            st.session_state.process = True

with col2:
    st.header("Result")
    
    if uploaded_file and st.session_state.get("process"):
        img_array = np.array(image.convert("RGB"))
        h, w = img_array.shape[:2]

        pixels = img_array.reshape(-1, 3).astype(np.float32)

        resolved_colors = st.session_state.colors
        initial_centers = np.array(resolved_colors, dtype=np.float32)

        kmeans = KMeans(
            n_clusters=len(resolved_colors),
            init=initial_centers,
            n_init=1,
            random_state=42
        )

        labels = kmeans.fit_predict(pixels)

        # Always map back to the exact user-selected colors
        output_colors = np.array(resolved_colors, dtype=np.uint8)
        clustered_pixels = output_colors[labels]

        clustered_image = clustered_pixels.reshape(h, w, 3)
        clustered_pil = Image.fromarray(clustered_image)

        st.image(clustered_pil, caption="Clustered Image", use_column_width=True)

        img_byte_arr = io.BytesIO()
        clustered_pil.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        st.download_button(
            label="Download Clustered Image",
            data=img_byte_arr,
            file_name="clustered_image.png",
            mime="image/png"
        )