import streamlit as st
import requests
import json
import pandas as pd
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="Crypto Detective - RAG System",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .evidence-card {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .confidence-very-high {
        color: #0068c9;
        font-weight: bold;
    }
    .confidence-high {
        color: #83c9ff;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffb347;
        font-weight: bold;
    }
    .confidence-low {
        color: #ff6961;
        font-weight: bold;
    }
    .confidence-very-low {
        color: #ff0000;
        font-weight: bold;
    }
    .report-section {
        background-color: #f9f9f9;
        border-left: 4px solid #0068c9;
        padding: 10px 15px;
        margin: 10px 0;
    }
    .expanded-queries {
        background-color: #e6f3ff;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .main-header {
        font-size: 30px;
        color: #0068c9;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🕵️ Crypto Detective - Investigation System</h1>", unsafe_allow_html=True)
st.markdown("""
This system helps detectives solve a cybercrime case involving a cryptocurrency exchange hack.
Ask a question about the case, and the AI will retrieve relevant evidence and generate an investigation report.
""")

# Sidebar info
with st.sidebar:
    st.header("About the Case")
    st.info("""
    **Case Summary:** A crypto exchange hack resulting in the theft of $5 million in cryptocurrency.
    
    **Evidence:** Eight case files containing a mix of useful evidence and potentially misleading information.
    
    **Goal:** Use AI to quickly identify relevant evidence and generate investigation reports.
    """)
    
    st.header("How it Works")
    st.markdown("""
    1. Your query is processed using vector embeddings
    2. The system retrieves relevant evidence from case files
    3. Evidence is reranked based on relevance to your query
    4. An AI-generated investigation report is created
    5. The report is saved to an S3 bucket for future reference
    """)
    
    st.divider()
    
    # Technical details toggle
    with st.expander("Technical Details"):
        st.markdown("""
        **Retrieval Strategy:** Multi-step retrieval with query expansion
        
        **Models Used:**
        - Embeddings: text-embedding-ada-002
        - LLM: gpt-4o-mini
        
        **Vector Database:** Pinecone
        
        **Backend:** FastAPI
        
        **Frontend:** Streamlit
        """)

query = st.text_area("Enter your investigation query", height=100, 
                    placeholder="E.g., What methods did the hacker use to cover their tracks?")

with st.expander("Advanced Settings"):
    col1, col2 = st.columns(2)
    with col1:
        retrieval_strategy = st.radio(
            "Retrieval Strategy",
            ["multi-step", "single-step"],
            index=0,
            help="Multi-step expands your query and retrieves supporting evidence first"
        )
    with col2:
        top_k = st.slider(
            "Number of Evidence Documents",
            min_value=1,
            max_value=8,
            value=5,
            help="Maximum number of evidence documents to retrieve"
        )

if st.button("Investigate", type="primary", disabled=not query):
    with st.spinner("Detective AI is investigating..."):
        try:
            payload = {"query": query}
            
            response = requests.post(f"{API_URL}/investigate", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                tab1, tab2, tab3 = st.tabs(["Investigation Report", "Evidence Analysis", "Technical Details"])
                
                with tab1:
                    if result['report'].get('is_relevant') is False:
                        st.header("Query Rejected")
                        st.error("⚠️ This query is not related to the crypto exchange hack investigation")
                    else:
                        st.header("Investigation Report")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"Query: {result['query']}")
                        st.caption(f"Generated: {result['report']['timestamp']}")
                    with col2:
                        st.caption(f"Evidence Sources: {result['report'].get('evidence_count', 'N/A')}")
                        st.caption(f"Report ID: {result['storage'].get('report_id', 'N/A')}")
                    
                    if result['report'].get('is_relevant') is False:
                        st.error(result['report']['report'])
                        st.warning(f"Reason: {result['report'].get('rejection_reason', 'Query not related to the investigation')}")
                        st.info("Please rephrase your query to focus on the cryptocurrency exchange hack investigation.")
                    else:
                        report_text = result['report']['report']
                        
                        st.markdown(report_text)
                    
                    if result['storage'].get('url'):
                        st.download_button(
                            label="Download Full Report (JSON)",
                            data=json.dumps(result['report'], indent=2),
                            file_name=f"investigation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
                with tab2:
                    st.header("Retrieved Evidence")
                    
                    if result['retrieval']['strategy'] == 'multi-step' and result['retrieval'].get('expanded_queries'):
                        st.subheader("Expanded Investigation Queries")
                        with st.expander("View expanded queries used for evidence retrieval", expanded=True):
                            for i, exp_query in enumerate(result['retrieval']['expanded_queries']):
                                st.markdown(f"**Query {i+1}:** {exp_query}")
                    
                    evidence_df = []
                    
                    st.subheader("Evidence Documents")
                    for i, doc in enumerate(result['retrieval']['documents']):
                        evidence_df.append({
                            "Document": f"Doc {i+1}",
                            "Source": doc['metadata'].get('file_name', 'Unknown'),
                            "Confidence": doc['confidence'],
                            "Score": round(doc['score'] * 100, 2)
                        })
                        
                        confidence_class = f"confidence-{doc['confidence'].lower().replace(' ', '-')}"
                        st.markdown(f"""
                        <div class="evidence-card">
                            <h4>Evidence {i+1}: <span class="{confidence_class}">{doc['confidence']} Confidence ({round(doc['score'] * 100, 2)}%)</span></h4>
                            <p><strong>Source:</strong> {doc['metadata'].get('file_name', 'Unknown')}</p>
                            <p>{doc['text']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.subheader("Evidence Comparison")
                    evidence_table = pd.DataFrame(evidence_df)
                    st.dataframe(evidence_table, use_container_width=True)
                
                with tab3:
                    st.header("Technical Process Details")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Retrieval Strategy")
                        st.info(f"Strategy used: **{result['retrieval']['strategy']}**")
                        
                        if result['retrieval']['strategy'] == 'multi-step':
                            st.markdown("""
                            **Multi-step Retrieval Process:**
                            1. Original query expanded into multiple search queries
                            2. Each search query executed against the vector database
                            3. Results combined and deduplicated
                            4. Top results selected based on relevance scores
                            """)
                        else:
                            st.markdown("""
                            **Single-step Retrieval Process:**
                            1. Query directly compared to all document embeddings
                            2. Top matching documents retrieved based on vector similarity
                            """)
                    
                    with col2:
                        st.subheader("Reranking Details")
                        
                        rerank_data = []
                        for i, doc in enumerate(result['retrieval']['documents']):
                            rerank_data.append({
                                "Document": f"Doc {i+1}",
                                "Vector Score": round(doc.get('vector_score', 0) * 100, 2),
                                "Relevance Score": round(doc.get('relevance_score', 0) * 100, 2),
                                "Combined Score": round(doc['score'] * 100, 2)
                            })
                        
                        rerank_df = pd.DataFrame(rerank_data)
                        st.dataframe(rerank_df, use_container_width=True)
                        
                        st.markdown("""
                        **Reranking Process:**
                        1. Vector similarity score from initial retrieval
                        2. LLM-based relevance assessment for context understanding
                        3. Combined score calculation (40% vector + 60% relevance)
                        4. Final ranking based on combined score
                        """)
                    
                    # S3 Storage information
                    st.subheader("Report Storage")
                    if result['storage'].get('success'):
                        st.success(f"Report successfully saved to S3 bucket: {result['storage'].get('filename')}")
                        if result['storage'].get('url'):
                            st.markdown(f"Access URL (valid for 24 hours): [View Report]({result['storage'].get('url')})")
                    else:
                        st.error(f"Failed to save report to S3: {result['storage'].get('error', 'Unknown error')}")
            
            else:
                st.error(f"API Error: {response.status_code}")
                st.json(response.json())
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.caption("Crypto Detective RAG System | Developed for AI Engineer Technical Test")