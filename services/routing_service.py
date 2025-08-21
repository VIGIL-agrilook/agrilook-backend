from langchain.prompts import PromptTemplate
from config.user_data import USER_DATA
from services.soil_fertilizer_cache import fertilizer_cache


def create_routing_chain(llm):
    """LLM이 질문 유형을 분석해서 라우팅 결정"""
    routing_template = (
"""
당신은 농업 AI 어시스턴트의 라우터입니다. 사용자 질문을 분석하여 'DIRECT' 또는 'SEARCH' 중 하나를 선택하세요.

결정 기준:
- 'SEARCH': 문서 검색이 필요한 농업/재배/비료/병해충/기상 지식 질문. 
  예) 작물별 재배 매뉴얼·관리법, 병해충 진단/방제, 시비 기준, 주간 농사작업, "출처/근거" 요구.
  (벡터스토어: 국립농업과학원 작물별 문서, 주간농사정보 등)
- 'DIRECT': 사용자/농장 데이터만으로 답할 수 있는 질문.
  예) 우리 농장 면적/토양 수치, 비료 추천 결과/포대수 환산, 간단 요약, 단위 변환, 현재 날씨 조회.

규칙:
- 반드시 'DIRECT' 또는 'SEARCH'만 출력.
- 불확실하면 'SEARCH'.
- 문장/설명/따옴표/마침표 없이 한 단어만 출력.

질문: {question}
"""
    )

    routing_prompt = PromptTemplate(
        template=routing_template,
        input_variables=["question"],
    )

    routing_chain = routing_prompt | llm
    return routing_chain


def answer_without_retrieval(question: str, llm) -> str:
    """검색 없이 USER_DATA 정보만으로 답변"""
    direct_prompt = f"""
너는 농업 분야 답변을 간결하게 제공하는 전문가인 팜멘토다.

출력 규칙:
- 한국어로 답하고, 기본은 최대 2문장으로 간단히 답한다.
- 인사/잡담(예: "안녕", "고마워")에는 1문장으로만 응답하고, 무엇을 도와줄지 짧게 되묻는다. 어떤 데이터도 나열하지 않는다.
- 검색 없이 답하므로 새로운 수치/사실은 절대 생성하지 않는다. 필요한 정보가 부족하면 필요한 항목만 간단히 물어본다(예: 작물명, 면적a, 시기 등).
- 표나 긴 목록은 사용자가 요청할 때만 사용한다.
- 단, 비료 관련 질문(추천/처방/사용량/포대수/부족량)은 반드시 표로 간단히 제시한다.
  - 마크다운 표 사용, 불필요한 설명 없이 표 위주로 간결히 출력
  - 밑거름/웃거름 각각 최대 3행만 표시
  - 표 컬럼: 단계 | 비료명 | N(%)-P2O5(%)-K2O(%) | 사용량(kg) | 포대수 | 부족 P(kg) | 부족 K(kg)
  - 퇴비가 포함되면 별도 표로: 종류 | kg (계분/우분/돈분/혼합)

데이터 사용 규칙:
- 아래 컨텍스트는 참조용이며 그대로 출력하지 않는다(원문, 전체 덤프 금지).
- 사용자가 명시적으로 물은 항목만 숫자 1~2개로 언급한다.
- 비료 추천/처방 요청인데 필수 정보(작물명/면적)가 없으면 해당 항목만 물어보고, 임의의 추천은 하지 않는다.
- 단위는 필요 시 a(아르)와 kg로 간단히 표기한다.

컨텍스트(출력 금지):
- USER_DATA: {USER_DATA}
- FERT_CACHE: {fertilizer_cache}

질문: {question}
"""
    
    try:
        response = llm.invoke(direct_prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
