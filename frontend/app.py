import streamlit as st
import requests
import json

# --- Konfiguracja ---
BACKEND_URL = "http://127.0.0.1:8000"

def main():
    """Główna funkcja aplikacji Streamlit."""
    st.set_page_config(page_title="Chatbot RAG", page_icon="🤖")

    st.title("Chatbot RAG z architekturą Backend/Frontend 🤖")
    st.caption("Interfejs użytkownika do interakcji z modelem RAG przez FastAPI.")

    # Inicjalizacja stanu sesji
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "files_processed" not in st.session_state:
        st.session_state.files_processed = False

    # Panel boczny (sidebar)
    with st.sidebar:
        st.header("Konfiguracja")
        uploaded_files = st.file_uploader(
            "Wgraj swoje pliki (PDF, MD)", 
            type=['pdf', 'md'], 
            accept_multiple_files=True
        )
        if st.button("Przetwórz pliki"):
            if uploaded_files:
                with st.spinner("Wysyłanie i przetwarzanie plików na backendzie..."):
                    files = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                    try:
                        response = requests.post(f"{BACKEND_URL}/upload", files=files)
                        if response.status_code == 200:
                            st.session_state.files_processed = True
                            st.success("Pliki przetworzone pomyślnie przez backend!")
                        else:
                            st.error(f"Błąd backendu: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Nie można połączyć się z backendem: {e}")
            else:
                st.warning("Proszę wgrać przynajmniej jeden plik.")

    # Wyświetlanie historii czatu
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Pole do wprowadzania tekstu przez użytkownika
    if prompt := st.chat_input("Zadaj pytanie na temat wgranych dokumentów..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if st.session_state.files_processed:
            with st.chat_message("assistant"):
                with st.spinner("Myślę..."):
                    try:
                        payload = {"question": prompt}
                        response = requests.post(f"{BACKEND_URL}/chat", json=payload)

                        if response.status_code == 200:
                            answer = response.json().get("answer", "Brak odpowiedzi w danych.")
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            st.error(f"Wystąpił błąd backendu: {response.text}")
                    
                    except requests.exceptions.RequestException as e:
                        st.error(f"Nie można połączyć się z backendem: {e}")
        else:
            st.warning("Proszę najpierw wgrać i przetworzyć dokumenty w panelu bocznym.")

if __name__ == '__main__':
    main() 