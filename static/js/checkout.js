/* ========================================
   QHUN22 - Checkout Page JS
   ======================================== */

document.addEventListener('DOMContentLoaded', function () {

    /* ==================== Config ==================== */
    var BANK_ID = 'TCB';
    var ACCOUNT_NO = '22100588888888';
    var ACCOUNT_NAME = 'TRUONG QUANG HUY';
    var QR_TIMEOUT = 15 * 60; // 15 phút (giây)

    var totalAmount = window.QH_CHECKOUT_TOTAL || 0;
    var vietqrPaid = false;
    var qrTimerInterval = null;

    /* ==================== Elements ==================== */
    var payOpts = document.querySelectorAll('.qh-checkout-pay-opt:not(.disabled)');
    var payText = document.getElementById('checkoutPayText');
    var summaryPayMethod = document.getElementById('summaryPayMethod');
    var summaryTotalEl = document.querySelector('.qh-checkout-summary-row.total .qh-checkout-summary-val');

    // QR elements
    var qrBox = document.getElementById('vietqrBox');
    var qrContent = document.getElementById('vietqrContent');
    var qrSuccess = document.getElementById('vietqrSuccess');
    var qrImage = document.getElementById('vietqrImage');
    var qrAmount = document.getElementById('vietqrAmount');
    var qrCode = document.getElementById('vietqrCode');
    var qrTimer = document.getElementById('vietqrTimer');
    var qrConfirmBtn = document.getElementById('vietqrConfirmBtn');

    /* ==================== Helpers ==================== */
    function formatPrice(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + 'đ';
    }

    function generateTransferCode() {
        var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        var code = 'QH';
        for (var i = 0; i < 6; i++) {
            code += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return code;
    }

    function buildQrUrl(amount, transferCode) {
        return 'https://img.vietqr.io/image/' + BANK_ID + '-' + ACCOUNT_NO + '-vietqr_net_2.jpg'
            + '?amount=' + amount
            + '&addInfo=' + encodeURIComponent(transferCode)
            + '&accountName=' + encodeURIComponent(ACCOUNT_NAME);
    }

    /* ==================== Timer ==================== */
    function startTimer() {
        stopTimer();
        var remaining = QR_TIMEOUT;
        updateTimerDisplay(remaining);
        qrTimerInterval = setInterval(function () {
            remaining--;
            if (remaining <= 0) {
                stopTimer();
                // Hết thời gian
                if (!vietqrPaid) {
                    hideQrBox();
                    if (window.QHToast) {
                        QHToast.show('Hết thời gian thanh toán QR. Vui lòng thử lại.', 'error');
                    }
                }
                return;
            }
            updateTimerDisplay(remaining);
        }, 1000);
    }

    function stopTimer() {
        if (qrTimerInterval) {
            clearInterval(qrTimerInterval);
            qrTimerInterval = null;
        }
    }

    function updateTimerDisplay(seconds) {
        var m = Math.floor(seconds / 60);
        var s = seconds % 60;
        if (qrTimer) {
            qrTimer.textContent = (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
        }
    }

    /* ==================== QR Box ==================== */
    function showQrBox() {
        if (!qrBox) return;
        var transferCode = generateTransferCode();

        // Set QR image
        if (qrImage) {
            qrImage.src = buildQrUrl(totalAmount, transferCode);
        }
        // Set amount
        if (qrAmount) {
            qrAmount.textContent = formatPrice(totalAmount);
        }
        // Set transfer code
        if (qrCode) {
            qrCode.textContent = transferCode;
        }
        // Reset states
        if (qrContent) qrContent.style.display = '';
        if (qrSuccess) qrSuccess.style.display = 'none';
        vietqrPaid = false;

        qrBox.style.display = '';
        startTimer();
    }

    function hideQrBox() {
        if (qrBox) qrBox.style.display = 'none';
        stopTimer();
    }

    /* ==================== Payment Confirm ==================== */
    function confirmVietqrPayment() {
        vietqrPaid = true;
        stopTimer();

        // Hide QR content, show success
        if (qrContent) qrContent.style.display = 'none';
        if (qrSuccess) qrSuccess.style.display = '';

        // Add verified checkmark to VIETQR option
        var vietqrOpt = document.querySelector('[data-pay-type="vietqr"]');
        if (vietqrOpt) {
            vietqrOpt.classList.add('verified');
        }

        // Update summary total to 0đ
        if (summaryTotalEl) {
            summaryTotalEl.textContent = '0đ';
        }

        if (window.QHToast) {
            QHToast.show('Thanh toán chuyển khoản thành công!', 'success');
        }
    }

    if (qrConfirmBtn) {
        qrConfirmBtn.addEventListener('click', confirmVietqrPayment);
    }

    /* ==================== Payment Selection ==================== */
    function updatePaySelection(opt) {
        var label = opt.getAttribute('data-pay-label');
        if (payText && label) {
            payText.innerHTML = 'Bạn đang chọn hình thức thanh toán <strong>' + label + '</strong>';
        }
        var shortLabel = opt.getAttribute('data-pay-short');
        if (summaryPayMethod && shortLabel) {
            summaryPayMethod.textContent = shortLabel;
        }
    }

    payOpts.forEach(function (opt) {
        opt.addEventListener('click', function () {
            var payType = this.getAttribute('data-pay-type');

            // Deselect all, remove verified from non-paid
            document.querySelectorAll('.qh-checkout-pay-opt').forEach(function (o) {
                o.classList.remove('selected');
                // Only remove verified if not vietqr-paid
                if (o.getAttribute('data-pay-type') !== 'vietqr' || !vietqrPaid) {
                    o.classList.remove('verified');
                }
            });

            // Select this
            this.classList.add('selected');

            // COD → verified immediately, hide QR, restore total
            if (payType === 'cod') {
                this.classList.add('verified');
                hideQrBox();
                // Restore total if switching back from paid vietqr
                if (summaryTotalEl) {
                    summaryTotalEl.textContent = formatPrice(totalAmount);
                }
            }
            // VIETQR → show QR box, no verified yet
            else if (payType === 'vietqr') {
                if (vietqrPaid) {
                    // Already paid, re-show success, keep verified, total = 0
                    this.classList.add('verified');
                    if (qrBox) qrBox.style.display = '';
                    if (qrContent) qrContent.style.display = 'none';
                    if (qrSuccess) qrSuccess.style.display = '';
                    if (summaryTotalEl) summaryTotalEl.textContent = '0đ';
                } else {
                    showQrBox();
                    if (summaryTotalEl) {
                        summaryTotalEl.textContent = formatPrice(totalAmount);
                    }
                }
            }

            updatePaySelection(this);
        });
    });

    // Set default selection (COD)
    var defaultSelected = document.querySelector('.qh-checkout-pay-opt.selected');
    if (defaultSelected) {
        updatePaySelection(defaultSelected);
    }

    /* ==================== Place Order ==================== */
    var submitBtn = document.getElementById('checkoutSubmitBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function () {
            var selected = document.querySelector('.qh-checkout-pay-opt.selected');
            if (!selected) {
                if (window.QHToast) {
                    QHToast.show('Vui lòng chọn phương thức thanh toán', 'error');
                }
                return;
            }
            var payType = selected.getAttribute('data-pay-type');
            if (payType === 'vietqr' && !vietqrPaid) {
                if (window.QHToast) {
                    QHToast.show('Vui lòng hoàn tất thanh toán chuyển khoản trước khi đặt hàng', 'error');
                }
                return;
            }
            if (window.QHToast) {
                QHToast.show('Chức năng đặt hàng đang được phát triển!', 'error');
            }
        });
    }

});
