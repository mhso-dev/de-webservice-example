from flask import Blueprint, jsonify, request, g, current_app
from flask_login import current_user, login_required
from app import db
from app.models import Product, Category, Order
import json
import logging
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/products', methods=['GET'])
def get_products():
    """상품 목록 API"""
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Product.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    products = query.paginate(page=page, per_page=per_page)
    
    result = {
        'total': products.total,
        'pages': products.pages,
        'current_page': page,
        'per_page': per_page,
        'products': [product.to_dict() for product in products.items]
    }
    
    return jsonify(result)

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """상품 상세 정보 API"""
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """카테고리 목록 API"""
    categories = Category.query.all()
    return jsonify([{
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'parent_id': category.parent_id
    } for category in categories])

@api_bp.route('/search', methods=['GET'])
def search_products():
    """상품 검색 API"""
    query = request.args.get('q', '')
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    search_query = Product.query
    
    if query:
        search_query = search_query.filter(
            Product.name.ilike(f'%{query}%') | Product.description.ilike(f'%{query}%')
        )
    
    if category_id:
        search_query = search_query.filter_by(category_id=category_id)
    
    products = search_query.paginate(page=page, per_page=per_page)
    
    result = {
        'total': products.total,
        'pages': products.pages,
        'current_page': page,
        'per_page': per_page,
        'products': [product.to_dict() for product in products.items]
    }
    
    return jsonify(result)

@api_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """사용자 주문 내역 API"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])

@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """주문 상세 정보 API"""
    order = Order.query.get_or_404(order_id)
    
    # 현재 사용자의 주문인지 확인
    if order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    return jsonify(order.to_dict())

@api_bp.route('/log/dwell-time', methods=['POST'])
def log_dwell_time():
    """페이지 체류 시간 로깅 API"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # 사용자 정보 추가
        user_id = current_user.id if current_user.is_authenticated else None
        session_id = g.session_id if hasattr(g, 'session_id') else None
        
        # 로그 데이터 구성
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'page_dwell',
            'user_id': user_id,
            'session_id': session_id,
            'product_id': data.get('product_id'),
            'dwell_time_seconds': data.get('dwell_time_seconds'),
            'max_scroll_percentage': data.get('max_scroll_percentage', 0),
            'path': data.get('path'),
            'referrer': data.get('referrer'),
            'user_agent': request.user_agent.string if request.user_agent else "Unknown",
            'ip_address': request.remote_addr
        }
        
        # 로깅
        activity_logger = logging.getLogger('user_activity')
        activity_logger.info(json.dumps(log_data))
        
        # DB에도 저장 (필요한 경우)
        from app.models.log import UserActivityLog
        
        log_entry = UserActivityLog(
            user_id=user_id,
            session_id=session_id,
            activity_type='page_dwell',
            entity_type='product',
            entity_id=data.get('product_id'),
            details=json.dumps(log_data),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else "Unknown"
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({'success': True}), 201
    
    except Exception as e:
        current_app.logger.error(f"체류 시간 로깅 오류: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/log/click-event', methods=['POST'])
def log_click_event():
    """사용자 클릭 이벤트 로깅 API"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # 사용자 정보 추가
        user_id = current_user.id if current_user.is_authenticated else None
        session_id = g.session_id if hasattr(g, 'session_id') else None
        
        # 로그 데이터 구성
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'click_event',
            'user_id': user_id,
            'session_id': session_id,
            'product_id': data.get('product_id'),
            'element_type': data.get('element_type'),
            'element_text': data.get('element_text'),
            'link_href': data.get('link_href'),
            'position_x_percent': data.get('position_x_percent'),
            'position_y_percent': data.get('position_y_percent'),
            'is_cart_action': data.get('is_cart_action', False),
            'path': request.referrer,
            'user_agent': request.user_agent.string if request.user_agent else "Unknown",
            'ip_address': request.remote_addr
        }
        
        # 로깅
        activity_logger = logging.getLogger('user_activity')
        activity_logger.info(json.dumps(log_data))
        
        # DB에도 저장 (필요한 경우)
        from app.models.log import UserActivityLog
        
        log_entry = UserActivityLog(
            user_id=user_id,
            session_id=session_id,
            activity_type='click_event',
            entity_type='product',
            entity_id=data.get('product_id'),
            details=json.dumps(log_data),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else "Unknown"
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({'success': True}), 201
    
    except Exception as e:
        current_app.logger.error(f"클릭 이벤트 로깅 오류: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 