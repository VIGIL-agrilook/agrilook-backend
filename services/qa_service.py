import os
import re
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from config.user_data import USER_DATA
from config.crop_codes import get_crop_code, get_crop_name


def ko_basic_tokenizer(text):
    """한국어 기본 토크나이저 - 공백과 한글 문자 기준"""
    import re
    tokens = re.findall(r'[가-힣]+|[a-zA-Z0-9]+', text)
    return tokens


def load_qa_chain():
    """QA 체인 로드"""
    # 벡터 스토어 로드
    VECTOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vectorstore")
    
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        vectorstore = FAISS.load_local(
            VECTOR_DIR, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        vector_retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # 하이브리드 검색 설정
        all_docs = []
        all_texts = vectorstore.docstore._dict
        for doc_id, doc in all_texts.items():
            if hasattr(doc, 'page_content') and len(doc.page_content.strip()) > 50:
                all_docs.append(doc)
        
        if all_docs:
            # 품질 필터링 (길이 기준)
            top_quality_docs = sorted(all_docs, key=lambda x: len(x.page_content), reverse=True)[:300]
            
            processed_docs = []
            for doc in top_quality_docs:
                processed_text = " ".join(ko_basic_tokenizer(doc.page_content))
                if len(processed_text.strip()) > 10:
                    processed_doc = type(doc)(
                        page_content=processed_text, 
                        metadata=doc.metadata
                    )
                    processed_docs.append(processed_doc)
            
            if processed_docs:
                bm25_retriever = BM25Retriever.from_documents(processed_docs)
                bm25_retriever.k = 3
                
                retriever = EnsembleRetriever(
                    retrievers=[vector_retriever, bm25_retriever],
                    weights=[0.7, 0.3]
                )
            else:
                retriever = vector_retriever
        else:
            retriever = vector_retriever
        
    except Exception as e:
        print(f"하이브리드 검색 설정 중 오류: {str(e)}")
        retriever = vector_retriever
    
    # LLM 설정
    from langchain_openai import ChatOpenAI
    base_url = os.getenv("BASE_URL")
    adotx_api_key = os.getenv("ADOTX_API_KEY")
    
    llm = ChatOpenAI(
        model="ax4",
        base_url=base_url,
        api_key=adotx_api_key
    )
    
    # USER_DATA 기반 프롬프트
    crops_info = ", ".join(USER_DATA['crop']['current_crops'])
    growth_stages = ", ".join([f"{crop}({stage})" for crop, stage in USER_DATA['crop']['growth_stage'].items()])
    soil = USER_DATA['soil']
    soil_info = f"pH {soil['ph']}, 유기물 {soil['om']}g/kg, 유효인산 {soil['vldpha']}mg/kg, 칼륨 {soil['posifert_K']}cmol+/kg, 칼슘 {soil['posifert_Ca']}cmol+/kg, 마그네슘 {soil['posifert_Mg']}cmol+/kg, 전기전도도 {soil['selc']}dS/m"
    recent_intruder = USER_DATA['intruder']['recent_incidents'][0]
    intruder_info = f"{recent_intruder['time']}, {recent_intruder['type']}"

    template = f"""
너는 작물 재배, 병충해 방제, 농업 기상 해석에 전문성을 가진 농업 전문가다. 
아래 컨텍스트를 기반으로 질문에 대해 구체적이고 실용적인 농사 조언을 제공하라.

**중요: 농업 표준 단위를 반드시 사용하세요**
- 면적: a(아르) 단위 사용 (1a = 100㎡, 10a = 1,000㎡)
- 농가 면적은 통상 "몇 a" 단위로 표현
- 예: "10a당 질소 15kg", "250a 농장에서는..."

현재 사용자 농장 정보:
- 현재 날짜: 2025년 8월 12일
- 재배 작물: {crops_info}
- 생육 단계: {growth_stages}
- 토양 상태: {soil_info}
- 최근 침입자 사건: {intruder_info}

사용자 농지 데이터는 참고만 하고, 절대 새로운 수치·사실 생성 근거로 사용하지 마,
RAG 컨텍스트에서 동일 주제 관련 정보가 있을 때만 조언에 포함.
ex) 노린재 질문에 토양성분에 대한 내용을 포함하지 말고 병충해 특히 노린재에 대한 답변만 해


규칙:
1. 컨텍스트에 없는 수치·날짜·지명은 절대 생성하지 말고 "자료에 없음"이라고 작성.
2. 모든 수치·날짜·사실 정보에는 반드시 문장 옆에 출처를 함께 괄호로 표기.
3. 자료가 없는 경우 "자료에 없으므로 일반 지침 안내"처럼 명확히 표시.
4. 답변은 핵심 요약과 세부 조언으로 구성.
5. 사용자의 작물과 토양 상태를 고려한 맞춤형 조언 제공.
6. **농업 면적이나 비료량 관련 답변 시 반드시 a(아르) 단위 사용하고, 실용적인 포대수나 kg 단위도 함께 제공**.
7. **참고 문서 목록은 반드시 컨텍스트에 존재하는 문서명과 페이지 번호만 표기하고, 존재하지 않는 파일명이나 페이지는 절대 포함하지 않는다.**

컨텍스트:
{{context}}

질문:
{{question}}

답변:
"""
    
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
    
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )
    
    return qa_chain


def format_source_documents(docs) -> list:
    """출처 문서를 간단하게 포맷팅"""
    formatted_sources = []
    display_docs = docs[:3]
    
    for i, doc in enumerate(display_docs, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        
        source_name = source.replace("_ocr_OCR.pdf", "").replace("_", " ")
        if "weekly farm" in source_name.lower():
            match = re.search(r'(\d+)', source_name)
            if match:
                source_name = f"주간농사정보 제{match.group(1)}호"
        elif "cucumber" in source_name.lower():
            source_name = "오이 재배 가이드"
        elif "tomato" in source_name.lower():
            source_name = "토마토 재배 가이드"
        elif "cabbage" in source_name.lower():
            source_name = "배추 재배 가이드"
        
        formatted_sources.append(f"{i}. {source_name} (p.{page})")
    
    return formatted_sources
