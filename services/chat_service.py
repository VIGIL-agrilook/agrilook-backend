"""
채팅 서비스 엔드포인트
챗봇 관련 기능들을 분리
"""
from flask import Blueprint, request, jsonify
from langchain_openai import ChatOpenAI
import os

from config.user_data import USER_DATA
from services.routing_service import create_routing_chain, answer_without_retrieval
from services.qa_service import load_qa_chain, format_source_documents

chat_bp = Blueprint('chat', __name__)

# 전역 변수로 체인들 저장
qa_chain = None
routing_chain = None


def initialize_chains():
    """채팅 체인들 초기화"""
    global qa_chain, routing_chain
    
    # LLM 초기화
    base_url = os.getenv("BASE_URL")
    adotx_api_key = os.getenv("ADOTX_API_KEY")
    
    llm = ChatOpenAI(
        model="ax4",
        base_url=base_url,
        api_key=adotx_api_key
    )
    
    # QA 체인 로드
    qa_chain = load_qa_chain()
    
    # 라우팅 체인 생성
    routing_chain = create_routing_chain(llm)


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """채팅 엔드포인트"""
    global qa_chain, routing_chain
    
    try:
        # 체인이 초기화되지 않았으면 초기화
        if qa_chain is None or routing_chain is None:
            initialize_chains()
            
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "status": "error",
                "message": "메시지가 필요합니다."
            }), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({
                "status": "error", 
                "message": "빈 메시지는 처리할 수 없습니다."
            }), 400
        
        # 라우팅 결정
        routing_input = {
            "question": user_message,
            "crops": ", ".join(USER_DATA['crop']['current_crops']),
            "ph": USER_DATA['soil']['ph'],
            "om": USER_DATA['soil']['om'],                          # 유기물
            "vldpha": USER_DATA['soil']['vldpha'],                  # 유효인산
            "posifert_K": USER_DATA['soil']['posifert_K'],          # 칼륨
            "posifert_Ca": USER_DATA['soil']['posifert_Ca'],        # 칼슘
            "posifert_Mg": USER_DATA['soil']['posifert_Mg'],        # 마그네슘
            "selc": USER_DATA['soil']['selc'],                      # 전기전도도
            "intruder_count": len(USER_DATA['intruder']['recent_incidents'])
        }
        
        routing_result = routing_chain.invoke(routing_input)
        decision = routing_result.content if hasattr(routing_result, 'content') else str(routing_result)
        
        # 답변 생성
        if "DIRECT" in decision.upper():
            # 검색 없이 직접 답변
            base_url = os.getenv("BASE_URL")
            adotx_api_key = os.getenv("ADOTX_API_KEY")
            
            llm = ChatOpenAI(
                model="ax4",
                base_url=base_url,
                api_key=adotx_api_key
            )
            
            answer = answer_without_retrieval(user_message, llm)
            
            return jsonify({
                "status": "success",
                "answer": answer,
                "routing": "DIRECT",
                "sources": []
            })
            
        else:
            # 검색 기반 답변
            result = qa_chain.invoke({"query": user_message})
            answer = result["result"]
            sources = format_source_documents(result["source_documents"])
            
            return jsonify({
                "status": "success", 
                "answer": answer,
                "routing": "SEARCH",
                "sources": sources
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"처리 중 오류가 발생했습니다: {str(e)}"
        }), 500
