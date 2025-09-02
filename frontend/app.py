import streamlit as st
import requests
import json
import time
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"  # Consider making this configurable via env or query param

def display_orchestration_result(transcript: Dict[str, Any]):
    """
    Displays the orchestration result in a structured way.
    """
    st.subheader("🎯 Original Question")
    st.write(transcript.get("user_prompt", ""))
    
    # Display RAG context if available
    if transcript.get("rag_context"):
        with st.expander("📚 Retrieved Context", expanded=False):
            st.text(transcript["rag_context"])
    
    # Display assigned teams
    if transcript.get("assigned_teams"):
        st.subheader("👥 Assigned Teams")
        teams_str = ", ".join(transcript["assigned_teams"])
        st.info(f"Teams: {teams_str}")
    
    # Display each phase of the discussion
    st.subheader("💬 Multi-Agent Discussion")
    
    phases = transcript.get("phases", [])
    for phase_data in phases:
        phase_name = phase_data.get("phase_name", "Unknown Phase")
        contributions = phase_data.get("contributions", [])
        
        with st.expander(f"🔄 Phase: {phase_name}", expanded=True):
            for contrib in contributions:
                alter_name = contrib.get("alter_name", "Unknown Alter")
                response = contrib.get("response", "No response")
                
                # Use different colors/styles for different alters
                st.markdown(f"**{alter_name}:**")
                st.write(response)
                st.divider()
    
    # Display final decision
    final_decision = transcript.get("final_decision", "")
    if final_decision:
        if "error" in final_decision.lower():
            st.error(f"❌ Final Decision: {final_decision}")
        else:
            st.success(f"✅ Final Decision: {final_decision}")
    else:
        st.warning("⚠️ No final decision was generated")

def check_backend_health():
    """
    Checks if the backend is healthy and returns status information.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"status": "unreachable", "error": str(e)}

def wait_until_backend_ready(max_wait_seconds: int = 45) -> Dict[str, Any]:
    """Polls backend health until healthy or timeout, showing a loading placeholder."""
    placeholder = st.empty()
    start = time.time()
    while True:
        status = check_backend_health()
        elapsed = int(time.time() - start)
        with placeholder.container():
            st.info(f"Starting backend... ({elapsed}s)")
            if status.get("status") == "healthy":
                st.success("Backend is healthy")
                return status
            st.progress(min(elapsed / max_wait_seconds, 1.0))
        if status.get("status") == "healthy":
            return status
        if elapsed >= max_wait_seconds:
            return status
        time.sleep(1.5)

def main():
    """Main Streamlit application function."""
    st.set_page_config(
        page_title="47Chat Orchestrator", 
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 47Chat - Multi-Agent AI Orchestrator")
    st.caption("Intelligent multi-agent discussions powered by local LLMs and RAG")

    # Initialize session state
    if "discussions" not in st.session_state:
        st.session_state.discussions = []
    if "files_uploaded" not in st.session_state:
        st.session_state.files_uploaded = False

    # Sidebar for configuration and file upload
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Backend health check with bootstrap wait
        health_status = check_backend_health()
        if health_status.get("status") != "healthy":
            with st.spinner("Waiting for backend to become healthy..."):
                health_status = wait_until_backend_ready()
        if health_status.get("status") == "healthy":
            st.success("✅ Backend is healthy")
            if health_status.get("ollama_available"):
                st.success("✅ Ollama is available")
            else:
                st.warning("⚠️ Ollama not available")
            
            if health_status.get("rag_store_exists"):
                st.info("📚 RAG store exists")
            else:
                st.info("📚 No RAG store found")
        else:
            st.error(f"❌ Backend: {health_status.get('error', 'Unknown error')}")
        
        st.divider()
        
        # File upload section
        st.subheader("📁 Document Upload")
        uploaded_files = st.file_uploader(
            "Upload documents (PDF, MD, TXT)", 
            type=['pdf', 'md', 'txt'], 
            accept_multiple_files=True
        )
        
        if st.button("📤 Process Files"):
            if uploaded_files:
                with st.spinner("Uploading and processing files..."):
                    files_data = []
                    for file in uploaded_files:
                        files_data.append(("files", (file.name, file.getvalue(), file.type)))
                    
                    try:
                        response = requests.post(f"{BACKEND_URL}/upload/", files=files_data)
                        if response.status_code == 200:
                            st.session_state.files_uploaded = True
                            result = response.json()
                            st.success(f"✅ {result['message']}")
                            st.json(result.get('files', []))
                        else:
                            st.error(f"❌ Backend error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Connection error: {e}")
            else:
                st.warning("Please upload at least one file.")
        
        st.divider()
        
        # RAG toggle
        use_rag = st.checkbox("🧠 Use RAG Context", value=True, 
                             help="Enable to use uploaded documents for context")

    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("💭 Ask a Question")
        
        # Question input
        question = st.text_area(
            "Enter your question:",
            placeholder="How can I improve my application's architecture?",
            height=100
        )
        
        if st.button("🚀 Start Orchestration", type="primary"):
            if question.strip():
                with st.spinner("Running multi-agent orchestration..."):
                    try:
                        payload = {
                            "question": question,
                            "use_rag": use_rag
                        }
                        
                        response = requests.post(f"{BACKEND_URL}/orchestrate/", json=payload)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("status") == "success":
                                transcript = result.get("transcript", {})
                                st.session_state.discussions.insert(0, transcript)
                                st.success("✅ Orchestration completed!")
                            else:
                                st.error("❌ Orchestration failed")
                        else:
                            error_detail = response.json().get("detail", response.text)
                            st.error(f"❌ Backend error: {error_detail}")
                            
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Connection error: {e}")
            else:
                st.warning("Please enter a question first.")
    
    with col2:
        st.subheader("📊 Discussion Results")
        
        if st.session_state.discussions:
            # Show the most recent discussion
            latest_discussion = st.session_state.discussions[0]
            display_orchestration_result(latest_discussion)
            
            # Show history
            if len(st.session_state.discussions) > 1:
                with st.expander("📝 Discussion History", expanded=False):
                    for i, discussion in enumerate(st.session_state.discussions[1:], 1):
                        st.write(f"**Discussion {i}:** {discussion.get('user_prompt', 'Unknown')[:50]}...")
                        if st.button(f"View Discussion {i}", key=f"view_{i}"):
                            display_orchestration_result(discussion)
        else:
            st.info("No discussions yet. Ask a question to get started!")
    
    # Footer
    st.divider()
    st.caption("Powered by 47Chat Multi-Agent Orchestrator | Local LLMs + RAG")

if __name__ == '__main__':
    main()