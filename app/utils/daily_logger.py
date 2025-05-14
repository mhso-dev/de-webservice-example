import os
import logging
from datetime import datetime
from logging import FileHandler

class DailyFileHandler(FileHandler):
    """
    날짜별로 다른 파일에 로그를 기록하는 핸들러
    형식: base_name-YYYY-MM-DD.log
    """
    
    def __init__(self, base_name, mode='a', encoding=None, delay=False):
        """
        base_name: 기본 로그 파일 이름 (e.g., 'app' 또는 'user_activity')
        """
        self.base_name = base_name
        self.log_dir = os.path.dirname(base_name)
        self.base_filename = os.path.basename(base_name)
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.current_filename = self._get_current_filename()
        
        FileHandler.__init__(self, self.current_filename, mode, encoding, delay)
    
    def _get_current_filename(self):
        """오늘 날짜에 맞는 로그 파일 이름 반환"""
        return os.path.join(self.log_dir, f"{self.base_filename}-{self.today}.log")
    
    def emit(self, record):
        """로그 레코드 처리 시 날짜 확인 및 파일 전환"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today != self.today:
            # 날짜가 변경됨 - 파일 핸들러 갱신
            self.today = today
            self.current_filename = self._get_current_filename()
            self.close()
            self.baseFilename = self.current_filename
            self._open()
        
        FileHandler.emit(self, record)

def setup_logger(app):
    """
    Flask 애플리케이션을 위한 로깅 설정
    :param app: Flask 애플리케이션 인스턴스
    """
    # 로그 디렉토리 확인/생성
    log_dir = os.path.join(os.path.abspath(os.path.dirname(app.root_path)), 'logs')
    print(log_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 1. 시스템 로그 설정
    app_log_base = os.path.join(log_dir, 'app')
    app_handler = DailyFileHandler(app_log_base)
    app_handler.setLevel(logging.INFO)
    # 기본 Formatter 대신 커스텀 Formatter 사용
    app_handler.setFormatter(MicrosecondsFormatter(
        '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s", "module":"%(module)s"}',
        '%Y-%m-%dT%H:%M:%S.%f'
    ))
    
    # 기존 핸들러 제거 및 새 핸들러 추가
    app.logger.handlers = []
    app.logger.addHandler(app_handler)
    app.logger.setLevel(logging.INFO)
    
    # 2. 사용자 활동 로그 설정
    user_log_base = os.path.join(log_dir, 'user_activity')
    user_handler = DailyFileHandler(user_log_base)
    user_handler.setLevel(logging.INFO)
    user_handler.setFormatter(logging.Formatter('%(message)s'))
    
    user_logger = logging.getLogger('user_activity')
    user_logger.handlers = []
    user_logger.addHandler(user_handler)
    user_logger.setLevel(logging.INFO)
    user_logger.propagate = False
    
    app.logger.info('웹 서비스 시작 - 날짜별 로깅 설정 완료')
    return app

# 커스텀 Formatter 클래스 추가
class MicrosecondsFormatter(logging.Formatter):
    """마이크로초까지 표시하는 커스텀 Formatter"""
    
    def formatTime(self, record, datefmt=None):
        """타임스탬프 포맷 처리 (마이크로초 포함)"""
        created = datetime.fromtimestamp(record.created)
        if datefmt:
            # %f를 실제 마이크로초로 교체
            datefmt = datefmt.replace('%f', f'{created.microsecond:06d}')
            return created.strftime(datefmt)
        else:
            return created.strftime('%Y-%m-%d %H:%M:%S,%f')