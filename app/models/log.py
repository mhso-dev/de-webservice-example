from datetime import datetime
from app import db

class UserActivityLog(db.Model):
    __tablename__ = 'user_activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    session_id = db.Column(db.String(100))
    activity_type = db.Column(db.String(20))
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON 형식 문자열로 저장
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 정의
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))
    
    def __repr__(self):
        return f'<UserActivityLog {self.id} - Type {self.activity_type} - User {self.user_id}>' 