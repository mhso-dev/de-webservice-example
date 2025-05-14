// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    // 장바구니 수량 변경 이벤트 처리
    setupCartQuantityButtons();
    
    // 별점 선택 이벤트 처리
    setupRatingStars();
    
    // 액티브 네비게이션 표시
    highlightActiveNavigation();
    
    // 플래시 메시지 자동 사라짐
    setupFlashMessages();
    
    // 페이지 체류 시간 측정 시작
    setupPageDwellTimeTracking();
});

// 장바구니 수량 변경 버튼 설정
function setupCartQuantityButtons() {
    const quantityForms = document.querySelectorAll('.quantity-form');
    
    quantityForms.forEach(form => {
        const decreaseBtn = form.querySelector('.btn-decrease');
        const increaseBtn = form.querySelector('.btn-increase');
        const quantityInput = form.querySelector('.quantity-input');
        
        if (decreaseBtn && increaseBtn && quantityInput) {
            decreaseBtn.addEventListener('click', function(e) {
                e.preventDefault();
                let value = parseInt(quantityInput.value);
                if (value > 1) {
                    quantityInput.value = value - 1;
                    form.submit();
                }
            });
            
            increaseBtn.addEventListener('click', function(e) {
                e.preventDefault();
                let value = parseInt(quantityInput.value);
                const maxStock = parseInt(quantityInput.dataset.maxStock || 99);
                if (value < maxStock) {
                    quantityInput.value = value + 1;
                    form.submit();
                }
            });
        }
    });
}

// 별점 선택 설정
function setupRatingStars() {
    const ratingContainer = document.querySelector('.rating-container');
    
    if (ratingContainer) {
        const stars = ratingContainer.querySelectorAll('.rating-star');
        const ratingInput = document.getElementById('rating');
        let selectedRating = parseInt(ratingInput.value) || 5;
        
        // 초기 별점 표시
        updateStarsDisplay(stars, selectedRating);
        
        // 각 별에 이벤트 리스너 추가
        stars.forEach((star, index) => {
            const starValue = 5 - index;
            
            // 마우스 오버 이벤트
            star.addEventListener('mouseover', function() {
                highlightStars(stars, starValue);
            });
            
            // 마우스 아웃 이벤트
            star.addEventListener('mouseout', function() {
                updateStarsDisplay(stars, selectedRating);
            });
            
            // 클릭 이벤트
            star.addEventListener('click', function() {
                selectedRating = starValue;
                ratingInput.value = selectedRating;
                updateStarsDisplay(stars, selectedRating);
            });
        });
    }
}

// 별 하이라이트 표시
function highlightStars(stars, rating) {
    stars.forEach((star, i) => {
        const starValue = 5 - i;
        if (starValue <= rating) {
            star.querySelector('i').classList.add('active');
            star.querySelector('i').style.color = '#ffc107'; // 노란색
        } else {
            star.querySelector('i').classList.remove('active');
            star.querySelector('i').style.color = '#ccc'; // 회색
        }
    });
}

// 선택된 별점에 따라 별 표시 업데이트
function updateStarsDisplay(stars, rating) {
    highlightStars(stars, rating);
}

// 현재 페이지의 네비게이션 링크를 활성화
function highlightActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
            link.classList.add('fw-bold');
        }
    });
}

// 플래시 메시지 자동 사라짐 설정
function setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(message);
            bsAlert.close();
        }, 5000);
    });
}

// 상품 목록 정렬 처리
function changeSort(selectElement) {
    const url = new URL(window.location);
    url.searchParams.set('sort', selectElement.value);
    window.location.href = url.toString();
}

// 페이지 체류 시간 측정
function setupPageDwellTimeTracking() {
    // 현재 페이지가 상품 상세 페이지인지 확인
    const isProductDetail = window.location.pathname.match(/\/products\/\d+$/);
    if (!isProductDetail) return;
    
    // 페이지 진입 시간 기록
    const pageEntryTime = Date.now();
    const productId = window.location.pathname.split('/').pop();
    
    // 스크롤 위치 추적을 위한 변수
    let maxScrollPercentage = 0;
    
    // 스크롤 이벤트 리스너
    window.addEventListener('scroll', function() {
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPosition = window.scrollY;
        const scrollPercentage = Math.round((scrollPosition / scrollHeight) * 100);
        
        // 최대 스크롤 위치 업데이트
        if (scrollPercentage > maxScrollPercentage) {
            maxScrollPercentage = scrollPercentage;
        }
    });
    
    // 페이지 이탈 시 체류 시간 기록
    function logDwellTime() {
        const dwellTime = Math.round((Date.now() - pageEntryTime) / 1000); // 초 단위로 변환
        
        // 페이지 이탈 시 데이터 전송 (1초 이상 체류한 경우에만)
        if (dwellTime >= 1) {
            const logData = {
                product_id: productId,
                dwell_time_seconds: dwellTime,
                max_scroll_percentage: maxScrollPercentage,
                path: window.location.pathname,
                referrer: document.referrer || "직접 접속"
            };
            
            // 비동기로 데이터 전송
            fetch('/api/log/dwell-time', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(logData),
                // 페이지 이탈 중에도 요청이 완료되도록 keepalive 설정
                keepalive: true
            }).catch(error => console.error('체류 시간 로깅 오류:', error));
        }
    }
    
    // 페이지 이탈 이벤트에 리스너 등록
    window.addEventListener('beforeunload', logDwellTime);
    window.addEventListener('pagehide', logDwellTime);
    
    // 클릭 이벤트 추적
    document.addEventListener('click', function(event) {
        // 클릭된 요소의 정보 수집
        const clickedElement = event.target.tagName;
        const nearestLink = event.target.closest('a');
        const nearestButton = event.target.closest('button');
        const clickX = event.clientX;
        const clickY = event.clientY;
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        // 클릭 위치를 백분율로 계산
        const clickXPercent = Math.round((clickX / windowWidth) * 100);
        const clickYPercent = Math.round((clickY / windowHeight) * 100);
        
        // 중요 클릭 이벤트만 기록 (링크, 버튼, 장바구니 추가 등)
        if (nearestLink || nearestButton || clickedElement === 'INPUT' || clickedElement === 'BUTTON') {
            const logData = {
                product_id: productId,
                element_type: clickedElement,
                element_text: event.target.textContent?.trim().substring(0, 50) || null,
                link_href: nearestLink?.href || null,
                position_x_percent: clickXPercent,
                position_y_percent: clickYPercent,
                is_cart_action: (nearestButton && nearestButton.textContent?.includes('장바구니')) || false
            };
            
            // 비동기로 클릭 이벤트 전송
            fetch('/api/log/click-event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(logData)
            }).catch(error => console.error('클릭 이벤트 로깅 오류:', error));
        }
    });
} 