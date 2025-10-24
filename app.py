import streamlit as st
import json
import re
from datetime import datetime
from io import BytesIO
import speech_recognition as sr
from st_audiorec import st_audiorec
from gtts import gTTS
# Assuming agents.orchestrator and tools.translator are available in your environment
from agents.orchestrator import OrchestratorAgent 
from tools.translator import translate_text, detect_language, SUPPORTED_LANGUAGES 
from tools.drug_checker import fetch_all_medicines
import base64
# --- Page Configuration ---
st.set_page_config(
    page_title="Aarogya AI",
    layout="wide",
    initial_sidebar_state="expanded",
)
# --- Background Image ---
def set_background_image(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
# NOTE: Ensure this path is correct for your environment.
# set_background_image("/Users/sanskritijha/Downloads/bg.png")
# --- TTS Helper ---
tts_placeholder = st.empty()
tts_audio = None
def speak_text(text, lang="en"):
    global tts_audio
    if not text.strip():
        return
    tts = gTTS(text=text, lang=lang)
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    tts_audio = fp.read()
    # Autoplay with stop option
    tts_placeholder.audio(tts_audio, format='audio/mp3', start_time=0, autoplay=True) # Added autoplay=True
def stop_audio():
    global tts_audio
    tts_placeholder.empty()
    tts_audio = None
# --- Routing Card Helper ---
def create_routing_card(intent_name, color, message_prefix="Query was handled by the"):
    return f"""
        <div style="background-color: rgba(26, 35, 126, 0.85); padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid {color}; color: white;">
            <strong>🚀 Agent Routing Status:</strong> {message_prefix} 
            <span style="color: {color}; font-weight: bold;">{intent_name}</span> tool.
        </div>
    """
# --- Styling ---
st.markdown("""
<style>
.main-header { font-size: 3em !important; font-weight: 900 !important; color: #1A237E !important; text-align:center; margin-bottom:0.3em !important; }
.subheader { font-size: 2.2em; color: #2E3A59; text-align:center; margin-bottom:1em; }
[data-testid="stForm"] { background-color: rgba(255,255,255,0.85); padding: 30px; border-radius:16px; box-shadow: 0 8px 30px rgba(0,0,0,0.3); border:1px solid #3498DB; }
[data-testid="stForm"] textarea { background-color: rgba(255,255,255,0.9); color:#1A237E; border:1px solid #3498DB; border-radius:8px; }
.stButton>button { background-color: #1ABC9C; color:#FFF; border-radius:8px; font-weight:bold; transition:0.3s; }
.stButton>button:hover { background-color:#16A085; transform:translateY(-1px); }
[data-testid="stSidebar"] { background-color: rgba(26,35,126,0.85); color:white; }
[data-testid="stMetricValue"] { color:#F1C40F; }
</style>
""", unsafe_allow_html=True)
# --- Header ---
st.markdown('<p class="main-header">Aarogya AI 🩺💊 </p>', unsafe_allow_html=True)
st.markdown('<p class="subheader">AI-Powered Health Agent - Connecting rural India with reliable health knowledge.</p>', unsafe_allow_html=True)
# --- Initialize Agent ---
if "agent" not in st.session_state:
    st.session_state.agent = OrchestratorAgent()
agent = st.session_state.agent
# --- Sidebar: Clear History ---
st.sidebar.markdown("### 📚 Search History")
if 'clear_history' not in st.session_state:
    st.session_state.clear_history = False
if st.sidebar.button("Clear History"):
    if hasattr(agent.memory, "history"):
        agent.memory.history = []
    st.session_state.clear_history = True
    # FIX: Replaced deprecated st.experimental_rerun() with st.rerun()
    st.rerun() 
# --- Display History ---
try:
    history = agent.memory.get_recent_history(limit=7) if hasattr(agent.memory, "get_recent_history") else []
    if history and not st.session_state.clear_history:
        for i, entry in enumerate(history):
            dt = datetime.fromisoformat(entry['timestamp']) if 'timestamp' in entry else datetime.now()
            date_str = dt.strftime("%Y-%m-%d")
            short_query = entry['query'][:30] + "..." if len(entry['query']) > 30 else entry['query']
            with st.sidebar.expander(f"**{i+1}.** {short_query} ({date_str})"):
                st.markdown(f"**Query:**\n> {entry['query']}")
                st.markdown("---")
                st.markdown(f"**Agent Response:**\n{entry['response']}")
    elif st.session_state.clear_history or not history:
        st.sidebar.info("No past queries found. Start your first analysis!")
except Exception as e:
    st.sidebar.error(f"History error: {e}")
# --- Main Content ---
response_container = st.empty()
routing_card_container = st.empty()
with st.form(key='query_form', clear_on_submit=True):
    st.markdown("#### Enter Your Health Query")
    query = st.text_area(
        "Describe your symptoms, medications, or health query:",
        height=50,
        placeholder="E.g., 'I have a fever and headache, should I take ibuprofen?'"
    )
    # 🎙️ Voice Input
    st.markdown("🎙️ Or record your query:")
    voice_data = st_audiorec()
    voice_query = ""
    if voice_data:
        recognizer = sr.Recognizer()
        # Try detecting language automatically
        for lang_code in ["hi-IN", "mr-IN", "en-US"]:
            try:
                with sr.AudioFile(BytesIO(voice_data)) as source:
                    audio = recognizer.record(source)
                    voice_query = recognizer.recognize_google(audio, language=lang_code)
                    if voice_query.strip():
                        break
            except:
                continue
        if voice_query.strip():
            st.success(f"Recognized Voice Query: {voice_query}")
        else:
            st.error("Sorry, could not understand the audio.")
    uploaded_file = st.file_uploader(
        "Upload an image (optional)", type=["jpg", "png", "jpeg"],
        help="Upload an image of a rash or prescription label."
    )
    submit_button = st.form_submit_button(label='Analyze Health Query', type="primary", use_container_width=True)
# --- Submission Logic ---
final_query = query.strip() if query.strip() else voice_query.strip()
image_uploaded = uploaded_file is not None
if submit_button and (final_query or image_uploaded):
    routing_card_container.empty()
    with st.status("🧠 Initiating Multi-Agent Workflow...", expanded=True) as status:
        
        # 1. Detect language
        detected_lang = detect_language(final_query) if final_query else "en"
        
        # 2. Translate to English for the agent
        # Only use the first two characters for gTTS language code lookup later
        tts_lang_code = {"hi":"hi","mr":"mr","en":"en"}.get(detected_lang[:2],"en") 

        query_for_agent = translate_text(final_query, "en") if detected_lang != "en" else final_query
        
        status.update(label="🩺💊 Determining intent and routing to specialized tool...")
        
        # 3. Run Agent (Input is always English)
        raw_response = agent.run_query(query_for_agent, uploaded_file, preferred_lang="en")  
        
        status.update(label="✨ Translating and displaying results...")
        
        # 4. Process Agent Response
        with response_container.container():
            st.markdown("### 📊 Agent Response Summary")
            
            # --- JSON PARSING AND FALLBACKS ---
            try:
                # Extract JSON from the raw response
                match = re.search(r"```json\s*([\s\S]+?)\s*```", raw_response)
                if match:
                    data = json.loads(match.group(1))
                    # IMPORTANT: Use the intent name as returned by the tool (now 'DRUG_CHECKER' is expected)
                    determined_intent = data.get("intent", "SYMPTOM_CHECK") 
                    simple_advice = data.get("simple_advice", "")
                    conditions = data.get("possible_conditions", [])
                    drug_warnings = data.get("medication_safety_check", [])

                else:
                    # Fallback if no JSON is found
                    data = {}
                    simple_advice = ""
                    conditions = []
                    drug_warnings = []
                    determined_intent = "SYMPTOM_CHECK"
                    
                    # FALLBACK LOGIC for failed JSON
                    if "drug" in raw_response.lower() or "interaction" in raw_response.lower() or "flexon" in query_for_agent.lower():
                        determined_intent = "DRUG_CHECKER_TOOL_FAIL" # Updated intent name
                        simple_advice = "The system routed your query to a medication safety tool but couldn't get structured data. **Always consult a registered pharmacist or doctor** before taking any new medication."
                        data['confidence_score'] = 15 
                    
            except Exception as e:
                # Fallback on JSON parsing error
                data = {}
                simple_advice = ""
                conditions = []
                drug_warnings = []
                determined_intent = "SYMPTOM_CHECK"
                # FALLBACK FOR PARSING ERROR
                if "drug" in raw_response.lower() or "interaction" in raw_response.lower() or "flexon" in query_for_agent.lower():
                    determined_intent = "DRUG_CHECKER_PARSING_FAIL" # Updated intent name
                    simple_advice = "A technical error occurred while processing the medication information. For safety, please consult a healthcare professional regarding your query about medication and symptoms."
                    data['confidence_score'] = 15
            
            # 5. Translate key elements for display and speech
            display_advice = translate_text(simple_advice, detected_lang) if simple_advice else ""
            
            display_conditions = []
            display_drug_warnings = []
            full_text_for_speech = ""
            conf_score = round(data.get('confidence_score', 0))
            
            # Build initial speech text with confidence score
            conf_score_phrase = translate_text(f"Overall confidence score is {conf_score} percent. ", detected_lang)
            full_text_for_speech += conf_score_phrase

            # --- TRANSLATION LOGIC ---
            if determined_intent in ["SYMPTOM_CHECK", "MEDICAL_KNOWLEDGE"]:
                if conditions:
                    for cond in conditions:
                        name_t = translate_text(cond.get('name', ''), detected_lang)
                        relevance_t = translate_text(cond.get('relevance', ''), detected_lang)
                        tests_t = [translate_text(t, detected_lang) for t in cond.get('tests', []) if isinstance(cond.get('tests', []), list)]
                        
                        display_conditions.append({
                            'name': name_t, 
                            'score': cond.get('score', 0), 
                            'relevance': relevance_t,
                            'tests': tests_t
                        })
                        # Build up the full text for speech for conditions
                        score = round(cond.get('score', 0), 1)
                        score_phrase = translate_text(f"{score} out of 10 chance.", detected_lang)
                        full_text_for_speech += f"{name_t}. {score_phrase}. "
            
            # *** UPDATED INTENT CHECK HERE ***
            elif determined_intent in ["DRUG_INTERACTION"]:
                if drug_warnings:
                    for warn in drug_warnings:
                        type_t = translate_text(warn.get('warning_type', ''), detected_lang)
                        desc_t = translate_text(warn.get('description', ''), detected_lang)

                        display_drug_warnings.append({
                            'type': type_t,
                            'description': desc_t
                        })
                        # Build up the full text for speech for drug warnings
                        full_text_for_speech += f"{type_t}. {desc_t}. "

            if display_advice:
                advice_phrase = translate_text("Advice: ", detected_lang)
                full_text_for_speech += f"{advice_phrase} {display_advice}"


            # 6. Display Translated Results
            
            # Routing card
            card_html = create_routing_card(determined_intent, "#3498DB", "Query was directed to the")
            routing_card_container.markdown(card_html, unsafe_allow_html=True)
            
            # Display Confidence
            st.metric(label="Overall Confidence Score", value=f"{conf_score}%")

            
            # --- CUSTOM DISPLAY LOGIC BASED ON INTENT ---
            
            if determined_intent in ["SYMPTOM_CHECK", "MEDICAL_KNOWLEDGE"]:
                # Standard display for conditions
                if display_conditions:
                    st.markdown("#### **Possible Conditions Analysis**")
                    for cond in display_conditions:
                        cond_name = cond.get('name', '')
                        cond_score = round(cond.get('score', 0), 1)
                        st.info(f"**{cond_name} ({cond_score}/10 chance)**")
                        st.markdown(f"*{cond.get('relevance','')}*")
                        tests = cond.get('tests', [])
                        if tests:
                            st.markdown("🧪 **Recommended Tests:**")
                            test_names = [t.get('name', str(t)) if isinstance(t, dict) else str(t) for t in tests]
                            st.write(", ".join(test_names))

                # Display suggested medicines if available
                suggested_medicines = data.get("suggested_medicines", [])
                if suggested_medicines:
                    st.markdown("#### 💊 **Suggested Medicines**")
                    for med in suggested_medicines:
                        st.markdown(f"**Brand Name:** {med.get('brand_name', 'N/A')}")
                        st.markdown(f"Generic Name: {med.get('generic_name', 'N/A')}")
                        st.markdown(f"Manufacturer: {med.get('manufacturer', 'N/A')}")
                        st.markdown(f"Purpose: {med.get('purpose', 'N/A')}")
                        st.markdown(f"Warnings: {med.get('warnings', 'N/A')}")
                        st.markdown("---")
                elif not display_conditions:
                    # If no conditions and no suggestions, show a message
                    st.info("No specific conditions or medicine suggestions found. Please provide more details or consult a healthcare professional.")
            
            # *** UPDATED INTENT CHECK HERE ***
            elif determined_intent in ["DRUG_INTERACTION", "DRUG_SUGGESTION"]:
                # Check if medicines are provided in the response
                medicines = data.get("medicines", [])
                if medicines:
                    st.markdown("#### 💊 **Medicines Related to Your Query**")
                    for med in medicines:
                        st.markdown(f"**Brand Name:** {med.get('brand_name', 'N/A')}")
                        st.markdown(f"Generic Name: {med.get('generic_name', 'N/A')}")
                        st.markdown(f"Manufacturer: {med.get('manufacturer', 'N/A')}")
                        st.markdown(f"Purpose: {med.get('purpose', 'N/A')}")
                        st.markdown(f"Warnings: {med.get('warnings', 'N/A')}")
                        st.markdown("---")
                # Specialized display for drug checks
                if display_drug_warnings:
                    st.markdown("#### 💊 **Medication Safety Check Results**")
                    for warn in display_drug_warnings:
                        # Use success for low/no warnings, warning for moderate/major, error for severe
                        if "critical" in warn['type'].lower() or "severe" in warn['type'].lower():
                            st.error(f"**🚨 {warn['type']}**")
                        elif "major" in warn['type'].lower() or "moderate" in warn['type'].lower():
                            st.warning(f"**⚠️ {warn['type']}**")
                        else:
                            st.success(f"**🟢 {warn['type']}**")

                        st.markdown(f"*{warn['description']}*")
                else:
                    # Fallback if intent is DRUG_INTERACTION but drug_warnings list is empty (shouldn't happen with the new drug_checker)
                    st.info("The medication checker ran, but did not find a specific result. Please rely on the Simple Advice.")

            # End of Custom Display Logic
            
            st.success("### 💊 Simple Advice")
            if display_advice:
                st.markdown(f"> {display_advice}")

            # 7. Speak the translated text aloud
            if full_text_for_speech.strip():
                speak_text(full_text_for_speech, lang=tts_lang_code)
            
        status.update(label="✅ Analysis Complete! Results Displayed.", state="complete")
        st.button("Stop", on_click=stop_audio)
elif submit_button and not final_query and not image_uploaded:
    st.error("Please enter a query, record a voice prompt, or upload an image before submitting.")

# New API endpoint to fetch all medicines
if st.sidebar.button("Fetch All Medicines"):
    medicines = fetch_all_medicines(limit=50)
    if medicines and isinstance(medicines, list):
        st.sidebar.markdown("### Medicines List (from OpenFDA)")
        for med in medicines:
            if 'error' in med:
                st.sidebar.error(med['error'])
                break
            st.sidebar.markdown(f"**Brand Name:** {med.get('brand_name', 'N/A')}")
            st.sidebar.markdown(f"Generic Name: {med.get('generic_name', 'N/A')}")
            st.sidebar.markdown(f"Manufacturer: {med.get('manufacturer', 'N/A')}")
            st.sidebar.markdown(f"Purpose: {med.get('purpose', 'N/A')}")
            st.sidebar.markdown(f"Warnings: {med.get('warnings', 'N/A')}")
            st.sidebar.markdown("---")
    else:
        st.sidebar.error("Failed to fetch medicines or no data available.")
