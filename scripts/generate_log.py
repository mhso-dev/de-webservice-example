#!/usr/bin/env python3
import json
import random
import string
import os
import uuid
from datetime import datetime, timedelta
import argparse
import ipaddress

# 명령행 인자 파싱
parser = argparse.ArgumentParser(description='가상 로그 생성기')
parser.add_argument('--count', type=int, default=100000, help='생성할 로그 수 (기본값: 100000)')
parser.add_argument('--output-dir', type=str, default='../logs', help='로그 파일 저장 경로')
parser.add_argument('--start-date', type=str, default='2025-03-10', help='시작 날짜 (YYYY-MM-DD)')
parser.add_argument('--end-date', type=str, default='2025-03-17', help='종료 날짜 (YYYY-MM-DD)')
args = parser.parse_args()

# 기본 설정
log_count = args.count
output_dir = args.output_dir
start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

# 경로 생성
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 제품 데이터 샘플
products = []
for i in range(1, 101):
    category = random.choice([1, 2, 3, 4, 5])
    products.append({
        'id': i,
        'name': f'Product {i}',
        'category': category,
        'price': round(random.uniform(10.0, 1000.0), 2)
    })

# 사용자 데이터 샘플
users = []
for i in range(1, 101):
    users.append({
        'id': i,
        'email': f'user{i}@example.com',
        'name': f'User {i}'
    })

# IP 주소 생성 함수
def generate_ip():
    # 국내 IP 대역 중 일부 사용
    networks = [
        '211.234.0.0/16',  # SKT
        '1.224.0.0/16',    # KT
        '39.7.0.0/16',     # LG U+
        '121.190.0.0/16',  # Local ISPs
        '125.188.0.0/16'   # Home networks
    ]
    
    network = random.choice(networks)
    net = ipaddress.IPv4Network(network)
    # 네트워크 내 랜덤 IP 생성
    random_ip = net.network_address + random.randint(0, min(65535, net.num_addresses - 1))
    return str(random_ip)

# 세션 ID 생성 함수
def generate_session_id():
    return uuid.uuid4().hex[:32]

# 사용자 에이전트 샘플
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    "Unknown"
]

# 경로 샘플
paths = [
    "/",
    "/products",
    "/products?category=1",
    "/products?category=2",
    "/products?category=3",
    "/products?category=4",
    "/products?category=5",
    "/search?q=smartphone",
    "/search?q=laptop",
    "/search?q=headphones",
    "/search?q=camera",
    "/cart",
    "/checkout",
    "/login",
    "/register",
    "/profile",
    "/orders"
]

# 특정 제품 경로
def product_path(product_id):
    return f"/products/{product_id}"

# 검색어 샘플
search_queries = [
    "스마트폰", "노트북", "헤드폰", "카메라", "TV", "태블릿", "게임기", "스피커", 
    "키보드", "마우스", "모니터", "프린터", "이어폰", "충전기", "케이블", "스마트워치",
    "블루투스", "무선", "삼성", "애플", "LG", "소니", "게이밍", "방수", "초고속", "초경량"
]

# 엔드포인트 매핑
endpoint_mapping = {
    "/": "main.index",
    "/products": "products.list",
    "/cart": "cart.view",
    "/checkout": "orders.checkout",
    "/login": "auth.login",
    "/register": "auth.register",
    "/profile": "users.profile",
    "/orders": "orders.list",
    "/search": "main.search"
}

# 카테고리별 제품 그룹화
products_by_category = {}
for product in products:
    cat_id = product['category']
    if cat_id not in products_by_category:
        products_by_category[cat_id] = []
    products_by_category[cat_id].append(product)

# 날짜별 로그 생성
active_sessions = {}  # 현재 활성 세션 추적
system_logs = []
user_activity_logs = []

# 날짜 범위 계산
date_range = (end_date - start_date).days + 1
logs_per_day = log_count // date_range

print(f"생성 시작: {log_count}개 로그를 {date_range}일에 걸쳐 생성 ({logs_per_day}개/일)")

for day_offset in range(date_range):
    current_date = start_date + timedelta(days=day_offset)
    date_str = current_date.strftime('%Y-%m-%d')
    
    print(f"날짜 {date_str} 로그 생성 중...")
    
    # 이 날짜의 시스템 로그
    system_log_file = f"{output_dir}/app-{date_str}.log"
    user_log_file = f"{output_dir}/user_activity-{date_str}.log"
    
    # 세션 관리 - 이전 날짜의 세션 일부는 유지, 일부는 제거, 새 세션 추가
    old_sessions = list(active_sessions.keys())
    
    # 75%의 이전 세션 제거
    for old_session in random.sample(old_sessions, int(len(old_sessions) * 0.75)):
        del active_sessions[old_session]
    
    # 새 세션 100개 추가
    for _ in range(100):
        session_id = generate_session_id()
        user = random.choice([None] + [u['id'] for u in users])  # 로그인 유무
        ip = generate_ip()
        ua = random.choice(user_agents)
        active_sessions[session_id] = {
            'user_id': user,
            'ip': ip,
            'user_agent': ua,
            'last_path': None
        }
    
    daily_logs_count = 0
    daily_system_logs = []
    daily_user_logs = []
    
    # 시스템 시작 로그
    start_time = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    system_start_log = {
        "timestamp": start_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
        "level": "INFO",
        "message": "웹 서비스 시작 - 날짜별 로깅 설정 완료",
        "module": "daily_logger"
    }
    daily_system_logs.append(json.dumps(system_start_log, ensure_ascii=False))
    
    # 이 날짜의 로그 생성
    while daily_logs_count < logs_per_day:
        # 로그 시간 - 0시부터 23시 59분까지
        log_time = current_date + timedelta(
            seconds=random.randint(0, 86399),
            microseconds=random.randint(0, 999999)
        )
        timestamp = log_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        
        # 50% 확률로 시스템 로그 또는 사용자 활동 로그 생성
        if random.random() < 0.3:  # 30% 시스템 로그
            log_level = random.choices(
                ["INFO", "WARNING", "ERROR", "DEBUG"],
                weights=[0.7, 0.15, 0.1, 0.05],
                k=1
            )[0]
            
            # 로그 레벨별 메시지 선택
            if log_level == "INFO":
                messages = [
                    "요청 처리 완료",
                    f"요청 종료: GET {random.choice(paths)} - {random.choice([200, 302, 304])}",
                    "데이터베이스 연결 성공",
                    "캐시 새로고침 완료",
                    f"사용자 {random.randint(1, 100)} 세션 생성",
                    "정적 자산 로드 완료"
                ]
                module = random.choice(["__init__", "routes", "models", "views", "utils"])
            elif log_level == "WARNING":
                messages = [
                    "데이터베이스 응답 지연",
                    "캐시 적중률 감소",
                    "세션 수 임계값 접근",
                    "API 응답 시간 지연",
                    "디스크 공간 부족 경고",
                    "메모리 사용량 증가"
                ]
                module = random.choice(["database", "cache", "session", "api", "system"])
            elif log_level == "ERROR":
                messages = [
                    "데이터베이스 연결 실패",
                    f"예상치 못한 예외 발생: {random.choice(['TypeError', 'ValueError', 'KeyError', 'IndexError'])}",
                    f"API 요청 실패: 상태 코드 {random.choice([400, 403, 404, 500, 503])}",
                    "파일 업로드 처리 중 오류",
                    "결제 프로세스 실패",
                    "템플릿 렌더링 오류"
                ]
                module = random.choice(["database", "api", "uploads", "payment", "templates"])
            else:  # DEBUG
                messages = [
                    "SQL 쿼리 실행: SELECT * FROM products LIMIT 10",
                    "캐시 키 생성: product_1234",
                    "세션 데이터 업데이트",
                    "폼 검증 시작",
                    "미들웨어 처리 중",
                    "환경 변수 로드 완료"
                ]
                module = random.choice(["database", "cache", "session", "forms", "middleware", "config"])
            
            system_log = {
                "timestamp": timestamp,
                "level": log_level,
                "message": random.choice(messages),
                "module": module
            }
            daily_system_logs.append(json.dumps(system_log, ensure_ascii=False))
        
        else:  # 70% 사용자 활동 로그
            # 세션 선택 (또는 세션이 없는 요청)
            if random.random() < 0.05:  # 5%는 세션 없는 요청
                session_id = "no_session"
                user_id = None
                ip = generate_ip()
                user_agent = random.choice(user_agents)
            else:
                session_id = random.choice(list(active_sessions.keys()))
                session_info = active_sessions[session_id]
                user_id = session_info['user_id']
                ip = session_info['ip']
                user_agent = session_info['user_agent']
                last_path = session_info['last_path']
            
            # 이벤트 유형 선택
            event_weights = {
                "page_view": 0.3,
                "view": 0.25,
                "search": 0.15,
                "login_attempt": 0.05,
                "login_success": 0.05,
                "login_failed": 0.02,
                "cart_add": 0.08,
                "server_dwell_time": 0.1
            }
            
            event_type = random.choices(
                list(event_weights.keys()),
                weights=list(event_weights.values()),
                k=1
            )[0]
            
            # 기본 로그 필드
            log_data = {
                "timestamp": timestamp,
                "session_id": session_id,
                "event_type": event_type,
                "user_id": user_id,
                "ip_address": ip,
                "user_agent": user_agent
            }
            
            # 이벤트별 특수 필드 추가
            if event_type == "page_view":
                path = random.choice(paths)
                log_data.update({
                    "entity_type": None,
                    "entity_id": None,
                    "endpoint": endpoint_mapping.get(path.split('?')[0], None),
                    "method": "GET",
                    "path": path,
                    "args": {},
                    "form": {},
                    "referrer": None,
                    "response_status": random.choice([200, 302, 304]),
                    "process_time": round(random.uniform(0.001, 0.5), 6)
                })
                
                # 카테고리 페이지인 경우
                if "category=" in path:
                    cat_id = int(path.split("category=")[1])
                    log_data["entity_type"] = "category"
                    log_data["entity_id"] = cat_id
                    
                # 쿼리 파라미터 파싱
                if "?" in path:
                    query_part = path.split("?")[1]
                    args = {}
                    for param in query_part.split("&"):
                        if "=" in param:
                            key, value = param.split("=")
                            args[key] = value
                    log_data["args"] = args
                
                # 세션 업데이트
                if session_id in active_sessions:
                    active_sessions[session_id]['last_path'] = path
            
            elif event_type == "view":
                product = random.choice(products)
                path = product_path(product['id'])
                log_data.update({
                    "entity_type": "product",
                    "entity_id": product['id'],
                    "endpoint": "products.detail",
                    "method": "GET",
                    "path": path,
                    "args": {},
                    "form": {},
                    "referrer": active_sessions.get(session_id, {}).get('last_path'),
                    "response_status": 200,
                    "process_time": round(random.uniform(0.01, 0.2), 6)
                })
                
                # 세션 업데이트
                if session_id in active_sessions:
                    active_sessions[session_id]['last_path'] = path
            
            elif event_type == "search":
                query = random.choice(search_queries)
                path = f"/search?q={query}"
                results_count = random.randint(0, 20)
                
                log_data.update({
                    "entity_type": None,
                    "entity_id": None,
                    "endpoint": "main.search",
                    "method": "GET",
                    "path": path,
                    "args": {"q": query},
                    "form": {},
                    "referrer": active_sessions.get(session_id, {}).get('last_path'),
                    "search_query": query,
                    "results_count": results_count,
                    "response_status": 200,
                    "process_time": round(random.uniform(0.05, 0.5), 6)
                })
                
                # 세션 업데이트
                if session_id in active_sessions:
                    active_sessions[session_id]['last_path'] = path
            
            elif event_type == "login_attempt":
                username = random.choice([f"user{random.randint(1, 100)}@example.com", "admin@example.com"])
                log_data.update({
                    "user_id": None,
                    "endpoint": "auth.login",
                    "method": "POST",
                    "path": "/auth/login",
                    "form": {"email": username, "password": "******"},
                    "username_attempt": username,
                    "response_status": 200
                })
            
            elif event_type == "login_failed":
                username = random.choice([f"user{random.randint(1, 100)}@example.com", "admin@example.com"])
                reason = random.choice(["invalid_credentials", "account_locked", "inactive_account"])
                log_data.update({
                    "username_attempt": username,
                    "reason": reason
                })
            
            elif event_type == "login_success":
                # 로그인 성공 시 사용자 ID 설정
                user_id = random.randint(1, 100)
                log_data.update({
                    "user_id": user_id,
                    "endpoint": "auth.login",
                    "method": "POST",
                    "path": "/auth/login",
                    "response_status": 200
                })
                
                # 세션 업데이트
                if session_id in active_sessions:
                    active_sessions[session_id]['user_id'] = user_id
                    active_sessions[session_id]['last_path'] = "/auth/login"
            
            elif event_type == "cart_add":
                product = random.choice(products)
                quantity = random.randint(1, 5)
                
                log_data.update({
                    "entity_type": "product",
                    "entity_id": product['id'],
                    "endpoint": "cart.add",
                    "method": "POST",
                    "path": "/cart/add",
                    "form": {"product_id": str(product['id']), "quantity": str(quantity)},
                    "referrer": product_path(product['id']),
                    "response_status": 302,
                    "process_time": round(random.uniform(0.01, 0.1), 6)
                })
            
            elif event_type == "server_dwell_time":
                current_path = random.choice(paths)
                previous_path = active_sessions.get(session_id, {}).get('last_path', "/")
                dwell_time = round(random.uniform(1, 600), 6)  # 1초~10분
                
                product_id = None
                if "/products/" in current_path and len(current_path.split("/")) > 2:
                    try:
                        product_id = int(current_path.split("/")[2])
                    except:
                        pass
                
                log_data.update({
                    "product_id": product_id,
                    "previous_path": previous_path,
                    "current_path": current_path,
                    "dwell_time_seconds": dwell_time,
                    "max_scroll_percentage": random.randint(0, 100)
                })
            
            daily_user_logs.append(json.dumps(log_data, ensure_ascii=False))
        
        daily_logs_count += 1
    
    # 시스템 종료 로그
    end_time = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    page_view_count = sum(1 for l in daily_user_logs if '"event_type": "page_view"' in l)
    search_count = sum(1 for l in daily_user_logs if '"event_type": "search"' in l)
    login_count = sum(1 for l in daily_user_logs if '"event_type": "login_success"' in l)

    system_end_log = {
        "timestamp": end_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
        "level": "INFO",
        "message": f"웹 서비스 일일 활동 요약: 페이지뷰 {page_view_count}, 검색 {search_count}, 로그인 {login_count}",
        "module": "stats"
    }
    daily_system_logs.append(json.dumps(system_end_log, ensure_ascii=False))
    
    # 파일에 저장
    with open(system_log_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(daily_system_logs))
    
    with open(user_log_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(daily_user_logs))
    
    print(f"  - 시스템 로그: {len(daily_system_logs)}개")
    print(f"  - 사용자 활동 로그: {len(daily_user_logs)}개")
    print(f"  - 총 {len(daily_system_logs) + len(daily_user_logs)}개 로그 생성 완료")

print(f"\n총 {log_count}개 로그 생성 완료. 출력 디렉토리: {output_dir}") 
