from langchain.prompts import PromptTemplate
from config.user_data import USER_DATA


def create_routing_chain(llm):
    """LLM이 질문 유형을 분석해서 라우팅 결정"""
    routing_template = """
당신은 농업 AI 어시스턴트의 라우터입니다. 사용자 질문을 분석해서 어떤 방식으로 답변할지 결정하세요.

현재 시스템 정보:
- 현재 날짜: 2025년 8월 12일
- 사용자 작물: {crops}
- 토양 정보: pH {ph}, 유기물 {om}g/kg, 유효인산 {vldpha}mg/kg, 칼륨 {posifert_K}cmol+/kg, 칼슘 {posifert_Ca}cmol+/kg, 마그네슘 {posifert_Mg}cmol+/kg, 전기전도도 {selc}dS/m
- 침입자 정보: 최근 사건 {intruder_count}건

**중요**: 다음 조건을 엄격히 적용하세요:

"DIRECT" - 다음에만 해당:
- 현재 날짜 질문
- 키우는 작물 리스트 질문  
- 토양 상태 (pH, 유기물, 영양소) 질문
- 침입자/보안 정보 질문
- 단순 인사말, 감사 표현

"SEARCH" - 다음 모든 경우:
- 병해충, 질병 관련 질문
- 재배 기술, 방법 질문  
- 비료, 영양 관리 방법 질문
- 기상, 날씨 활용법 질문
- 수확, 저장 방법 질문
- 농업 기술 전반 질문
- "어떻게", "방법", "관리", "방제" 등이 포함된 질문

질문: {question}

위 기준에 따라 정확히 DIRECT 또는 SEARCH 중 하나만 답하세요.
결정: """
    
    routing_prompt = PromptTemplate(
        template=routing_template,
        input_variables=[
            "question", "crops", "ph", "om", "vldpha", "posifert_K", "posifert_Ca", "posifert_Mg", "selc", "intruder_count"
        ]
    )
    
    routing_chain = routing_prompt | llm
    return routing_chain


def answer_without_retrieval(question: str, llm) -> str:
    """검색 없이 USER_DATA 정보만으로 답변"""
    current_date = "2025년 8월 12일"
    
    soil = USER_DATA['soil']
    direct_prompt = f"""
너는 농업 전문가야. 아래 사용자 정보를 바탕으로 질문에 답변해줘.

현재 정보:
- 현재 날짜: {current_date}
- 재배 작물: {', '.join(USER_DATA['crop']['current_crops'])}
- 작물별 파종일: {USER_DATA['crop']['planting_date']}
- 작물별 생육단계: {USER_DATA['crop']['growth_stage']}
- 토양 상태: pH {soil['ph']}, 유기물 {soil['om']}g/kg, 유효인산 {soil['vldpha']}mg/kg, 칼륨 {soil['posifert_K']}cmol+/kg, 칼슘 {soil['posifert_Ca']}cmol+/kg, 마그네슘 {soil['posifert_Mg']}cmol+/kg, 전기전도도 {soil['selc']}dS/m
- 최근 침입자 사건: {len(USER_DATA['intruder']['recent_incidents'])}건

질문: {question}

친근하고 전문적으로 답변해줘. 만약 질문이 농업과 관련이 없다면 정중하게 농업 관련 질문을 요청해줘.
"""
    
    try:
        response = llm.invoke(direct_prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
