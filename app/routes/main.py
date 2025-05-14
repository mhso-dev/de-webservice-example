from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Product, Category, CartItem, Order, OrderItem
import uuid

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """메인 페이지"""
    featured_products = Product.query.order_by(Product.id.desc()).limit(8).all()
    categories = Category.query.filter_by(parent_id=None).all()
    return render_template('index.html', 
                           featured_products=featured_products,
                           categories=categories)

@main_bp.route('/search')
def search():
    """상품 검색"""
    query = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    sort = request.args.get('sort', 'relevance')
    
    products_query = Product.query
    
    if query:
        products_query = products_query.filter(
            Product.name.ilike(f'%{query}%') | Product.description.ilike(f'%{query}%')
        )
    
    if category_id:
        selected_category = Category.query.get(category_id)
        if selected_category:
            if selected_category.subcategories:  # 상위 카테고리인 경우
                # 현재 카테고리 + 모든 하위 카테고리 ID 목록
                subcategory_ids = [subcat.id for subcat in selected_category.subcategories]
                category_ids = [category_id] + subcategory_ids
                products_query = products_query.filter(Product.category_id.in_(category_ids))
            else:  # 하위 카테고리인 경우
                products_query = products_query.filter_by(category_id=category_id)
    
    # 정렬 적용
    if sort == 'price_asc':
        products_query = products_query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        products_query = products_query.order_by(Product.price.desc())
    elif sort == 'newest':
        products_query = products_query.order_by(Product.created_at.desc())
    
    # 페이지네이션
    page = request.args.get('page', 1, type=int)
    products = products_query.paginate(page=page, per_page=12)
    
    categories = Category.query.filter_by(parent_id=None).all()
    
    # 검색 이벤트 로깅
    if query:
        try:
            import json
            import logging
            from datetime import datetime
            from flask_login import current_user
            from app import db
            from app.models.log import UserActivityLog
            
            # 사용자 정보
            user_id = current_user.id if current_user.is_authenticated else None
            session_id = request.cookies.get('session') or 'unknown'
            
            # 로그 데이터 구성
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'search',
                'user_id': user_id,
                'session_id': session_id,
                'search_query': query,
                'category_id': category_id,
                'sort_option': sort,
                'page': page,
                'results_count': products.total,
                'results_page_count': products.pages,
                'user_agent': request.user_agent.string if request.user_agent else "Unknown",
                'ip_address': request.remote_addr,
                'referrer': request.referrer
            }
            
            # 로깅
            activity_logger = logging.getLogger('user_activity')
            activity_logger.info(json.dumps(log_data))
            
            # DB에 저장
            log_entry = UserActivityLog(
                user_id=user_id,
                session_id=session_id,
                activity_type='search',
                entity_type='query',
                entity_id=None,
                details=json.dumps(log_data),
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string if request.user_agent else "Unknown"
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            print(f"검색 로깅 오류: {str(e)}")
    
    return render_template('search.html', 
                           products=products,
                           categories=categories,
                           query=query,
                           category_id=category_id,
                           sort=sort)

@main_bp.route('/cart')
@login_required
def cart():
    """장바구니 페이지"""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@main_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """장바구니에 상품 추가"""
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    
    if not product_id or quantity <= 0:
        flash('Invalid request', 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    product = Product.query.get_or_404(product_id)
    
    # 이미 장바구니에 있는 상품인지 확인
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()
    
    # 장바구니 상태 및 변경 사항 기록
    is_new_item = False
    previous_quantity = 0
    
    if cart_item:
        # 이전 수량 기록
        previous_quantity = cart_item.quantity
        # 수량 증가
        cart_item.quantity += quantity
    else:
        # 새 항목 추가
        is_new_item = True
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    # 장바구니 추가 이벤트 로깅
    try:
        import json
        import logging
        from datetime import datetime
        from app.models.log import UserActivityLog
        
        # 세션 ID 획득
        session_id = request.cookies.get('session') or 'unknown'
        
        # 참조 페이지 정보
        ref_page = request.referrer or 'direct'
        ref_type = 'unknown'
        
        if '/products/' in ref_page:
            if f'/products/{product_id}' in ref_page:
                ref_type = 'product_detail'
            else:
                ref_type = 'product_list'
        elif '/search' in ref_page:
            ref_type = 'search_results'
        elif '/cart' in ref_page:
            ref_type = 'cart'
        
        # 로그 데이터 구성
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'cart_add',
            'user_id': current_user.id,
            'session_id': session_id,
            'product_id': product_id,
            'product_name': product.name,
            'product_price': float(product.price),
            'quantity': quantity,
            'is_new_item': is_new_item,
            'previous_quantity': previous_quantity,
            'current_quantity': cart_item.quantity,
            'referrer_page': ref_page,
            'referrer_type': ref_type,
            'user_agent': request.user_agent.string if request.user_agent else "Unknown",
            'ip_address': request.remote_addr
        }
        
        # 로깅
        activity_logger = logging.getLogger('user_activity')
        activity_logger.info(json.dumps(log_data))
        
        # DB에 저장
        log_entry = UserActivityLog(
            user_id=current_user.id,
            session_id=session_id,
            activity_type='cart_add',
            entity_type='product',
            entity_id=product_id,
            details=json.dumps(log_data),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else "Unknown"
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"장바구니 추가 로깅 오류: {str(e)}")
    
    flash(f'"{product.name}" 상품이 장바구니에 추가되었습니다.', 'success')
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    """장바구니에서 상품 제거"""
    cart_item_id = request.form.get('cart_item_id', type=int)
    
    if not cart_item_id:
        flash('Invalid request', 'danger')
        return redirect(url_for('main.cart'))
    
    cart_item = CartItem.query.get_or_404(cart_item_id)
    
    # 현재 사용자의 장바구니 항목인지 확인
    if cart_item.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('main.cart'))
    
    # 제거할 상품 정보 저장
    product_id = cart_item.product_id
    product_name = cart_item.product.name if hasattr(cart_item, 'product') else "Unknown"
    product_price = float(cart_item.product.price) if hasattr(cart_item, 'product') else 0
    removed_quantity = cart_item.quantity
    
    # 장바구니에서 제거
    db.session.delete(cart_item)
    db.session.commit()
    
    # 장바구니 제거 이벤트 로깅
    try:
        import json
        import logging
        from datetime import datetime
        from app.models.log import UserActivityLog
        
        # 세션 ID 획득
        session_id = request.cookies.get('session') or 'unknown'
        
        # 로그 데이터 구성
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'cart_remove',
            'user_id': current_user.id,
            'session_id': session_id,
            'product_id': product_id,
            'product_name': product_name,
            'product_price': product_price,
            'removed_quantity': removed_quantity,
            'referrer_page': request.referrer or 'direct',
            'user_agent': request.user_agent.string if request.user_agent else "Unknown",
            'ip_address': request.remote_addr
        }
        
        # 로깅
        activity_logger = logging.getLogger('user_activity')
        activity_logger.info(json.dumps(log_data))
        
        # DB에 저장
        log_entry = UserActivityLog(
            user_id=current_user.id,
            session_id=session_id,
            activity_type='cart_remove',
            entity_type='product',
            entity_id=product_id,
            details=json.dumps(log_data),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else "Unknown"
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"장바구니 제거 로깅 오류: {str(e)}")
    
    flash('상품이 장바구니에서 제거되었습니다.', 'success')
    return redirect(url_for('main.cart'))

@main_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """주문 결제 페이지"""
    if request.method == 'GET':
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash('장바구니가 비어있습니다.', 'warning')
            return redirect(url_for('main.index'))
        
        total = sum(item.product.price * item.quantity for item in cart_items)
        return render_template('checkout.html', cart_items=cart_items, total=total)
    
    else:  # POST
        # 주문 정보 처리
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash('장바구니가 비어있습니다.', 'warning')
            return redirect(url_for('main.index'))
        
        # 배송 주소 등 정보 수집
        recipient_name = request.form.get('recipient_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        address_detail = request.form.get('address_detail', '')
        postcode = request.form.get('postcode')
        
        # 배송 주소 조합
        shipping_address = f"{recipient_name}, {phone}, ({postcode}) {address}"
        if address_detail:
            shipping_address += f" {address_detail}"
        
        # 필수 필드 검증
        if not all([recipient_name, phone, address, postcode]):
            flash('모든 필수 항목을 입력해주세요.', 'warning')
            return redirect(url_for('main.checkout'))
        
        # 주문 생성
        total = sum(item.product.price * item.quantity for item in cart_items)
        
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            status='주문완료',
            shipping_address=shipping_address
        )
        db.session.add(order)
        db.session.flush()  # order.id 얻기 위한 임시 커밋
        
        # 주문 항목 생성
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
            
            # 재고 감소 처리
            product = cart_item.product
            product.stock -= cart_item.quantity
            
            # 장바구니 항목 삭제
            db.session.delete(cart_item)
        
        db.session.commit()
        
        flash('주문이 완료되었습니다!', 'success')
        return redirect(url_for('main.order_confirmation', order_id=order.id))

@main_bp.route('/orders/<int:order_id>/confirmation')
@login_required
def order_confirmation(order_id):
    """주문 확인 페이지"""
    order = Order.query.get_or_404(order_id)
    
    # 현재 사용자의 주문인지 확인
    if order.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('main.index'))
    
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('order_confirmation.html', order=order, order_items=order_items)

@main_bp.route('/orders')
@login_required
def order_history():
    """주문 내역 페이지"""
    page = request.args.get('page', 1, type=int)
    orders_query = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc())
    pagination = orders_query.paginate(page=page, per_page=10)
    orders = pagination.items
    return render_template('auth/order_history.html', orders=orders, pagination=pagination)

@main_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """주문 상세 정보 페이지"""
    order = Order.query.get_or_404(order_id)
    
    # 현재 사용자의 주문인지 확인
    if order.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('main.index'))
    
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('auth/order_detail.html', order=order, order_items=order_items) 