import os
import json
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from flask import Flask, request, g, session, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
import pymysql
from dotenv import load_dotenv
import uuid
from app.utils.daily_logger import setup_logger  # 새 로깅 모듈 import

# .env 파일 로드
load_dotenv()

# SQLAlchemy 객체 생성
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='../templates')
    
    # 설정 로드
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '../static/uploads')
    
    # 인스턴스 초기화
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # 로깅 설정
    # 날짜별 로깅 설정 적용
    setup_logger(app)
    
    # 블루프린트 등록
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.products import products_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 요청 처리 전에 실행되는 함수
    @app.before_request
    def before_request():
        g.user = None
        if 'user_id' in session:
            from app.models.user import User
            g.user = User.query.get(session['user_id'])
        
        # 요청 고유 ID 생성
        g.request_id = str(uuid.uuid4())
        
        # 모든 요청에서 카테고리 목록 가져오기
        # 내비게이션 메뉴에서 사용하기 위함
        if not request.path.startswith('/static'):
            from app.models import Category
            g.all_categories = Category.query.all()
        
        # 시작 시간 기록
        g.request_start_time = datetime.now()
        
        # 세션 ID 관리
        if 'session_id' not in session:
            session['session_id'] = os.urandom(16).hex()
        g.session_id = session['session_id']
        
        # 요청 시작 로그
        if not request.path.startswith('/static'):
            app.logger.info(f"요청 시작: {request.method} {request.path}", 
                           extra={"data": {"request_params": {
                               "args": dict(request.args),
                               "form": {k: v for k, v in request.form.items() if k.lower() not in ['password', 'token']}
                           }}})
    
    # 요청 처리 후에 실행되는 함수
    @app.after_request
    def after_request(response):
        from flask_login import current_user
        
        # 정적 파일은 로깅 제외
        if request.path.startswith('/static'):
            return response
        
        # 이전 페이지 체류 시간 계산 및 로깅
        current_time = datetime.now()
        current_path = request.path
        
        # 페이지 및 API 호출 타임스탬프 기록 (JavaScript 호출이 없는 페이지를 위한 백업)
        if not current_path.startswith('/api/log/'):  # 로깅 API 자체는 제외
            # 이전 페이지 경로와 시간이 세션에 있으면 체류 시간 계산
            if 'last_page' in session and 'last_page_time' in session:
                last_path = session.get('last_page')
                last_time_str = session.get('last_page_time')
                
                try:
                    last_time = datetime.fromisoformat(last_time_str)
                    dwell_time_seconds = (current_time - last_time).total_seconds()
                    
                    # 유효한 체류 시간인 경우에만 로깅 (1초부터 30분까지)
                    if 1 <= dwell_time_seconds <= 1800:
                        # 이전 페이지가 제품 상세 페이지인 경우 특별히 처리
                        product_id = None
                        path_parts = last_path.split('/')
                        if '/products/' in last_path and len(path_parts) > 2:
                            try:
                                product_id = int(path_parts[-1])
                            except ValueError:
                                pass
                        
                        # 체류 시간 로그 데이터 구성
                        log_data = {
                            'timestamp': current_time.isoformat(),
                            'event_type': 'server_dwell_time',
                            'user_id': current_user.id if current_user.is_authenticated else None,
                            'session_id': g.session_id if hasattr(g, 'session_id') else None,
                            'product_id': product_id,
                            'previous_path': last_path,
                            'current_path': current_path,
                            'dwell_time_seconds': dwell_time_seconds,
                            'user_agent': request.user_agent.string if request.user_agent else "Unknown",
                            'ip_address': request.remote_addr
                        }
                        
                        # 로깅
                        activity_logger = logging.getLogger('user_activity')
                        activity_logger.info(json.dumps(log_data))
                        
                        # DB에 저장 (필요한 경우)
                        if product_id:
                            from app.models.log import UserActivityLog
                            try:
                                log_entry = UserActivityLog(
                                    user_id=current_user.id if current_user.is_authenticated else None,
                                    session_id=g.session_id if hasattr(g, 'session_id') else None,
                                    activity_type='page_dwell',
                                    entity_type='product',
                                    entity_id=product_id,
                                    details=json.dumps(log_data),
                                    ip_address=request.remote_addr,
                                    user_agent=request.user_agent.string if request.user_agent else "Unknown"
                                )
                                db.session.add(log_entry)
                                db.session.commit()
                            except Exception as e:
                                db.session.rollback()
                                app.logger.error(f"체류 시간 DB 저장 오류: {str(e)}")
                except Exception as e:
                    app.logger.error(f"체류 시간 계산 오류: {str(e)}")
            
            # 현재 페이지 정보 세션에 저장 (다음 요청에서 체류 시간 계산용)
            session['last_page'] = current_path
            session['last_page_time'] = current_time.isoformat()
        
        # 모든 웹 요청에 대해 activity 로그 기록 (정적 파일 제외)
        log_activity(request, response)
        
        # 요청 처리 결과 로깅
        processing_time = (datetime.now() - g.request_start_time).total_seconds() * 1000
        log_data = {
            "data": {
                "response": {
                    "status_code": response.status_code,
                    "content_type": response.content_type,
                    "content_length": len(response.get_data()) if response.get_data() else 0
                },
                "performance": {
                    "processing_time_ms": processing_time
                }
            }
        }
        
        # 로그 레벨 결정 (에러는 ERROR, 그 외는 INFO)
        if 400 <= response.status_code < 600:
            app.logger.error(f"요청 종료: {request.method} {request.path} - {response.status_code}", extra=log_data)
        else:
            app.logger.info(f"요청 종료: {request.method} {request.path} - {response.status_code}", extra=log_data)
        
        return response
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    return app

def setup_logging(app):
    log_dir = os.getenv('LOG_PATH', '../logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # JSON 형식 포맷터 정의
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "path": record.pathname
            }
            
            # 예외 정보 추가
            if record.exc_info:
                log_record["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": self.formatException(record.exc_info)
                }
            
            # 요청 정보 추가 - 애플리케이션 컨텍스트 내에서만 실행
            try:
                from flask import g, request, current_app, has_request_context
                from flask_login import current_user
                
                if has_request_context():
                    if hasattr(g, 'request_id'):
                        log_record["request_id"] = g.request_id
                    
                    if hasattr(g, 'user') and g.user:
                        log_record["user_id"] = g.user.id
                        
                    if hasattr(current_user, 'id') and current_user.is_authenticated:
                        log_record["auth_user_id"] = current_user.id
                    
                    # HTTP 요청 정보가 있는 경우 추가
                    try:
                        log_record["http"] = {
                            "method": request.method,
                            "url": request.url,
                            "path": request.path,
                            "endpoint": request.endpoint,
                            "ip": request.remote_addr,
                            "user_agent": request.user_agent.string if request.user_agent else None,
                            "referrer": request.referrer
                        }
                    except:
                        # request 객체가 없는 경우 예외 발생
                        pass
                    
                    # 성능 정보 추가
                    if hasattr(g, 'request_start_time'):
                        processing_time = (datetime.now() - g.request_start_time).total_seconds()
                        log_record["performance"] = {
                            "processing_time_ms": processing_time
                        }
            except:
                # 애플리케이션 컨텍스트 외부에서 실행 시 예외 처리
                pass
            
            # 추가 속성이 있으면 로그에 포함
            if hasattr(record, 'data') and record.data:
                log_record.update(record.data)
                
            return json.dumps(log_record)
    
    # 일반 로그 설정 - JSON 포맷
    app_log_file = os.path.join(log_dir, 'app.log')
    app_handler = TimedRotatingFileHandler(
        app_log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # 30일 보관
        encoding='utf-8'
    )
    app_handler.suffix = '%Y-%m-%d'  # 날짜 접미사 형식 설정
    app_handler.setFormatter(JsonFormatter())
    app_handler.setLevel(logging.INFO)
    app.logger.addHandler(app_handler)
    
    # 사용자 활동 로그 설정 - 날짜별 로테이션
    activity_log_file = os.path.join(log_dir, 'user_activity.log')
    activity_handler = TimedRotatingFileHandler(
        activity_log_file,
        when='midnight',        # 자정에 로그 파일 전환
        interval=1,             # 1일 간격
        backupCount=30,         # 30일치 로그 보관
        encoding='utf-8'
    )
    activity_handler.suffix = '%Y-%m-%d'  # 날짜 접미사 형식 설정
    activity_handler.setFormatter(logging.Formatter('%(message)s'))
    
    activity_logger = logging.getLogger('user_activity')
    activity_logger.setLevel(logging.INFO)
    activity_logger.addHandler(activity_handler)
    
    app.logger.setLevel(logging.INFO)
    
    # 애플리케이션 시작 로그 - 애플리케이션 컨텍스트 문제 방지
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "event": "app_start",
        "message": "애플리케이션 시작"
    }
    
    # 애플리케이션 시작 로그 - 일반 로거 사용
    print(f"애플리케이션 시작 - 로깅 테스트")
    activity_logger.info(json.dumps(log_data))
    print(f"테스트 로그 작성 시도: {json.dumps(log_data)}")
    
    # 콘솔 로그 추가 (개발 시 편리함)
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JsonFormatter())
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
        activity_logger.addHandler(console_handler)

def log_activity(request, response=None):
    """사용자 활동을 JSON 형식으로 로깅"""
    from app.models.log import UserActivityLog
    import traceback
    from flask_login import current_user
    
    try:
        # 로거 가져오기
        activity_logger = logging.getLogger('user_activity')
        
        # 활동 타입 결정
        activity_type = None
        entity_type = None
        entity_id = None
        details = {}
        
        if '/products/' in request.path and request.method == 'GET':
            activity_type = 'view'
            entity_type = 'product'
            try:
                entity_id = int(request.path.split('/')[-1])
            except:
                pass
        elif '/search' in request.path:
            activity_type = 'search'
            details['search_query'] = request.args.get('q', '')
            details['results_count'] = 0  # 실제 결과 수는 응답을 처리한 후에 추가
        elif '/cart/add' in request.path:
            activity_type = 'cart_add'
            entity_type = 'product'
            entity_id = request.form.get('product_id')
        elif '/cart/remove' in request.path:
            activity_type = 'cart_remove'
            entity_type = 'product'
            entity_id = request.form.get('product_id')
        elif '/auth/login' in request.path and request.method == 'POST':
            activity_type = 'login_attempt'
            details['username_attempt'] = request.form.get('username', '') or request.form.get('email', '')
        elif '/auth/register' in request.path and request.method == 'POST':
            activity_type = 'register_attempt'
        
        # 기본 로그 데이터 구성
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": request.cookies.get('session', 'no_session'),
            "event_type": activity_type or 'page_view',
            "user_id": current_user.id if current_user.is_authenticated else None,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "endpoint": request.endpoint,
            "method": request.method,
            "path": request.path,
            "args": dict(request.args),
            "form": dict(request.form),
            "ip_address": request.remote_addr,
            "user_agent": request.user_agent.string if request.user_agent else "Unknown",
            "referrer": request.referrer,
        }
        
        # 추가 상세 정보가 있으면 병합
        if details:
            log_data.update(details)
        
        # 응답 정보 추가
        if response:
            log_data["response_status"] = response.status_code
            
            # 처리 시간 계산
            if hasattr(g, 'request_start_time'):
                process_time = (datetime.now() - g.request_start_time).total_seconds()
                log_data["process_time"] = process_time
        
        # 로그 기록
        activity_logger.info(json.dumps(log_data))
        
        # DB에 로그 저장
        activity_log = UserActivityLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=request.cookies.get('session', 'no_session'),
            activity_type=activity_type or 'page_view',
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(log_data),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else "Unknown"
        )
        
        db.session.add(activity_log)
        db.session.commit()
    except Exception as e:
        # 오류가 있어도 기본 기능 작동을 방해하지 않도록 예외 처리
        print(f"로그 기록 중 오류 발생: {e}")
        traceback.print_exc()
        db.session.rollback()  # DB 트랜잭션 롤백 