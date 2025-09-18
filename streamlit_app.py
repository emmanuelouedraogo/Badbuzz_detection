# /full/path/to/your/project/badbuzz_detection/streamlit_app.py
import streamlit as st
import requests
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Sentiment Analysis AI",
    page_icon="🧠",
    layout="wide",  # Use wide layout for more space
    initial_sidebar_state="auto",
)

# --- Custom CSS for dynamic progress bar color ---
st.markdown(
    """
<style>
    .st-emotion-cache-115fc2v {
        width: 100%;
    }
    /* Class for positive sentiment progress bar */
    .positive-progress .st-emotion-cache-115fc2v.e115fc2v0 {
        background-color: #28a745; /* Green */
    }
    /* Class for negative sentiment progress bar */
    .negative-progress .st-emotion-cache-115fc2v.e115fc2v0 {
        background-color: #dc3545; /* Red */
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- API Configuration ---
# The URL for the Flask API is loaded from an environment variable.
# For local development, it's set in the .env file.
# For Docker, it will be set in docker-compose.yml.
API_URL = os.getenv("API_URL", "http://api:5000/predict")


# --- Functions ---
def set_text(text):
    """Callback to set the text area content."""
    st.session_state.text_input = text


# --- Session State Initialization ---
if "text_input" not in st.session_state:
    st.session_state.text_input = "I love this product, it's absolutely fantastic!"

# --- Main Interface ---
st.title("Advanced Sentiment Analysis AI 🧠✨")
st.markdown(
    "An AI-powered tool to analyze the sentiment of any text. "
    "This app classifies text as **Positive** or **Negative**."
)
st.divider()

# --- Example Buttons ---
st.subheader("Try with an example:")
cols = st.columns(2)
with cols[0]:
    st.button(
        "Positive Example 😄",
        on_click=set_text,
        args=(
            "This is the best movie I have seen in years! The acting was superb and the plot was gripping.",
        ),
        use_container_width=True,
    )
with cols[1]:
    st.button(
        "Negative Example 😠",
        on_click=set_text,
        args=(
            "The service was terrible. I waited for an hour and the food was cold. I will not be coming back.",
        ),
        use_container_width=True,
    )

# --- Text Input ---
user_input = st.text_area(
    "Or enter your own text to analyze:",
    key="text_input",
    height=150,
    placeholder="Type or paste your text here...",
)

# --- Analysis Trigger ---
if st.button("Analyze Sentiment", type="primary", use_container_width=True):
    if user_input:
        try:
            payload = {"text": user_input}
            with st.spinner("🤖 AI is thinking..."):
                response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                result = response.json()
                prediction = result.get("prediction")
                raw_score = result.get("confidence_score")

                # L'API retourne le score de la classe "Positive".
                # Nous calculons la confiance dans le label prédit.
                display_confidence = (
                    raw_score if prediction == "Positive" else 1 - raw_score
                )

                st.divider()
                st.subheader("✨ Analysis Result")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        label="Predicted Sentiment",
                        value=prediction,
                        delta="👍" if prediction == "Positive" else "👎",
                    )

                with col2:
                    progress_bar_class = (
                        "positive-progress"
                        if prediction == "Positive"
                        else "negative-progress"
                    )
                    st.write(f"Confidence in Prediction: **{display_confidence:.2%}**")
                    st.markdown(
                        f'<div class="{progress_bar_class}">', unsafe_allow_html=True
                    )
                    st.progress(display_confidence)
                    st.markdown("</div>", unsafe_allow_html=True)

                with st.expander("Show Technical Details"):
                    st.write(f"Raw model score: `{raw_score:.4f}`")
                    st.write("_Model convention: score > 0.5 is Positive._")
                    st.json(result)
            else:
                st.error(
                    f"API Error (Code: {response.status_code}). Please ensure the Flask server is running correctly."
                )
                st.json(response.json())
        except requests.exceptions.ConnectionError:
            st.error(
                "Connection to API failed. Please make sure the Flask server (app.py) is running."
                + f" (Attempted to connect to: {API_URL})"
            )
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.warning("Please enter some text to analyze.")

st.divider()
st.markdown(
    "<p style='text-align: center; color: grey;'>Made with ❤️ using Streamlit & Flask</p>",
    unsafe_allow_html=True,
)
