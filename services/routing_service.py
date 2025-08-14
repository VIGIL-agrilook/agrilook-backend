from langchain.prompts import PromptTemplate
from config.user_data import USER_DATA


def create_routing_chain(llm):
    """LLM이 질문 유형을 분석해서 라우팅 결정"""
    routing_template = f"""
당신은 농업 AI 어시스턴트의 라우터입니다. 사용자 질문을 분석해서 어떤 방식으로 답변할지 결정하세요.

현재 시스템 정보:

**중요**: 다음 조건을 엄격히 적용하세요:

"DIRECT" - 다음에만 해당:

"SEARCH" - 다음 모든 경우:

위 기준에 따라 정확히 DIRECT 또는 SEARCH 중 하나만 답하세요.
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

질문: {question}

친근하고 전문적으로 답변해줘. 농업 면적이나 비료량 관련 답변 시 반드시 a(아르) 단위를 사용하고, 실용적인 포대수나 kg 단위도 함께 제공해줘. 만약 질문이 농업과 관련이 없다면 정중하게 농업 관련 질문을 요청해줘.
"""
    
    try:
        response = llm.invoke(direct_prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
