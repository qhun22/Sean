/**
 * QHUN22 Mobile - Product Compare
 * Quản lý so sánh sản phẩm với localStorage
 */

const QHCompare = {
    MAX_ITEMS: 3,
    STORAGE_KEY: 'compareProducts',
    COLLAPSE_KEY: 'compareBarCollapsed',

    _isCollapsed() {
        return localStorage.getItem(this.COLLAPSE_KEY) === '1';
    },

    _setCollapsed(val) {
        localStorage.setItem(this.COLLAPSE_KEY, val ? '1' : '0');
    },

    getItems() {
        try {
            const data = localStorage.getItem(this.STORAGE_KEY);
            return data ? JSON.parse(data) : [];
        } catch {
            return [];
        }
    },

    saveItems(items) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(items));
    },

    addToCompare(id, name, image, price) {
        const items = this.getItems();

        if (items.find(item => item.id === id)) {
            if (window.QHToast) QHToast.show('Sản phẩm đã có trong danh sách so sánh', 'error');
            return false;
        }

        if (items.length >= this.MAX_ITEMS) {
            if (window.QHToast) QHToast.show('Chỉ được so sánh tối đa ' + this.MAX_ITEMS + ' sản phẩm', 'error');
            return false;
        }

        items.push({ id, name, image, price });
        this.saveItems(items);
        this._setCollapsed(false);
        this.renderCompareBar();
        this.updateButtons();

        if (window.QHToast) QHToast.show('Đã thêm vào so sánh', 'success');
        return true;
    },

    removeFromCompare(id) {
        let items = this.getItems();
        items = items.filter(item => item.id !== id);
        this.saveItems(items);
        this.renderCompareBar();
        this.updateButtons();
    },

    clearCompare() {
        localStorage.removeItem(this.STORAGE_KEY);
        this._setCollapsed(false);
        this.renderCompareBar();
        this.updateButtons();
    },

    goToCompare() {
        const items = this.getItems();
        if (items.length < 2) {
            if (window.QHToast) QHToast.show('Cần ít nhất 2 sản phẩm để so sánh', 'error');
            return;
        }
        const ids = items.map(item => item.id).join(',');
        window.location.href = '/compare/?ids=' + ids;
    },

    toggleBar() {
        const collapsed = this._isCollapsed();
        this._setCollapsed(!collapsed);
        this._applyBarState();
    },

    _applyBarState() {
        const bar = document.getElementById('qh-compare-bar');
        const fab = document.getElementById('qh-compare-fab');
        const items = this.getItems();

        if (items.length === 0) {
            if (bar) { bar.style.transform = 'translateY(100%)'; bar.style.opacity = '0'; bar.style.pointerEvents = 'none'; }
            if (fab) { fab.style.transform = 'scale(0)'; fab.style.opacity = '0'; fab.style.pointerEvents = 'none'; }
            return;
        }

        const collapsed = this._isCollapsed();

        if (collapsed) {
            if (bar) { bar.style.transform = 'translateY(100%)'; bar.style.opacity = '0'; bar.style.pointerEvents = 'none'; }
            if (fab) { fab.style.transform = 'scale(1)'; fab.style.opacity = '1'; fab.style.pointerEvents = 'auto'; }
        } else {
            if (bar) { bar.style.transform = 'translateY(0)'; bar.style.opacity = '1'; bar.style.pointerEvents = 'auto'; }
            if (fab) { fab.style.transform = 'scale(0)'; fab.style.opacity = '0'; fab.style.pointerEvents = 'none'; }
        }
    },

    truncateName(name, maxLen) {
        if (!name) return '';
        return name.length > maxLen ? name.substring(0, maxLen) + '...' : name;
    },

    updateButtons() {
        const items = this.getItems();
        const ids = items.map(i => i.id);
        document.querySelectorAll('.qh-compare-btn').forEach(btn => {
            const pid = parseInt(btn.getAttribute('data-product-id'));
            if (ids.includes(pid)) {
                btn.classList.add('active');
                btn.innerHTML = '<i class="ri-check-line"></i> Đang so sánh';
            } else {
                btn.classList.remove('active');
                btn.innerHTML = '<i class="ri-arrow-left-right-line"></i> So sánh';
            }
        });
    },

    renderCompareBar() {
        const items = this.getItems();
        const bar = document.getElementById('qh-compare-bar');
        const container = document.getElementById('qh-compare-items');
        const compareBtn = document.getElementById('qh-compare-go-btn');
        const countBadge = document.getElementById('qh-compare-fab-count');

        if (!bar || !container) return;

        if (countBadge) countBadge.textContent = items.length;

        if (compareBtn) {
            if (items.length >= 2) {
                compareBtn.disabled = false;
                compareBtn.style.opacity = '1';
                compareBtn.style.cursor = 'pointer';
            } else {
                compareBtn.disabled = true;
                compareBtn.style.opacity = '0.5';
                compareBtn.style.cursor = 'not-allowed';
            }
        }

        let html = '';
        items.forEach(item => {
            html += `
                <div class="qh-compare-bar-item">
                    <img src="${item.image}" alt="${this.truncateName(item.name, 20)}">
                    <div class="qh-compare-bar-item-info">
                        <div class="qh-compare-bar-item-name">${this.truncateName(item.name, 18)}</div>
                        <div class="qh-compare-bar-item-price">${item.price}</div>
                    </div>
                    <button class="qh-compare-bar-item-remove" onclick="event.stopPropagation();QHCompare.removeFromCompare(${item.id})">
                        <i class="ri-close-line"></i>
                    </button>
                </div>
            `;
        });

        for (let i = items.length; i < this.MAX_ITEMS; i++) {
            html += `<div class="qh-compare-bar-slot"><span>Trống</span></div>`;
        }

        container.innerHTML = html;
        this._applyBarState();
    },

    init() {
        this.renderCompareBar();
        this.updateButtons();
    }
};

window.QHCompare = QHCompare;

document.addEventListener('DOMContentLoaded', () => {
    QHCompare.init();
});
