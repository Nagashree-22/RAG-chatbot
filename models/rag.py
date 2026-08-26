
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


# Load embedding model
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# Load knowledge base
loader = TextLoader(
    "data/knowledge.txt",
    encoding="utf-8"
)


documents = loader.load()


# Split documents into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)


docs = splitter.split_documents(documents)


# Create vector database
db = Chroma.from_documents(
    documents=docs,
    embedding=embedding,
    persist_directory="vector_db"
)


# Save database
db.persist()


# Create retriever
retriever = db.as_retriever(
    search_kwargs={"k": 3}
)

