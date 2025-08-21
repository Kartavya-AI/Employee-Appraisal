import os
import json
import random
from dotenv import load_dotenv

import chromadb
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please ensure it is set in your .env file.")
os.environ["GOOGLE_API_KEY"] = api_key


def load_knowledge_base_from_json(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"The knowledge base file was not found at {file_path}. Please create it.")
    except json.JSONDecodeError:
        raise ValueError(f"The file at {file_path} is not a valid JSON. Please check its format.")

KNOWLEDGE_BASE = load_knowledge_base_from_json("knowledge_base.json")

def setup_knowledge_base():
    persist_directory = "chroma_db"
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    client = chromadb.PersistentClient(path=persist_directory)
    collection_name = "appraisal_questions"

    roles_from_json = set(KNOWLEDGE_BASE.keys())
    rebuild_required = False

    try:
        collection = client.get_collection(name=collection_name)
        existing_metadata = collection.get(include=["metadatas"])
        
        if existing_metadata and existing_metadata['metadatas']:
            roles_in_db = set(meta.get('role', None) for meta in existing_metadata['metadatas'])
        else:
            roles_in_db = set()
            
        if roles_in_db != roles_from_json:
            print("Knowledge base roles mismatch detected. Rebuilding database...")
            rebuild_required = True
            client.delete_collection(name=collection_name)
    except ValueError:
        print("Collection not found. A new one will be created.")
        rebuild_required = True

    vector_store = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )

    if rebuild_required or vector_store._collection.count() == 0:
        print("Populating database with questions...")
        documents, metadata, ids = [], [], []
        for role, questions in KNOWLEDGE_BASE.items():
            for i, q in enumerate(questions):
                documents.append(q["question"])
                meta = {
                    "role": role,
                    "full_question": q["question"],
                    "options": "||".join(q["options"]),
                    "answer": q["answer"]
                }
                metadata.append(meta)
                ids.append(f"{role.replace(' ', '_')}_{i}")
        vector_store.add_texts(texts=documents, metadatas=metadata, ids=ids)
        print("Database population complete.")
    else:
        print("Database is up-to-date and already populated.")
        
    return vector_store

def get_questions_for_role(vector_store: Chroma, role: str, num_questions: int = 10):
    all_role_questions_data = vector_store._collection.get(where={"role": role})
    metadatas = all_role_questions_data.get("metadatas", [])

    if not metadatas:
        return []

    questions = []
    for meta in metadatas:
        question_obj = {
            "question": meta.get("full_question"),
            "options": meta.get("options", "").split("||"),
            "answer": meta.get("answer")
        }
        questions.append(question_obj)

    random.shuffle(questions)
    return questions[:num_questions]

def get_feedback(score: int, total_questions: int, role: str) -> str:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.7)
    prompt_template = PromptTemplate.from_template(
        """
        You are an expert HR Manager providing detailed feedback for an employee's appraisal test. The employee is being assessed for the role of: **{role}**. The employee's score is: **{score} out of {total_questions}**.

        Please provide a comprehensive and detailed performance review based on this score. The tone should be constructive, professional, and encouraging. Structure the feedback using the following markdown format:

        ### Overall Performance Analysis
        Start with a summary paragraph analyzing the score. Categorize the performance (e.g., Excellent, Very Good, Good, Needs Improvement, Foundational) and explain what this score generally indicates about their current skill level for the '{role}' position.

        ### Key Strengths
        Based on the score, describe the employee's likely strengths. For a high score, highlight deep expertise and readiness for more complex challenges. For an average score, acknowledge a solid understanding of core concepts. For a low score, focus on their foundational knowledge and willingness to learn.

        ### Areas for Professional Development
        Identify specific areas for improvement constructively. For a high score, suggest exploring advanced topics or leadership skills. For an average score, recommend focusing on specific intermediate topics. For a low score, gently outline the core competency areas that need attention.

        ### Recommended Next Steps & Resources
        Provide a bulleted list of actionable next steps like specific courses, books, or projects relevant to their role.

        ### Concluding Remarks
        End with an encouraging and motivational closing statement, reinforcing their value and your support for their growth.
        """
    )
    chain = prompt_template | llm | StrOutputParser()
    response = chain.invoke({"score": score, "total_questions": total_questions, "role": role})
    return response