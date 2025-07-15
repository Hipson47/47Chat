import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import ConversationalRetrievalChain

# Opcja 1: Model Google Vertex AI (Gemini)
# from langchain_google_vertexai import VertexAI

# Opcja 2: Model OpenAI (GPT)
from langchain_openai import ChatOpenAI

# --- Konfiguracja ---
# Ustaw swoje klucze API jako zmienne środowiskowe
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/credentials.json"
# Upewnij się, że klucz API OpenAI jest ustawiony w zmiennych środowiskowych
# Na przykład: os.environ["OPENAI_API_KEY"] = "twoj_klucz_api_openai"

# Zmienna globalna do przechowywania wektorowej bazy danych
vectorstore = None

app = FastAPI(
    title="Backend RAG Chatbot",
    description="API do obsługi chatbota RAG z zewnętrznymi modelami językowymi.",
    version="1.0.0",
)

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None # Placeholder for future session management

def process_text_from_files(files: List[UploadFile]):
    """Wyodrębnia tekst z wgranych plików (PDF, MD)."""
    full_text = ""
    for file in files:
        if not file.filename:
            continue
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(file.file.read())

        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(temp_path)
        elif file.filename.endswith(".md"):
            loader = TextLoader(temp_path)
        else:
            continue # Ignoruj nieobsługiwane typy plików
            
        documents = loader.load()
        for doc in documents:
            full_text += doc.page_content + "\n"
        
        os.remove(temp_path)
    return full_text

def get_text_chunks(text):
    """Dzieli tekst na mniejsze kawałki."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def create_vectorstore(text_chunks):
    """Tworzy wektorową bazę danych z kawałków tekstu."""
    if not text_chunks:
        return None
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Endpoint do wgrywania i przetwarzania plików."""
    global vectorstore
    if not files:
        raise HTTPException(status_code=400, detail="Nie wgrano żadnych plików.")
    
    try:
        raw_text = process_text_from_files(files)
        if not raw_text:
            raise HTTPException(status_code=400, detail="Nie udało się wyodrębnić tekstu z plików.")
            
        text_chunks = get_text_chunks(raw_text)
        vectorstore = create_vectorstore(text_chunks)
        
        if vectorstore is None:
             raise HTTPException(status_code=500, detail="Nie udało się stworzyć bazy wektorowej.")

        return JSONResponse(content={"message": "Pliki przetworzone pomyślnie."}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wystąpił błąd: {str(e)}")


@app.post("/chat")
async def chat_with_rag(request: ChatRequest):
    """Endpoint do zadawania pytań do załadowanych dokumentów."""
    global vectorstore
    if vectorstore is None:
        raise HTTPException(status_code=400, detail="Baza wektorowa nie została zainicjowana. Proszę najpierw wgrać pliki.")

    question = request.question
    
    try:
        retriever = vectorstore.as_retriever()

        # --- Wybór modelu LLM ---
        # Opcja 1: Gemini 1.5 Flash (zakomentowane)
        # llm = VertexAI(model_name="gemini-1.5-flash-001")

        # Opcja 2: GPT-4o-mini
        llm = ChatOpenAI(model="gpt-3.5-turbo")
        
        template = """Odpowiedz na pytanie użytkownika opierając się tylko i wyłącznie na poniższym kontekście. Jeśli w kontekście nie ma odpowiedzi, poinformuj o tym.
        Kontekst: {context}
        Pytanie: {question}"""
        
        prompt_template = PromptTemplate.from_template(template)

        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt_template
            | llm
            | StrOutputParser()
        )

        response = rag_chain.invoke(question)
        
        return JSONResponse(content={"answer": response})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wystąpił błąd podczas generowania odpowiedzi: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 