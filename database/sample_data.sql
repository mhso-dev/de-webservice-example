USE shopping_mall;

-- 카테고리 데이터 삽입
INSERT INTO categories (name, description, parent_id) VALUES
('전자제품', '컴퓨터, 휴대폰 등 전자제품', NULL),
('패션', '의류, 신발, 액세서리', NULL),
('가구/인테리어', '가구 및 인테리어 소품', NULL),
('식품', '신선식품, 가공식품 등', NULL),
('컴퓨터', '데스크톱, 노트북, 주변기기', 1),
('휴대폰', '스마트폰, 피처폰, 케이스', 1),
('남성의류', '남성을 위한 의류', 2),
('여성의류', '여성을 위한 의류', 2),
('생활가구', '침대, 소파, 테이블 등', 3),
('인테리어소품', '쿠션, 액자, 조명 등', 3),
('신선식품', '과일, 채소, 육류 등', 4),
('가공식품', '라면, 통조림, 스낵 등', 4);

-- 제품 데이터 삽입
INSERT INTO products (name, description, price, stock, category_id, image_url) VALUES
('삼성 갤럭시 S21', '삼성 최신 스마트폰', 899.99, 50, 6, '/static/images/galaxy_s21.jpg'),
('애플 맥북 프로', '13인치 M1 칩 탑재 맥북 프로', 1299.99, 30, 5, '/static/images/macbook_pro.jpg'),
('남성 슬림핏 청바지', '편안한 착용감의 슬림핏 청바지', 59.99, 100, 7, '/static/images/mens_jeans.jpg'),
('여성 니트 스웨터', '따뜻한 겨울용 니트 스웨터', 49.99, 80, 8, '/static/images/womens_sweater.jpg'),
('원목 식탁 세트', '4인용 원목 식탁 세트', 499.99, 10, 9, '/static/images/dining_table.jpg'),
('LED 스탠드 조명', '밝기 조절 가능한 LED 스탠드', 39.99, 60, 10, '/static/images/led_lamp.jpg'),
('애플 아이패드 에어', '10.9인치 아이패드 에어', 599.99, 25, 5, '/static/images/ipad_air.jpg'),
('LG 그램 노트북', '가벼운 울트라북', 1199.99, 15, 5, '/static/images/lg_gram.jpg'),
('삼성 QLED TV', '55인치 4K 스마트 TV', 799.99, 20, 1, '/static/images/samsung_tv.jpg'),
('소니 헤드폰', '노이즈 캔슬링 블루투스 헤드폰', 249.99, 40, 1, '/static/images/sony_headphones.jpg'),
('남성 캐주얼 셔츠', '면 100% 캐주얼 셔츠', 39.99, 120, 7, '/static/images/mens_shirt.jpg'),
('여성 가디건', '가볍고 따뜻한 가디건', 45.99, 90, 8, '/static/images/womens_cardigan.jpg'),
('3인용 패브릭 소파', '편안한 패브릭 소파', 599.99, 8, 9, '/static/images/sofa.jpg'),
('벽걸이 액자 세트', '다양한 사이즈의 액자 5개 세트', 29.99, 50, 10, '/static/images/frames.jpg'),
('유기농 과일 바구니', '제철 유기농 과일 모음', 39.99, 30, 11, '/static/images/fruit_basket.jpg'),
('프리미엄 견과류 선물세트', '다양한 견과류 선물세트', 49.99, 25, 12, '/static/images/nuts_gift.jpg');

-- 유저 데이터 삽입 (비밀번호 해시는 실제로는 bcrypt 등을 사용하여 생성해야 함)
INSERT INTO users (username, email, password_hash, first_name, last_name) VALUES
('john_doe', 'john.doe@example.com', '$2b$12$1tJXsK7CmVyRRqEhuYKvWOUwAp4aKQV9ZiVVJo4XItkHIJ8Z3DhOy', 'John', 'Doe'),
('jane_smith', 'jane.smith@example.com', '$2b$12$3aLg/vTZCavZNrd4NF92rOfBM4hOXg6TQM9M52.QVPbbq.1v5t4Dy', 'Jane', 'Smith'),
('mike_wilson', 'mike.wilson@example.com', '$2b$12$M/uLEMYyIjFNEkyoF7nKdOVr6GYXe8Fn1a3yjQf/oyiSuFCc1HKDq', 'Mike', 'Wilson'),
('sarah_johnson', 'sarah.johnson@example.com', '$2b$12$DgFGkW9ieGkKGDU3djKj6.kTjQh.EVKFvKP5VJ.vJZ.L17W0YSKYa', 'Sarah', 'Johnson'),
('david_brown', 'david.brown@example.com', '$2b$12$g8MFn.fVTT2OiBu0CIOKcOZsXE.AIFc.TCXNLPCPWzX93sV3JZvv2', 'David', 'Brown');

-- 장바구니 아이템 데이터
INSERT INTO cart_items (user_id, product_id, quantity) VALUES
(1, 3, 2),
(1, 7, 1),
(2, 4, 1),
(2, 13, 1),
(3, 9, 1),
(4, 2, 1),
(4, 6, 2),
(5, 16, 3);

-- 주문 데이터
INSERT INTO orders (user_id, total_amount, status, shipping_address) VALUES
(1, 1299.99, 'delivered', '123 Main St, Anytown, USA'),
(2, 549.98, 'shipped', '456 Elm St, Somewhere, USA'),
(3, 799.99, 'paid', '789 Oak St, Nowhere, USA'),
(4, 89.98, 'pending', '321 Pine St, Everywhere, USA'),
(5, 149.97, 'paid', '654 Maple St, Anywhere, USA');

-- 주문 아이템 데이터
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 2, 1, 1299.99),
(2, 13, 1, 599.99),
(3, 9, 1, 799.99),
(4, 6, 1, 39.99),
(4, 14, 1, 29.99),
(5, 16, 3, 49.99);

-- 제품 리뷰 데이터
INSERT INTO product_reviews (product_id, user_id, rating, comment) VALUES
(2, 1, 5, '최고의 노트북! 배터리 수명이 길고 성능이 뛰어납니다.'),
(9, 3, 4, '화질이 훌륭하지만 설치가 조금 복잡했습니다.'),
(13, 2, 5, '매우 편안하고 내구성이 좋습니다.'),
(6, 4, 3, '가격 대비 성능은 괜찮지만 밝기가 조금 아쉽습니다.'),
(16, 5, 5, '신선하고 맛있는 견과류 선물세트입니다!');

-- 사용자 활동 로그 데이터
INSERT INTO user_activity_logs (user_id, session_id, activity_type, entity_type, entity_id, details, ip_address, user_agent) VALUES
(1, 'sess_123456', 'view', 'product', 2, '{"page": "product_detail", "referrer": "home"}', '192.168.1.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(1, 'sess_123456', 'cart_add', 'product', 2, '{"quantity": 1}', '192.168.1.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(1, 'sess_123456', 'purchase', 'order', 1, '{"total": 1299.99, "payment_method": "credit_card"}', '192.168.1.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(2, 'sess_234567', 'search', NULL, NULL, '{"query": "소파", "results_count": 3}', '192.168.1.2', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'),
(2, 'sess_234567', 'view', 'product', 13, '{"page": "product_detail", "referrer": "search"}', '192.168.1.2', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'),
(2, 'sess_234567', 'cart_add', 'product', 13, '{"quantity": 1}', '192.168.1.2', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'),
(3, 'sess_345678', 'view', 'product', 9, '{"page": "product_detail", "referrer": "category"}', '192.168.1.3', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1)'),
(4, 'sess_456789', 'search', NULL, NULL, '{"query": "조명", "results_count": 2}', '192.168.1.4', 'Mozilla/5.0 (Android 10; Mobile)'),
(4, 'sess_456789', 'view', 'product', 6, '{"page": "product_detail", "referrer": "search"}', '192.168.1.4', 'Mozilla/5.0 (Android 10; Mobile)'),
(5, 'sess_567890', 'view', 'product', 16, '{"page": "product_detail", "referrer": "home"}', '192.168.1.5', 'Mozilla/5.0 (iPad; CPU OS 14_6)'),
(NULL, 'sess_678901', 'view', 'category', 5, '{"page": "category_list", "referrer": "home"}', '192.168.1.6', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(NULL, 'sess_678901', 'search', NULL, NULL, '{"query": "노트북", "results_count": 2}', '192.168.1.6', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'); 