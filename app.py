from app import create_app, db
from app.models import User, Category, Product, ProductReview, CartItem, Order, OrderItem, UserActivityLog
import logging
import json
from datetime import datetime

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Flask shell에서 사용할 컨텍스트 제공"""
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Product': Product,
        'ProductReview': ProductReview,
        'CartItem': CartItem,
        'Order': Order,
        'OrderItem': OrderItem,
        'UserActivityLog': UserActivityLog
    }

if __name__ == '__main__':
    # 시작 시 로깅 테스트
    print("애플리케이션 시작 - 로깅 테스트")
    
    # user_activity 로거 직접 테스트
    activity_logger = logging.getLogger('user_activity')
    test_log = {
        'timestamp': datetime.now().isoformat(),
        'event': 'app_start_test',
        'message': '애플리케이션 시작 테스트 로그'
    }
    activity_logger.info(json.dumps(test_log))
    print(f"테스트 로그 작성 시도: {json.dumps(test_log)}")
    
    # 애플리케이션 실행
    app.run(host='0.0.0.0', port=5001, debug=True) 