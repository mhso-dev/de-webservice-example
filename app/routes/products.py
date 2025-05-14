from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app import db
from app.models import Product, Category, ProductReview, Order, OrderItem
from sqlalchemy import text

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/')
def index():
    """상품 목록 페이지"""
    category_id = request.args.get('category', type=int)
    
    # 기본 정렬은 최신순
    sort = request.args.get('sort', 'newest')
    
    products_query = Product.query
    
    # 카테고리 필터링
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
    
    # 정렬
    if sort == 'price_low':
        products_query = products_query.order_by(Product.price.asc())
    elif sort == 'price_high':
        products_query = products_query.order_by(Product.price.desc())
    else:  # newest
        products_query = products_query.order_by(Product.created_at.desc())
    
    # 페이지네이션
    page = request.args.get('page', 1, type=int)
    products = products_query.paginate(page=page, per_page=12)
    
    categories = Category.query.all()
    
    selected_category = None
    if category_id:
        selected_category = Category.query.get(category_id)
    
    return render_template('products/index.html', 
                           products=products,
                           categories=categories,
                           selected_category=selected_category,
                           sort=sort)

@products_bp.route('/<int:product_id>')
def detail(product_id):
    """상품 상세 페이지"""
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter_by(category_id=product.category_id).filter(Product.id != product.id).limit(4).all()
    reviews = ProductReview.query.filter_by(product_id=product_id).order_by(ProductReview.created_at.desc()).all()
    
    # 리뷰 평균 평점 계산
    avg_rating = 0
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)
    
    # 사용자가 이미 리뷰를 작성했는지 확인
    user_review = None
    # 사용자가 해당 상품을 구매했는지 확인
    has_purchased = False
    debug_info = {}
    
    if current_user.is_authenticated:
        user_review = ProductReview.query.filter_by(
            product_id=product_id,
            user_id=current_user.id
        ).first()
        
        # 구매 여부 확인 - 명시적 조인 사용
        order_items = OrderItem.query.join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.product_id == product_id,
            Order.user_id == current_user.id,
            # 상태가 없거나(null) 빈 문자열인 경우도 유효한 구매로 인정
            (Order.status.in_(['결제완료', '주문완료', '배송중', '배송완료']) | 
             Order.status.is_(None) | 
             Order.status == '')
        ).all()
        
        # 디버깅 정보 수집
        debug_info['user_id'] = current_user.id
        debug_info['product_id'] = product_id
        debug_info['order_items_count'] = len(order_items)
        debug_info['order_items'] = []
        
        for item in order_items:
            debug_info['order_items'].append({
                'order_id': item.order_id,
                'order_status': item.order.status if hasattr(item, 'order') else 'Unknown'
            })
        
        # 직접 SQL을 사용한 디버깅
        # 1. 해당 사용자의 전체 주문 확인
        user_orders_query = text("""
            SELECT id, status, created_at 
            FROM orders 
            WHERE user_id = :user_id
        """)
        user_orders_result = db.session.execute(user_orders_query, {'user_id': current_user.id})
        print("\n=== 사용자 주문 목록 (직접 SQL) ===")
        user_order_ids = []
        for row in user_orders_result:
            print(f"주문 ID: {row.id}, 상태: {row.status}, 날짜: {row.created_at}")
            user_order_ids.append(row.id)
        
        # 2. 해당 상품의 주문 아이템 확인
        if user_order_ids:
            try:
                if len(user_order_ids) == 1:
                    # 단일 주문인 경우
                    order_items_query = text("""
                        SELECT oi.id, oi.order_id, oi.product_id, oi.quantity, o.status
                        FROM order_items oi
                        JOIN orders o ON oi.order_id = o.id
                        WHERE oi.product_id = :product_id
                        AND oi.order_id = :order_id
                    """)
                    order_items_result = db.session.execute(
                        order_items_query, 
                        {'product_id': product_id, 'order_id': user_order_ids[0]})
                else:
                    # 여러 주문인 경우
                    order_ids_str = ','.join(str(id) for id in user_order_ids)
                    order_items_query = text(f"""
                        SELECT oi.id, oi.order_id, oi.product_id, oi.quantity, o.status
                        FROM order_items oi
                        JOIN orders o ON oi.order_id = o.id
                        WHERE oi.product_id = :product_id
                        AND oi.order_id IN ({order_ids_str})
                    """)
                    order_items_result = db.session.execute(
                        order_items_query, 
                        {'product_id': product_id})
                
                print("\n=== 해당 상품 주문 아이템 (직접 SQL) ===")
                sql_has_purchased = False  # SQL로 직접 확인한 구매 여부
                for row in order_items_result:
                    print(f"주문 아이템 ID: {row.id}, 주문 ID: {row.order_id}, 상품 ID: {row.product_id}, 수량: {row.quantity}, 상태: {row.status}")
                    # 상태가 특정 값이거나 null/빈 문자열인 경우 구매로 인정
                    if row.status in ['결제완료', '주문완료', '배송중', '배송완료'] or row.status is None or row.status == '':
                        sql_has_purchased = True
                
                # 불일치 시 알림
                if sql_has_purchased != has_purchased:
                    print(f"\n!!! 불일치 감지: ORM 쿼리 결과({has_purchased}) != SQL 쿼리 결과({sql_has_purchased}) !!!")
                    # 직접 SQL로 확인한 값을 사용
                    has_purchased = sql_has_purchased
            
            except Exception as e:
                print(f"SQL 쿼리 실행 중 오류 발생: {str(e)}")
        
        # 서버 콘솔에 디버깅 정보 출력
        print(f"DEBUG: 사용자 {current_user.id}의 상품 {product_id} 구매 여부: {has_purchased}")
        print(f"DEBUG: 해당 상품 주문 수: {len(order_items)}")
    
    return render_template('products/detail.html', 
                           product=product,
                           related_products=related_products,
                           reviews=reviews,
                           avg_rating=avg_rating,
                           user_review=user_review,
                           has_purchased=has_purchased,
                           debug_info=debug_info)

@products_bp.route('/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    """상품 리뷰 추가"""
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    if not rating or rating < 1 or rating > 5:
        flash('별점을 선택해주세요.', 'warning')
        return redirect(url_for('products.detail', product_id=product_id))
    
    # 이미 리뷰를 작성했는지 확인
    existing_review = ProductReview.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()
    
    if existing_review:
        # 기존 리뷰 업데이트
        existing_review.rating = rating
        existing_review.comment = comment
        db.session.commit()
        flash('리뷰가 업데이트되었습니다.', 'success')
    else:
        # 새 리뷰 작성 - 구매 여부 확인 (명시적 조인 사용)
        order_items = OrderItem.query.join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.product_id == product_id,
            Order.user_id == current_user.id,
            # 상태가 없거나(null) 빈 문자열인 경우도 유효한 구매로 인정
            (Order.status.in_(['결제완료', '주문완료', '배송중', '배송완료']) | 
             Order.status.is_(None) | 
             Order.status == '')
        ).all()
        
        purchased = len(order_items) > 0
        
        # 직접 SQL을 사용한 디버깅
        try:
            # 사용자의 주문 목록 조회 - 상태 조건 수정
            user_orders_query = text("""
                SELECT id FROM orders 
                WHERE user_id = :user_id
                AND (status IN ('결제완료', '주문완료', '배송중', '배송완료') 
                     OR status IS NULL 
                     OR status = '')
            """)
            user_orders_result = db.session.execute(user_orders_query, {'user_id': current_user.id})
            
            user_order_ids = [row.id for row in user_orders_result]
            
            # 주문 아이템 조회
            sql_purchased = False
            if user_order_ids:
                if len(user_order_ids) == 1:
                    order_items_query = text("""
                        SELECT id FROM order_items
                        WHERE product_id = :product_id
                        AND order_id = :order_id
                    """)
                    result = db.session.execute(order_items_query, {
                        'product_id': product_id,
                        'order_id': user_order_ids[0]
                    })
                else:
                    order_ids_str = ','.join(str(id) for id in user_order_ids)
                    order_items_query = text(f"""
                        SELECT id FROM order_items
                        WHERE product_id = :product_id
                        AND order_id IN ({order_ids_str})
                    """)
                    result = db.session.execute(order_items_query, {'product_id': product_id})
                
                # 결과가 있으면 구매한 것
                sql_purchased = result.first() is not None
            
            # 불일치 시 보고 및 SQL 결과 사용
            if sql_purchased != purchased:
                print(f"\n!!! 리뷰 작성 - 구매 여부 불일치: ORM({purchased}) != SQL({sql_purchased}) !!!")
                purchased = sql_purchased
        
        except Exception as e:
            print(f"리뷰 SQL 쿼리 실행 중 오류: {str(e)}")
        
        # 디버깅 정보 출력
        print(f"DEBUG: 리뷰 작성 - 사용자 {current_user.id}의 상품 {product_id} 구매 여부: {purchased}")
        print(f"DEBUG: 리뷰 작성 - 해당 상품 주문 수: {len(order_items)}")
        
        if not purchased:
            flash('구매한 상품에 대해서만 리뷰를 작성할 수 있습니다.', 'warning')
            return redirect(url_for('products.detail', product_id=product_id))
            
        # 새 리뷰 작성
        review = ProductReview(
            product_id=product_id,
            user_id=current_user.id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()
        flash('리뷰가 등록되었습니다.', 'success')
    
    return redirect(url_for('products.detail', product_id=product_id))

@products_bp.route('/<int:product_id>/review/delete', methods=['POST'])
@login_required
def delete_review(product_id):
    """상품 리뷰 삭제"""
    # 해당 사용자의 리뷰가 있는지 확인
    review = ProductReview.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()
    
    if not review:
        flash('삭제할 리뷰가 없습니다.', 'warning')
        return redirect(url_for('products.detail', product_id=product_id))
    
    # 리뷰 삭제
    db.session.delete(review)
    db.session.commit()
    
    flash('리뷰가 삭제되었습니다.', 'success')
    return redirect(url_for('products.detail', product_id=product_id))

@products_bp.route('/category/<int:category_id>')
def category(category_id):
    """카테고리별 상품 목록"""
    return redirect(url_for('products.index', category=category_id)) 