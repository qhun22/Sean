// JavaScript cho trang đăng ký
document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('email');
    const getOtpBtn = document.getElementById('otpBtn');
    const otpMessage = document.getElementById('otpMessage');
    
    // Xử lý nút Lấy mã OTP
    if (emailInput && getOtpBtn) {
        // Kiểm tra email hợp lệ
        function isValidEmail(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        }
        
        // Cập nhật trạng thái nút
        function updateOtpButtonState() {
            const email = emailInput.value.trim();
            if (isValidEmail(email)) {
                getOtpBtn.disabled = false;
                getOtpBtn.style.opacity = '1';
                getOtpBtn.style.cursor = 'pointer';
            } else {
                getOtpBtn.disabled = true;
                getOtpBtn.style.opacity = '0.5';
                getOtpBtn.style.cursor = 'not-allowed';
            }
        }
        
        // Khởi tạo trạng thái
        updateOtpButtonState();
        
        // Lắng nghe sự kiện nhập email
        emailInput.addEventListener('input', updateOtpButtonState);
        
        // Xử lý khi click nút Lấy mã
        getOtpBtn.addEventListener('click', function() {
            const email = emailInput.value.trim();
            
            if (!isValidEmail(email)) {
                if (window.QHToast) {
                    window.QHToast.show('Vui lòng nhập email hợp lệ!', 'error');
                }
                return;
            }
            
            // Vô hiệu hóa nút trong khi gửi
            getOtpBtn.disabled = true;
            getOtpBtn.textContent = 'Đang gửi...';
            
            fetch('/send-otp/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCsrfToken()
                },
                body: 'email=' + encodeURIComponent(email)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (QHToast) {
                        QHToast.show('Đã gửi mã OTP về email của bạn!', 'success');
                    }
                    // Ẩn message cũ
                    if (otpMessage) {
                        otpMessage.style.display = 'none';
                    }
                    // Đếm ngược 60s
                    let countdown = 60;
                    const interval = setInterval(function() {
                        getOtpBtn.textContent = 'Gửi lại sau ' + countdown + 's';
                        countdown--;
                        if (countdown < 0) {
                            clearInterval(interval);
                            getOtpBtn.textContent = 'Lấy mã';
                            updateOtpButtonState();
                        }
                    }, 1000);
                } else {
                    if (QHToast) {
                        QHToast.show(data.message || 'Gửi OTP thất bại!', 'error');
                    }
                    getOtpBtn.textContent = 'Lấy mã';
                    updateOtpButtonState();
                }
            })
            .catch(error => {
                if (QHToast) {
                    QHToast.show('Lỗi kết nối server!', 'error');
                }
                getOtpBtn.textContent = 'Lấy mã';
                updateOtpButtonState();
            });
        });
    }
});

// Hàm lấy CSRF token
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
