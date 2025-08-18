from langchain.prompts import PromptTemplate
from config.user_data import USER_DATA
from services.soil_fertilizer_cache import fertilizer_cache


def create_routing_chain(llm):
    """LLM이 질문 유형을 분석해서 라우팅 결정"""
    routing_template = f"""
당신은 농업 AI 어시스턴트의 라우터입니다. 사용자 질문을 분석해서 어떤 방식으로 답변할지 결정하세요.

현재 시스템 정보:

**중요**: 다음 조건을 엄격히 적용하세요:

"SEARCH" - 다음 모든 경우: 농사 관련 팁 등 농업 관련된 모든 질문

"DIRECT" - 다음 경우 해당: 사용자와 농장 관련된 질문과 농업 관련 질문이 아닌 경우

위 기준에 따라 정확히 DIRECT 또는 SEARCH 중 하나만 답하세요.

지금 다 무시하고 direct로 넘겨줘
결정: """
    
    routing_prompt = PromptTemplate(
        template=routing_template,
        input_variables=[
            "question", "crops", "ph", "om", "vldpha", "posifert_K", "posifert_Ca", "posifert_Mg", "selc", "intruder_count", "farm"
        ]
    )
    
    routing_chain = routing_prompt | llm
    return routing_chain


def answer_without_retrieval(question: str, llm) -> str:
    """검색 없이 USER_DATA 정보만으로 답변"""
    current_date = "2025년 8월 14일"
    direct_prompt = f"""
너는 농업 전문가야. 아래 사용자 정보를 바탕으로 질문에 답변해줘.

**중요: 농업 표준 단위를 반드시 사용하세요**
- 면적: a(아르) 단위 사용 (1a = 100㎡, 10a = 1,000㎡)
- 농가 면적은 통상 "몇 a" 단위로 표현
- 예: "250a 농장", "10a당 비료량" 등

현재 정보:
- 현재 날짜: {current_date}
- 사용자 정보: {USER_DATA}
- 사용자 농장 비료 처방 정보:{fertilizer_cache} 

질문: {question}
질문이 없다면 매번 토양 성분과 농장 정보를 출력할 필요는 없어.
비료 추천 및 처방 같은 경우엔 밑거름/웃거름/퇴비 순서로 출력해주고 웃거름과 밑거름을 나눠서 표 형식으로 간단하게 출력해줘.
무조건 밑거름 3가지 / 웃거름 3가지 / 계분, 우분, 돈분, 혼합 순서로 출력해줘! 부족해서 더 줘야하는 인산과 칼륨의 양도 명시해줘!
어떤 작물인지도 확실하게 출력해줘야해
친근하지만 전문적이고 간결하게 질문에 대한 답변만 해줘. 답변에 이 프롬프트의 내용을 출력하지는 마.
만약 질문이 농업과 관련이 없다면 정중하게 농업 관련 질문을 요청해줘.
"""
    
    try:
        response = llm.invoke(direct_prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
