import streamlit as st
import requests
import os
import time

# Backend osoite
BACKEND_HOST = os.environ.get("BACKEND_HOST", "http://127.0.0.1:8000")

def render_tab_insights():
    st.markdown("### ✨ Konsultoi AI-tiimiä (CrewAI)")
    
    # Näytä valittu malli
    current_model = st.session_state.get("selected_model", "qwen3.6:35b-a3b")
    st.markdown(f"🧠 **Käytössä:** `{current_model}` | *Vaihda mallia vasemman reunan Hallinta-paneelista*")
    
    if "agent_chat_history" not in st.session_state:
        st.session_state.agent_chat_history = []
    if "chat_is_generating" not in st.session_state:
        st.session_state.chat_is_generating = False
        
    def add_message(role, content):
        st.session_state.agent_chat_history.append({"role": role, "content": content})

    def start_chat_task(prompt):
        add_message("user", prompt)
        st.session_state.chat_is_generating = True
        try:
            requests.post(
                f"{BACKEND_HOST}/api/chat",
                json={
                    "message": prompt, 
                    "model": current_model,
                    "history": st.session_state.agent_chat_history
                },
                timeout=5
            )
        except Exception as e:
            print(f"Chat start error: {e}")
        
    with st.expander("🚀 Valmiit tehtävänannot tiimille", expanded=not st.session_state.chat_is_generating):
        st.caption("Valitse alta valmis komento, jonka Analyysipäällikkö delegoi oikealle agentille:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Luo osastoanalyysi (Data-analyytikko)", use_container_width=True, disabled=st.session_state.chat_is_generating):
                start_chat_task("Tutki tietokannasta, mitkä osastot ovat suosituimpia ja luo niistä selkeä Markdown-taulukko.")
                st.rerun()
            if st.button("🗺️ Kärryreitit Pythonilla (Visualisoija)", use_container_width=True, disabled=st.session_state.chat_is_generating):
                start_chat_task("Kirjoita Python-koodi, joka visualisoi kärryjen X/Y-koordinaatit kartalle (Heatmap) Matplotlib-kirjastolla.")
                st.rerun()
        with col2:
            if st.button("🛒 Analysoi kassaruuhkat (Ali Baba)", use_container_width=True, disabled=st.session_state.chat_is_generating):
                start_chat_task("Selvitä, mihin aikaan kassalla (checkout) on eniten ruuhkaa, ja anna kehitysehdotuksia myymäläpäällikölle.")
                st.rerun()
            if st.button("🗑️ Tyhjennä keskusteluhistoria", use_container_width=True, disabled=st.session_state.chat_is_generating):
                st.session_state.agent_chat_history = []
                st.rerun()

    st.divider()

    chat_container = st.container(height=500)
    
    with chat_container:
        for msg in st.session_state.agent_chat_history:
            if msg["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    content = msg["content"]
                    if content.startswith("__IMG_B64__"):
                        # Pura base64-kuva ja teksti talteen
                        parts = content.split("__CONTENT__", 1)
                        img_b64 = parts[0].replace("__IMG_B64__", "")
                        text = parts[1] if len(parts) > 1 else ""
                        st.image(f"data:image/png;base64,{img_b64}",
                                 caption="UWB Heatmap – kärryjen liikkuminen pohjakuvan päällä",
                                 use_container_width=True)
                        if text:
                            st.markdown(text)
                    else:
                        st.markdown(content)
                    
        # Polling logiikka (Reasoning-näkymä lennossa)
        if st.session_state.chat_is_generating:
            with st.chat_message("assistant", avatar="🤖"):
                try:
                    res = requests.get(f"{BACKEND_HOST}/api/report-status", timeout=5)
                    if res.status_code == 200:
                        status_data = res.json()
                        
                        # Jos on vielä käynnissä
                        if status_data.get("generating", True):
                            st.markdown(f"🔄 **{status_data.get('current_step', 'Odotetaan...')}**")
                            reason_steps = status_data.get("reasoning_steps", [])
                            with st.expander("Tekoälytiimin prosessi (Reasoning-näkymä)", expanded=True):
                                for step in reason_steps:
                                    st.caption(step)
                            time.sleep(2)
                            st.rerun()
                            
                        # Jos on valmis tai virhe
                        else:
                            st.session_state.chat_is_generating = False
                            if status_data.get("current_step") == "Valmis":
                                ans = status_data.get("report_content", "Valmis!")
                                img_b64 = status_data.get("image_b64")
                                # Heatmap: tallenna base64 sessioon, jotta se näkyy historiassa
                                if img_b64:
                                    add_message("assistant", f"__IMG_B64__{img_b64}__CONTENT__{ans}")
                                else:
                                    add_message("assistant", ans)
                            else:
                                ans = f"⚠️ Agentti kohtasi virheen: {status_data.get('reasoning_steps', ['Tuntematon virhe'])[-1]}"
                                add_message("assistant", ans)
                            
                            # Nollataan taustan status
                            requests.post(f"{BACKEND_HOST}/api/cancel-report", timeout=2)
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"Yhteysvirhe taustapalveluun: {e}")
                    st.session_state.chat_is_generating = False
                    time.sleep(2)
                    st.rerun()
                
    if prompt := st.chat_input("Kirjoita viesti Analyysipäällikölle...", disabled=st.session_state.chat_is_generating):
        start_chat_task(prompt)
        st.rerun()
