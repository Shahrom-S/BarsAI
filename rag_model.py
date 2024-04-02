import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores.faiss import FAISS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def read_pdf(file_path):
    text = ""
    pdf = PdfReader(file_path)
    for page in pdf.pages:
        text += page.extract_text()
    return text

def read_word(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def read_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def read_csv_excel(file_path):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    return df.to_string()

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=1000)
    return text_splitter.split_text(text)

def get_vector_store(text_chunks, file_path):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    index_file = f"faiss_index_{os.path.basename(file_path)}"
    vector_store.save_local(index_file)

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the 
    answer is not in the provided context just say, 'answer is not in the provided context', don't provide the wrong answer.

    Context:\n{context}?\n
    Question: \n{question}\n
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.4)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

def user_input(user_question, file_path):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    index_file = f"faiss_index_{os.path.basename(file_path)}"
    new_db = FAISS.load_local(index_file, embeddings, allow_dangerous_deserialization=True)

    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    return response