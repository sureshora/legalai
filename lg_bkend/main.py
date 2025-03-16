import os
import pdfplumber
import openai
from dotenv import dotenv_values
from fastapi import FastAPI, File, UploadFile, HTTPException
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from pydantic import BaseModel
import uuid

# ✅ Define Request Model
class QueryRequest(BaseModel):
    question: str

# ✅ Load environment variables
env_path = "/home/sureshwizard/projects/legalai/lg_bkend/.env"
config = dotenv_values(env_path)

os.environ["OPENAI_API_KEY"] = config.get("OPENAI_API_KEY", "")
os.environ["PINECONE_API_KEY"] = config.get("PINECONE_API_KEY", "")
os.environ["PINECONE_ENV"] = config.get("PINECONE_ENV", "us-east-1")

# ✅ Ensure API keys exist
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")

if not OPENAI_API_KEY:
    raise ValueError("❌ ERROR: Missing OpenAI API Key! Check your .env file.")

if not PINECONE_API_KEY:
    raise ValueError("❌ ERROR: Missing Pinecone API Key! Check your .env file.")

# ✅ Initialize OpenAI Client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Initialize Pinecone Client
pc = PineconeClient(api_key=PINECONE_API_KEY)

# ✅ Ensure Pinecone index exists
index_name = "legal-docs"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="euclidean",
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_ENV
        )
    )

# ✅ Connect to Pinecone Index
index = pc.Index(index_name)
embeddings = OpenAIEmbeddings()
vector_store = PineconeVectorStore(index_name=index_name, embedding=embeddings, pinecone_api_key=PINECONE_API_KEY)

# ✅ Initialize FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Legal AI API is running! Check /docs for API documentation."}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Extract text from PDF and store it in Pinecone for retrieval."""
    try:
        with pdfplumber.open(file.file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        # ✅ Generate a unique document ID
        doc_id = str(uuid.uuid4())

        # ✅ Store the document text in Pinecone
        vector_store.add_texts(texts=[text], metadatas=[{"document_id": doc_id}])

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Summarize this legal document:"}, {"role": "user", "content": text}]
        )

        return {"summary": response.choices[0].message.content, "document_id": doc_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Error processing document: {str(e)}")

@app.post("/query/")
async def query_legal_ai(request: QueryRequest):
    """Retrieve relevant legal answers using RAG."""
    try:
        results = vector_store.similarity_search(request.question, k=5)
        if not results:
            raise HTTPException(status_code=500, detail="❌ No matching legal document found in Pinecone.")

        legal_context = "\n".join([doc.page_content for doc in results])

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a legal assistant. Answer user questions based on legal context."},
                {"role": "user", "content": f"Legal Context:\n{legal_context}\n\nQuestion: {request.question}"}
            ]
        )

        return {"answer": response.choices[0].message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Error retrieving legal answer: {str(e)}")

@app.post("/contract-risk/")
async def contract_risk_analysis(file: UploadFile = File(...)):
    """Analyze contracts and highlight risky clauses."""
    try:
        with pdfplumber.open(file.file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        risk_analysis = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Analyze the given contract and highlight potential risks."},
                {"role": "user", "content": text}
            ]
        )

        return {"risks": risk_analysis.choices[0].message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Error analyzing contract: {str(e)}")
