from langchain.prompts import PromptTemplate
from config.user_data import USER_DATA
from services.soil_fertilizer_cache import fertilizer_cache


def create_routing_chain(llm):
    """LLM이 질문 유형을 분석해서 라우팅 결정"""
    routing_template = (
"""
농업 AI 어시스턴트의 질문 분류기입니다. 다음 질문을 'SEARCH' 또는 'DIRECT' 중 하나로 분류하세요.

분류 기준:

'SEARCH' - 농업 전문 지식/기술이 필요한 질문:
- 병해충 진단, 방제법, 증상 설명
- 작물별 재배 기술, 재배 매뉴얼, 품종 특성
- 농작업 가이드, 시기별 작업, 농업 기법
- 폭염/가뭄/장마 등 기상 대응법
- 일반적인 비료 시비법, 농업 기준
- "어떻게", "방법", "기술", "매뉴얼" 관련 질문

'DIRECT' - 개인 농장 데이터 관련 질문:
- "우리 농장", "내 농장" 토양/면적/작물 정보
- 개인 맞춤 비료 추천 요청
- 현재 날씨, 침입자 감지 현황
- 구체적 수치 계산, 데이터 조회

질문 예시:
"폭염일 때 농사에서 가장 중요한 부분이 뭘까요" → SEARCH
"고추 비료 추천 내역 뽑아주세요" → DIRECT

중요: 반드시 'SEARCH' 또는 'DIRECT' 한 단어만 출력하세요.

질문: {question}
응답:"""
    )

    routing_prompt = PromptTemplate(
        template=routing_template,
        input_variables=["question"],
    )

    routing_chain = routing_prompt | llm
    return routing_chain


def answer_without_retrieval(question: str, llm) -> str:
    """검색 없이 USER_DATA 정보만으로 답변"""
    from services.intruder_cache import get_intruder_context
    
    try:
        intruder_info = get_intruder_context()
        
        # 안전한 데이터 포맷팅
        user_data_str = str(USER_DATA) if USER_DATA else "없음"
        fert_cache_str = str(fertilizer_cache) if fertilizer_cache else "없음"
        intruder_info_str = str(intruder_info) if intruder_info else "없음"
        
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
  - 표 컬럼: 단계 | 비료명 | N-P2O5-K2O | 사용량(kg) | 포대수 | 부족 P(kg) | 부족 K(kg)
  - 퇴비가 포함되면 별도 표로: 종류 | kg (계분/우분/돈분/혼합)
- 침입자/보안 질문에는 감지 현황을 간단히 요약해서 답변한다.

데이터 사용 규칙:
- 아래 컨텍스트는 참조용이며 그대로 출력하지 않는다(원문, 전체 덤프 금지).
- 사용자가 명시적으로 물은 항목만 숫자 1~2개로 언급한다.
- 비료 추천/처방 요청인데 필수 정보(작물명/면적)가 없으면 해당 항목만 물어보고, 임의의 추천은 하지 않는다.
- 단위는 필요 시 a(아르)와 kg로 간단히 표기한다.

컨텍스트(출력 금지):
- USER_DATA: {user_data_str}
- FERT_CACHE: {fert_cache_str}
- INTRUDER_INFO: {intruder_info_str}

질문: {question}
"""
        
    except Exception as e:
        # 데이터 로드 실패 시 단순 프롬프트
        direct_prompt = f"""
너는 농업 전문가다. 다음 질문에 간단히 답변하라:

질문: {question}

답변:
"""
    
    try:
        response = llm.invoke(direct_prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
