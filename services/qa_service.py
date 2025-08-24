import os
import re
import logging
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema.runnable import RunnableLambda
from config.user_data import USER_DATA

logger = logging.getLogger(__name__)

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
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        vectorstore = FAISS.load_local(
            VECTOR_DIR, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        vector_retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # 임시로 벡터 검색만 사용 (BM25 비활성화)
        retriever = vector_retriever
        logging.info("[QA] Using vector retriever only (BM25 disabled for debugging)")
        
    except Exception as e:
        logger.exception("벡터스토어 설정 중 오류")
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
    
    # 농업 지식 기반 프롬프트 (농장 정보 참고)
    # USER_DATA 임포트
    from config.user_data import USER_DATA
    from services.soil_fertilizer_cache import fertilizer_cache
    
    # USER_DATA를 안전하게 문자열로 변환 (중괄호 이스케이프)
    user_data_str = str(USER_DATA).replace('{', '{{').replace('}', '}}')
    
    # 비료 캐시를 안전하게 문자열로 변환
    fertilizer_info_str = str(fertilizer_cache).replace('{', '{{').replace('}', '}}') if fertilizer_cache else "없음"
    
    template = f"""
너는 작물 재배, 병충해 방제, 농업 기술에 전문성을 가진 농업 전문가다. 
아래 농업 문서 컨텍스트를 기반으로 질문에 대해 구체적이고 실용적인 농사 조언을 제공하라.

**중요: 농업 표준 단위를 반드시 사용하세요**
- 면적: a(아르) 단위 사용 (1a = 100㎡, 10a = 1,000㎡)
- 농가 면적은 통상 "몇 a" 단위로 표현
- 예: "10a당 질소 15kg", "250a 농장에서는..."

사용자 농장 정보 (참고용):
{user_data_str}

현재 비료 처방 정보 (참고용):
{fertilizer_info_str}

답변 원칙:
- 제공된 농업 문서 컨텍스트에서만 정보를 추출하여 답변 (농업기술길잡이, 주요농사기술, 주간농업정보 등)
- 사용자 농장 정보는 답변을 개인화하는 참고 자료로만 활용 (토양/비료 수치는 직접 언급하지 않음)
- **비료/처방 관련 질문 시에는 위의 "현재 비료 처방 정보"를 적극 활용하여 구체적인 비료명, 사용량, 포대수 등을 포함한 맞춤형 답변 제공**
- 일반적인 농업 기술 지식과 시기별 농작업 정보에 집중
- 주간농업정보(25~31일)에서 시기별 작업 가이드 제공 가능
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
    
    QA_CHAIN_PROMPT = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    logging.info(f"[QA] Creating custom QA chain with input variables: {QA_CHAIN_PROMPT.input_variables}")
    
    # RetrievalQA 대신 수동으로 QA 체인 구성
    from langchain.chains import LLMChain
    from langchain.schema.runnable import RunnableLambda
    from langchain.schema import Document
    
    def qa_chain_func(inputs):
        question = inputs["question"]
        
        # 1. 검색 수행
        docs = retriever.get_relevant_documents(question)
        
        # 2. 컨텍스트 생성
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # 3. LLM 체인 생성 및 실행
        llm_chain = LLMChain(llm=llm, prompt=QA_CHAIN_PROMPT)
        result = llm_chain.run(context=context, question=question)
        
        return {
            "result": result,
            "source_documents": docs
        }
    
    qa_chain = RunnableLambda(qa_chain_func)
    
    logging.info("[QA] Custom QA chain created successfully")
    
    return qa_chain


def format_source_documents(docs) -> list:
    """출처 문서를 간단하게 포맷팅 - 페이지 정보 및 URL 포함"""
    formatted_sources = []
    display_docs = docs[:3]
    
    for i, doc in enumerate(display_docs, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page")
        
        # 파일명 정리
        source_name = source.replace("_OCR.pdf", "").replace("_OCR.PDF", "").replace("_", " ")
        
        # 문서별 URL 매핑 (build_vectorstore.py의 DOCUMENT_URLS와 동일)
        doc_url = None
        
        if "주간농사정보" in source_name:
            # 주간농사정보 제33호(2025.8.25.~8.31.).pdf → 주간농사정보 제33호
            match = re.search(r'제(\d+)호', source_name)
            if match:
                source_name = f"주간농사정보 제{match.group(1)}호"
                doc_url = "https://www.nongsaro.go.kr/portal/contentsFileView.do?cntntsNo=262533&fileSeCode=185001&fileSn=1"
        elif "농업기술길잡이" in source_name:
            # 농업기술길잡이_115_고추_OCR.pdf → 농업기술길잡이 - 고추
            if "고추" in source_name:
                source_name = "농업기술길잡이 - 고추"
                doc_url = "https://www.nongsaro.go.kr/portal/ps/psb/psbx/cropEbookLst.ps?menuId=PS65290&sText=&pageIndex=1&pageSize=10&sKeyword=&sNameOrderAt=Y&group2Cnt=&cropEbookGubunChk=&sStdPrdlstCode=&sStdTchnlgyCode=&stdPrdlstCode=&sRdaStdPrdlstCode=&sRdaStdTchnlgyCode=&kidofcomdtyNo=0&sOldDtShowAt=N&sSearchText=&sSearchType=srchType02&cNo=53&stdItemCd=VC011205&cropsEbookNm=%EA%B3%A0%EC%B6%94"
            elif "부추" in source_name:
                source_name = "농업기술길잡이 - 부추"
                doc_url = "https://www.nongsaro.go.kr/portal/ps/psb/psbx/cropEbookLst.ps?menuId=PS65290&sText=&pageIndex=1&pageSize=10&sKeyword=&sNameOrderAt=Y&group2Cnt=&cropEbookGubunChk=&sStdPrdlstCode=&sStdTchnlgyCode=&stdPrdlstCode=&sRdaStdPrdlstCode=&sRdaStdTchnlgyCode=&kidofcomdtyNo=0&sOldDtShowAt=N&sSearchText=&sSearchType=srchType02&cNo=61&stdItemCd=VC021010&cropsEbookNm=%EB%B6%80%EC%B6%94"
            elif "파" in source_name:
                source_name = "농업기술길잡이 - 파"
                doc_url = "https://www.nongsaro.go.kr/portal/ps/psb/psbx/cropEbookLst.ps?menuId=PS65290&sText=&pageIndex=1&pageSize=10&sKeyword=&sNameOrderAt=Y&group2Cnt=&cropEbookGubunChk=&sStdPrdlstCode=&sStdTchnlgyCode=&stdPrdlstCode=&sRdaStdPrdlstCode=&sRdaStdTchnlgyCode=&kidofcomdtyNo=0&sOldDtShowAt=N&sSearchText=&sSearchType=srchType02&cNo=133&stdItemCd=VC041202&cropsEbookNm=%ED%8C%8C"
        elif "주요 농사기술" in source_name:
            if "1" in source_name:
                source_name = "주요 농사기술-1"
                doc_url = "https://www.nongsaro.go.kr/portal/bsFileView.do?ep=a5gb/CMEYLclIUPoWw9/DZpAzn2z8@sWTCNA5pR4wDVpzfVJj79Y8WiAGSZ8dpOLr/BD1mimyxS24DCPRsGqxQ!!"
            elif "2" in source_name:
                source_name = "주요 농사기술-2"
                doc_url = "https://www.nongsaro.go.kr/portal/bsFileView.do?ep=a5gb/CMEYLclIUPoWw9/DZpAzn2z8@sWTCNA5pR4wDVpzfVJj79Y8WiAGSZ8dpOLzikZYGMo0Hz8ayNFiXs3DQ!!"
        elif "폭염" in source_name or "폭우" in source_name or "태풍" in source_name:
            source_name = "폭염·폭우·태풍 대비 농작업"
            doc_url = "https://www.nongsaro.go.kr/portal/ps/psv/psvr/psvre/curationDtl.ps?menuId=PS03352&srchCurationNo=1536"
        else:
            # 확장자 제거
            if source_name.endswith('.pdf'):
                source_name = source_name[:-4]
            elif source_name.endswith('.PDF'):
                source_name = source_name[:-4]
            elif source_name.endswith('.txt'):
                source_name = source_name[:-4]
            elif source_name.endswith('.md'):
                source_name = source_name[:-3]
        
        # 페이지 정보와 URL 포함
        if page is not None:
            if doc_url:
                formatted_sources.append(f"{i}. {source_name} (p.{page}) - {doc_url}")
            else:
                formatted_sources.append(f"{i}. {source_name} (p.{page})")
        else:
            if doc_url:
                formatted_sources.append(f"{i}. {source_name} - {doc_url}")
            else:
                formatted_sources.append(f"{i}. {source_name}")
    
    return formatted_sources



