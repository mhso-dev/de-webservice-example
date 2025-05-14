from datetime import datetime
from app import db

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CartItem {self.id} - User {self.user_id} - Product {self.product_id}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.id} - User {self.user_id} - Total {self.total_amount}>'
    
    def to_dict(self):
        """API 응답용 딕셔너리 반환"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'shipping_address': self.shipping_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OrderItem {self.id} - Order {self.order_id} - Product {self.product_id}>'
    
    def to_dict(self):
        """API 응답용 딕셔너리 반환"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown Product',
            'quantity': self.quantity,
            'price': float(self.price),
            'subtotal': float(self.price * self.quantity)
        } 