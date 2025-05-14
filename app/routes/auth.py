from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """사용자 회원가입"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # 기본 검증
        if not username or not email or not password:
            flash('모든 필수 항목을 입력해주세요.', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('비밀번호가 일치하지 않습니다.', 'danger')
            return render_template('auth/register.html')
        
        # 사용자명 중복 확인
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('이미 사용 중인 사용자명입니다.', 'danger')
            return render_template('auth/register.html')
        
        # 이메일 중복 확인
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('이미 사용 중인 이메일입니다.', 'danger')
            return render_template('auth/register.html')
        
        # 신규 사용자 생성
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다. 로그인해주세요.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """사용자 로그인"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        if not username or not password:
            flash('사용자명과 비밀번호를 입력해주세요.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('사용자명 또는 비밀번호가 잘못되었습니다.', 'danger')
            
            # 로그인 실패 로그 기록
            try:
                import json
                from datetime import datetime
                import logging
                from app.models.log import UserActivityLog
                
                # 로그 데이터 구성
                log_data = {
                    'timestamp': datetime.now().isoformat(),
                    'event_type': 'login_failed',
                    'username_attempt': username,
                    'session_id': session.get('session_id'),
                    'ip_address': request.remote_addr,
                    'user_agent': request.user_agent.string if request.user_agent else "Unknown",
                    'reason': 'invalid_credentials'
                }
                
                # 로거를 통해 로깅
                activity_logger = logging.getLogger('user_activity')
                activity_logger.info(json.dumps(log_data))
                
                # DB에 로그 저장 - 실패한 사용자 이름으로 저장
                log_entry = UserActivityLog(
                    user_id=None,  # 로그인 실패이므로 user_id는 None
                    session_id=session.get('session_id'),
                    activity_type='login_failed',
                    entity_type='auth',
                    entity_id=None,
                    details=json.dumps(log_data),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string if request.user_agent else "Unknown"
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                print(f"로그인 실패 로깅 오류: {str(e)}")
                db.session.rollback()
            
            return render_template('auth/login.html')
        
        # 로그인 처리
        login_user(user, remember=remember)
        
        # 명시적으로 로그인 로그 기록
        try:
            import json
            from datetime import datetime
            import logging
            from app.models.log import UserActivityLog
            
            # 로그 데이터 구성
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'login',
                'user_id': user.id,  # 명시적으로 사용자 ID 설정
                'session_id': session.get('session_id'),
                'username': user.username,
                'ip_address': request.remote_addr,
                'user_agent': request.user_agent.string if request.user_agent else "Unknown"
            }
            
            # 로거를 통해 로깅
            activity_logger = logging.getLogger('user_activity')
            activity_logger.info(json.dumps(log_data))
            
            # DB에 로그 저장
            log_entry = UserActivityLog(
                user_id=user.id,
                session_id=session.get('session_id'),
                activity_type='login',
                entity_type='user',
                entity_id=user.id,
                details=json.dumps(log_data),
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string if request.user_agent else "Unknown"
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            print(f"로그인 로깅 오류: {str(e)}")
            db.session.rollback()
        
        # 리디렉션 URL 처리
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        
        flash('로그인되었습니다.', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """사용자 로그아웃"""
    # 명시적으로 로그아웃 로그 기록
    try:
        import json
        from datetime import datetime
        import logging
        from app.models.log import UserActivityLog
        
        # 로그 데이터 구성
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'logout',
            'user_id': current_user.id,
            'session_id': session.get('session_id'),
            'username': current_user.username,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string if request.user_agent else "Unknown"
        }
        
        # 로거를 통해 로깅
        activity_logger = logging.getLogger('user_activity')
        activity_logger.info(json.dumps(log_data))
        
        # DB에 로그 저장
        log_entry = UserActivityLog(
            user_id=current_user.id,
            session_id=session.get('session_id'),
            activity_type='logout',
            entity_type='user',
            entity_id=current_user.id,
            details=json.dumps(log_data),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else "Unknown"
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"로그아웃 로깅 오류: {str(e)}")
        db.session.rollback()
    
    logout_user()
    session.clear()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """사용자 프로필 페이지"""
    return render_template('auth/profile.html')

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """사용자 프로필 편집"""
    if request.method == 'POST':
        user = current_user
        
        # 프로필 정보 업데이트
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        
        # 이메일 변경 처리
        new_email = request.form.get('email')
        if new_email != user.email:
            existing_email = User.query.filter_by(email=new_email).first()
            if existing_email:
                flash('이미 사용 중인 이메일입니다.', 'danger')
                return render_template('auth/edit_profile.html')
            user.email = new_email
        
        # 비밀번호 변경 처리
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password:
            if not user.check_password(current_password):
                flash('현재 비밀번호가 일치하지 않습니다.', 'danger')
                return render_template('auth/edit_profile.html')
            
            if new_password != confirm_password:
                flash('새 비밀번호가 일치하지 않습니다.', 'danger')
                return render_template('auth/edit_profile.html')
            
            user.set_password(new_password)
        
        db.session.commit()
        flash('프로필이 업데이트되었습니다.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html') 