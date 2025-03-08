# AI Detective Challenge: Retrieval-Augmented Generation (RAG) System

An AI-powered RAG system to assist detectives in solving a cryptocurrency exchange hack case. This system processes case files, retrieves relevant evidence, and generates detailed investigation reports.

## 🔍 System Features

- **Vector Embeddings**: Store case files as vector embeddings for semantic search
- **Multi-Step Retrieval**: Expand queries to find relevant evidence across case files
- **Evidence Reranking**: Rerank documents based on relevance to the query
- **Investigation Reports**: Generate detailed reports from the retrieved evidence
- **S3 Storage**: Save reports to an S3 bucket for future reference
- **Web UI**: User-friendly interface for detectives to interact with the system
- **Guard Agent**: AI-powered validation to ensure queries relate to the crypto hack investigation

## 🏗️ Architecture

The system uses a multi-component architecture:

1. **Guard Agent**: Validates incoming queries to ensure they're related to the investigation
2. **Document Processing**: Convert case files into embeddings with text-embedding-ada-002
3. **Vector Database**: Pinecone for storing and searching document embeddings
4. **Retrieval Engine**: Implement both single-step and multi-step retrieval strategies
5. **Reranking System**: Improve retrieval quality using LLM-based relevance scoring
6. **Report Generation**: Create investigation reports using gpt-mini-4o-mini
7. **Storage Layer**: Save reports to Amazon S3
8. **API Layer**: FastAPI backend for handling requests
9. **UI Layer**: Streamlit frontend for detective interaction

## 🛠️ Technical Stack

- **Embeddings**: OpenAI's text-embedding-ada-002
- **LLM**: OpenAI's gpt-mini-4o-mini
- **Vector Database**: Pinecone
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Storage**: Amazon S3
- **Language**: Python 3.9+

## 📋 Setup and Installation

### Prerequisites

- Python 3.9+
- Pinecone API key
- OpenAI API key
- AWS credentials

### Environment Setup

1. Clone the repository:

```bash
git clone [repo-url]
```

2. Create a virtual environment and install dependencies:

```bash
conda create -n `your_project` python==3.10 -y
conda activate `your_project`
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export PINECONE_API_KEY="your-pinecone-api-key"
export PINECONE_ENVIRONMENT="your-pinecone-environment"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-key"
export AWS_REGION="your-region"
export S3_BUCKET="your-bucket"
```

### Case Files

Place your case files (in .txt format) in the `data/case_files/` directory. The system expects text files containing case evidence.

### Loading Documents

Before using the system, load the case files into the vector database: