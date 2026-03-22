/**
 * product_detail_section.js
 * Quản lý phần "Chi tiết sản phẩm" hợp nhất với 6 tab dọc bên trái:
 *   1. Chi tiết sản phẩm (detail)
 *   2. SKU (sku)
 *   3. Thư mục (folder)
 *   4. Màu – Ảnh sản phẩm (color-image)
 *   5. Dung lượng (capacity)
 *   6. Thông tin sản phẩm (info)
 */

// ==================== State ====================
let pdCurrentProductId = null;
let pdCurrentDetailId = null;
let pdCurrentSkusWithColor = [];
let pdCapSelectedColors = [];
let pdCurrentHasSpec = false;
let pdColorImagePreviewImages = [];
let pdInfoEditorInstance = null;
let pdInfoEditorReady = false;

// ==================== Navigation ====================

function openProductDetailSection(productId, productName) {
    pdCurrentProductId = productId;
    pdCurrentDetailId = null;
    pdCurrentSkusWithColor = [];
    pdCapSelectedColors = [];
    pdCurrentHasSpec = false;
    pdColorImagePreviewImages = [];

    // Cập nhật tiêu đề
    const title = document.getElementById('pdSectionTitle');
    if (title) title.textContent = productName;

    // Chuyển sang section product-detail
    const url = new URL(window.location);
    url.searchParams.set('section', 'product-detail');
    window.history.pushState({}, '', url);

    // Ẩn tất cả section, hiển thị product-detail
    document.querySelectorAll('.da-main > div[id$="-section"]').forEach(function (el) {
        el.style.display = 'none';
    });
    var pdSection = document.getElementById('product-detail-section');
    if (pdSection) pdSection.style.display = 'block';

    // Cập nhật sidebar active
    document.querySelectorAll('.da-nav-item').forEach(function (item) {
        var sec = item.getAttribute('data-section');
        if (sec === 'products' || sec === 'product-detail') {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Mặc định mở tab "detail"
    switchPdTab('detail');

    // Tải dữ liệu cho tab detail
    loadPdDetail(productId);
}

function backToProductList() {
    pdCurrentProductId = null;
    pdCurrentDetailId = null;

    var url = new URL(window.location);
    url.searchParams.set('section', 'products');
    window.history.pushState({}, '', url);

    document.querySelectorAll('.da-main > div[id$="-section"]').forEach(function (el) {
        el.style.display = 'none';
    });
    var productsSection = document.getElementById('products-section');
    if (productsSection) productsSection.style.display = 'block';

    document.querySelectorAll('.da-nav-item').forEach(function (item) {
        var sec = item.getAttribute('data-section');
        item.classList.toggle('active', sec === 'products');
    });
}

// ==================== Tab Switching ====================

function resetPdTabState() {
    // --- Reset tất cả toggle history về trạng thái đóng ---
    var toggleIds = [
        { history: 'pdSkuHistory', btn: 'pdSkuToggleBtn', text: 'pdSkuToggleText', icon: 'pdSkuToggleIcon' },
        { history: 'pdFolderHistory', btn: 'pdFolderToggleBtn', text: 'pdFolderToggleText', icon: 'pdFolderToggleIcon' },
        { history: 'pdColorImageHistory', btn: 'pdColorImageToggleBtn', text: 'pdColorImageToggleText', icon: 'pdColorImageToggleIcon' },
        { history: 'pdCapVariantList', btn: 'pdCapToggleBtn', text: 'pdCapToggleText', icon: 'pdCapToggleIcon' }
    ];
    toggleIds.forEach(function (t) {
        var histEl = document.getElementById(t.history);
        var textEl = document.getElementById(t.text);
        var iconEl = document.getElementById(t.icon);
        if (histEl) histEl.style.display = 'none';
        if (textEl) textEl.textContent = 'Xem danh sách đã thêm';
        if (iconEl) iconEl.style.transform = '';
    });

    // --- Reset form tab Màu - Ảnh sản phẩm ---
    var colorFolderSel = document.getElementById('pdColorFolderSelect');
    var colorSkuSel = document.getElementById('pdColorSkuSelect');
    var colorNameInp = document.getElementById('pdColorNameInput');
    var colorFileName = document.getElementById('pdColorImageFileName');
    var colorFileInp = document.getElementById('pdColorImageFile');
    var colorPreviewGrid = document.getElementById('pdColorImagePreviewGrid');
    if (colorFolderSel) colorFolderSel.selectedIndex = 0;
    if (colorSkuSel) colorSkuSel.selectedIndex = 0;
    if (colorNameInp) colorNameInp.value = '';
    if (colorFileName) colorFileName.textContent = '';
    if (colorFileInp) colorFileInp.value = '';
    if (colorPreviewGrid) colorPreviewGrid.innerHTML = '';
    pdColorImagePreviewImages = [];
}

function switchPdTab(tabName) {
    // Reset UI state của tab trước
    resetPdTabState();

    // Toggle active trên tab buttons
    document.querySelectorAll('.pd-tab').forEach(function (el) {
        el.classList.toggle('active', el.getAttribute('data-pd-tab') === tabName);
    });
    // Toggle panels
    document.querySelectorAll('.pd-panel').forEach(function (el) {
        el.style.display = 'none';
    });
    var panel = document.getElementById('pdPanel-' + tabName);
    if (panel) panel.style.display = 'block';

    // Tải dữ liệu khi chuyển tab
    if (pdCurrentProductId) {
        if (tabName === 'detail') {
            loadPdDetail(pdCurrentProductId);
        } else if (tabName === 'sku') {
            loadPdSkuList();
        } else if (tabName === 'folder') {
            loadPdFolderList();
        } else if (tabName === 'color-image') {
            loadPdColorImageData();
        } else if (tabName === 'capacity') {
            loadPdCapacityData();
        } else if (tabName === 'info') {
            loadPdInfoData();
        }
    }
}

// ==================== TAB 1: Chi tiết sản phẩm ====================

function loadPdDetail(productId) {
    fetch('/products/detail/get/?product_id=' + productId, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                var nameEl = document.getElementById('pdDetailName');
                var stockEl = document.getElementById('pdDetailStock');
                if (nameEl) nameEl.textContent = data.product_name || '';
                if (stockEl) stockEl.value = data.product_stock || 0;
                pdCurrentDetailId = data.detail_id || null;

                // Save SKU+color list for capacity tab
                pdCurrentSkusWithColor = data.skus_with_color || [];

                // Load spec preview
                loadPdSpecPreview(data.spec_data);

                // Load YouTube preview
                loadPdYoutubePreview(data.youtube_id || '');
            }
        })
        .catch(function (err) {
            console.error('Error loading product detail:', err);
        });
}

// ---- Spec ----
function handlePdSpecFileChange(event) {
    var file = event.target.files[0];
    var el = document.getElementById('pdSpecFileName');
    if (!file) { if (el) el.textContent = ''; return; }
    if (!file.name.endsWith('.json')) {
        if (window.QHToast) window.QHToast.show('Chỉ chấp nhận file .json!', 'error');
        event.target.value = '';
        if (el) el.textContent = '';
        return;
    }
    if (el) el.textContent = file.name;
}

function uploadPdSpec() {
    var fileInput = document.getElementById('pdSpecFileInput');
    if (!fileInput || !fileInput.files.length) {
        if (window.QHToast) window.QHToast.show('Vui lòng chọn file JSON trước!', 'error');
        return;
    }
    if (!pdCurrentDetailId && !pdCurrentProductId) {
        if (window.QHToast) window.QHToast.show('Không xác định được sản phẩm!', 'error');
        return;
    }
    if (!pdCurrentDetailId) {
        if (window.QHToast) window.QHToast.show('Vui lòng "Lưu chi tiết" trước khi tải thông số!', 'error');
        return;
    }
    var file = fileInput.files[0];
    var fd = new FormData();
    fd.append('json_file', file);
    fd.append('detail_id', pdCurrentDetailId);

    fetch(window.specUploadUrl || '/products/specification/upload/', {
        method: 'POST',
        headers: { 'X-CSRFToken': window.csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: fd
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                if (window.QHToast) window.QHToast.show(data.message || 'Tải thành công!', 'success');
                loadPdSpecPreview(data.spec_data);
                fileInput.value = '';
                var fn = document.getElementById('pdSpecFileName');
                if (fn) fn.textContent = '';
            } else {
                if (window.QHToast) window.QHToast.show(data.message || 'Tải thất bại!', 'error');
            }
        })
        .catch(function () {
            if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error');
        });
}

function deletePdSpec() {
    if (!pdCurrentHasSpec) {
        if (window.QHToast) window.QHToast.show('Chưa có file JSON nào để xóa!', 'error');
        return;
    }
    if (!pdCurrentDetailId) {
        if (window.QHToast) window.QHToast.show('Không xác định được sản phẩm!', 'error');
        return;
    }
    function doDelete() {
        fetch(window.specDeleteUrl || '/products/specification/delete/', {
            method: 'POST',
            headers: { 'X-CSRFToken': window.csrfToken, 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'detail_id=' + pdCurrentDetailId
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    if (window.QHToast) window.QHToast.show(data.message || 'Đã xóa!', 'success');
                    loadPdSpecPreview(null);
                } else {
                    if (window.QHToast) window.QHToast.show(data.message || 'Xóa thất bại!', 'error');
                }
            })
            .catch(function () { if (window.QHToast) window.QHToast.show('Có lỗi!', 'error'); });
    }
    if (window.QHConfirm && window.QHConfirm.show) {
        window.QHConfirm.show('Bạn có chắc muốn xóa thông số kỹ thuật?', doDelete);
    } else {
        if (!confirm('Xóa thông số kỹ thuật?')) return;
        doDelete();
    }
}

function loadPdSpecPreview(specData) {
    var el = document.getElementById('pdSpecStatus');
    if (!el) return;
    if (specData && Object.keys(specData).length > 0) {
        pdCurrentHasSpec = true;
        el.textContent = 'Đã tải file JSON thông số kỹ thuật.';
        el.style.color = '#16a34a';
    } else {
        pdCurrentHasSpec = false;
        el.textContent = 'Bạn chưa tải file JSON nào.';
        el.style.color = '#9ca3af';
    }
}

// ---- YouTube ----
function savePdYoutubeId() {
    var input = document.getElementById('pdYoutubeId');
    var youtubeId = input ? input.value.trim() : '';
    if (!pdCurrentProductId) {
        if (window.QHToast) window.QHToast.show('Không xác định được sản phẩm!', 'error');
        return;
    }
    var fd = new FormData();
    fd.append('product_id', pdCurrentProductId);
    fd.append('youtube_id', youtubeId);

    fetch('/products/youtube/save/', {
        method: 'POST',
        headers: { 'X-CSRFToken': window.csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: fd
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                if (window.QHToast) window.QHToast.show(data.message || 'Đã lưu!', 'success');
                loadPdYoutubePreview(data.youtube_id);
            } else {
                if (window.QHToast) window.QHToast.show(data.message || 'Lưu thất bại!', 'error');
            }
        })
        .catch(function () { if (window.QHToast) window.QHToast.show('Có lỗi!', 'error'); });
}

function loadPdYoutubePreview(youtubeId) {
    var el = document.getElementById('pdYoutubeStatus');
    var input = document.getElementById('pdYoutubeId');
    if (!el) return;
    if (youtubeId) {
        el.innerHTML = 'Đã lưu: <a href="https://www.youtube.com/watch?v=' + encodeURIComponent(youtubeId) + '" target="_blank" rel="noopener noreferrer" style="color:#dc2626;text-decoration:underline;">' + youtubeId.replace(/</g, '&lt;') + '</a>';
        el.style.color = '#16a34a';
        if (input) input.value = youtubeId;
    } else {
        el.textContent = 'Chưa có video YouTube.';
        el.style.color = '#9ca3af';
        if (input) input.value = '';
    }
}

// ---- Save detail (stock) ----
function savePdDetail() {
    var stockEl = document.getElementById('pdDetailStock');
    var stock = stockEl ? stockEl.value : 0;
    var fd = new FormData();
    fd.append('product_id', pdCurrentProductId);
    fd.append('original_price', 0);
    fd.append('discount_percent', 0);
    fd.append('stock', stock);
    fd.append('description', '');

    fetch('/products/detail/save/', {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                pdCurrentDetailId = data.detail_id;
                if (window.QHToast) window.QHToast.show(data.message, 'success');
            } else {
                if (window.QHToast) window.QHToast.show(data.message, 'error');
            }
        })
        .catch(function () {
            if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error');
        });
}

// ==================== TAB 2: SKU ====================

function loadPdSkuList() {
    fetch('/products/sku/list/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                var allSkus = data.skus || [];
                var filtered = allSkus.filter(function (s) { return String(s.product_id) === String(pdCurrentProductId); });
                renderPdSkuTable(filtered);
            }
        })
        .catch(function (err) { console.error('Error loading SKU list:', err); });
}

function renderPdSkuTable(skus) {
    var tbody = document.getElementById('pdSkuTableBody');
    if (!tbody) return;
    if (!skus || skus.length === 0) {
        tbody.innerHTML = '<tr class="da-table-empty"><td colspan="4">Chưa có SKU nào.</td></tr>';
        return;
    }
    var html = '';
    skus.forEach(function (s, i) {
        var dateStr = '-';
        if (s.created_at) {
            var d = new Date(s.created_at);
            dateStr = d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
        }
        var skuEsc = (s.sku || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
        var skuHtml = (s.sku || '').replace(/</g, '&lt;');
        html += '<tr id="pdSkuRow_' + i + '"><td>' + (i + 1) + '</td><td id="pdSkuCell_' + i + '" style="font-weight:500;">' + skuHtml + '</td><td>' + dateStr + '</td>';
        html += '<td style="white-space:nowrap;"><button type="button" onclick="editPdSku(' + i + ', \'' + s.id + '\', \'' + skuEsc + '\')" class="da-btn da-btn-sm da-btn-info">Sửa</button> ';
        html += '<button type="button" onclick="deletePdSku(\'' + s.id + '\', \'' + skuEsc + '\')" class="da-btn da-btn-sm da-btn-del">Xóa</button></td></tr>';
    });
    tbody.innerHTML = html;
}

function editPdSku(rowIdx, compositeId, skuValue) {
    var cell = document.getElementById('pdSkuCell_' + rowIdx);
    if (!cell) return;
    var decoded = skuValue.replace(/&quot;/g, '"').replace(/\\'/g, "'");
    cell.innerHTML = '<input type="text" id="pdSkuEditInput_' + rowIdx + '" value="' + decoded.replace(/"/g, '&quot;') + '" style="width:100%;padding:6px 8px;border:1px solid #3b82f6;border-radius:4px;font-size:13px;font-family:inherit;box-sizing:border-box;" onkeydown="if(event.key===\'Enter\'){event.preventDefault();saveEditPdSku(' + rowIdx + ',\'' + compositeId + '\');}">';
    var input = document.getElementById('pdSkuEditInput_' + rowIdx);
    if (input) input.focus();
    // Replace action buttons
    var row = document.getElementById('pdSkuRow_' + rowIdx);
    if (row) {
        var actionCell = row.cells[3];
        actionCell.innerHTML = '<button type="button" onclick="saveEditPdSku(' + rowIdx + ',\'' + compositeId + '\')" class="da-btn da-btn-sm da-btn-success">Lưu</button> <button type="button" onclick="loadPdSkuList()" class="da-btn da-btn-sm da-btn-ghost">Hủy</button>';
    }
}

function saveEditPdSku(rowIdx, compositeId) {
    var input = document.getElementById('pdSkuEditInput_' + rowIdx);
    if (!input) return;
    var newSku = input.value.trim();
    if (!newSku) {
        if (window.QHToast) window.QHToast.show('SKU không được để trống!', 'error');
        return;
    }
    var fd = new FormData();
    fd.append('sku_id', compositeId);
    fd.append('sku', newSku);
    fetch('/products/sku/edit/', {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                if (window.QHToast) window.QHToast.show(data.message || 'Đã cập nhật!', 'success');
                loadPdSkuList();
            } else {
                if (window.QHToast) window.QHToast.show(data.message || 'Không thể cập nhật!', 'error');
            }
        })
        .catch(function () { if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error'); });
}

function savePdSku() {
    var input = document.getElementById('pdSkuInput');
    var sku = input ? input.value.trim() : '';
    if (!pdCurrentProductId) {
        if (window.QHToast) window.QHToast.show('Không xác định được sản phẩm.', 'error');
        return;
    }
    if (!sku) {
        if (window.QHToast) window.QHToast.show('Vui lòng nhập SKU!', 'error');
        return;
    }
    var fd = new FormData();
    fd.append('product_id', pdCurrentProductId);
    fd.append('sku', sku);

    fetch('/products/sku/add/', {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                if (window.QHToast) window.QHToast.show(data.message, 'success');
                if (input) input.value = '';
                loadPdSkuList();
            } else {
                if (window.QHToast) window.QHToast.show(data.message, 'error');
            }
        })
        .catch(function () { if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error'); });
}

function deletePdSku(compositeId, skuName) {
    var msg = 'Xóa SKU "' + skuName + '"?';
    function doDelete() {
        var fd = new FormData();
        fd.append('sku_id', compositeId);
        fetch('/products/sku/delete/', {
            method: 'POST',
            body: fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    if (window.QHToast) window.QHToast.show(data.message, 'success');
                    loadPdSkuList();
                } else {
                    if (window.QHToast) window.QHToast.show(data.message || 'Không thể xóa!', 'error');
                }
            })
            .catch(function () { if (window.QHToast) window.QHToast.show('Có lỗi!', 'error'); });
    }
    if (window.QHConfirm && window.QHConfirm.show) {
        window.QHConfirm.show(msg, doDelete);
    } else {
        if (!confirm(msg)) return;
        doDelete();
    }
}

function togglePdSkuHistory() {
    var el = document.getElementById('pdSkuHistory');
    var text = document.getElementById('pdSkuToggleText');
    var icon = document.getElementById('pdSkuToggleIcon');
    if (!el) return;
    var isHidden = el.style.display === 'none';
    el.style.display = isHidden ? 'block' : 'none';
    if (text) text.textContent = isHidden ? 'Đóng danh sách đã thêm' : 'Xem danh sách đã thêm';
    if (icon) icon.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
    if (isHidden) loadPdSkuList();
}

// ==================== TAB 3: Thư mục ====================

function loadPdFolderList() {
    fetch('/product-images/folders/list/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                var folders = (data.folders || []).filter(function (f) {
                    return String(f.product_id) === String(pdCurrentProductId);
                });
                renderPdFolderTable(folders);
            }
        })
        .catch(function (err) { console.error('Error loading folders:', err); });
}

function renderPdFolderTable(folders) {
    var tbody = document.getElementById('pdFolderTableBody');
    if (!tbody) return;
    if (!folders || folders.length === 0) {
        tbody.innerHTML = '<tr class="da-table-empty"><td colspan="3">Chưa có thư mục nào.</td></tr>';
        return;
    }
    var html = '';
    folders.forEach(function (f, i) {
        var nameEsc = (f.name || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        var nameJs = (f.name || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        html += '<tr id="pdFolderRow_' + i + '"><td>' + (i + 1) + '</td><td id="pdFolderCell_' + i + '" style="font-weight:500;">' + nameEsc + '</td>';
        html += '<td style="white-space:nowrap;"><button type="button" onclick="editPdFolder(' + i + ',' + f.id + ',\'' + nameJs + '\')" class="da-btn da-btn-sm da-btn-info">Sửa</button> ';
        html += '<button type="button" onclick="deletePdFolder(' + f.id + ', \'' + nameEsc.replace(/'/g, "\\'") + '\')" class="da-btn da-btn-sm da-btn-del">Xóa</button></td></tr>';
    });
    tbody.innerHTML = html;
}

function editPdFolder(rowIdx, folderId, folderName) {
    var cell = document.getElementById('pdFolderCell_' + rowIdx);
    if (!cell) return;
    var decoded = folderName.replace(/\\'/g, "'");
    cell.innerHTML = '<input type="text" id="pdFolderEditInput_' + rowIdx + '" value="' + decoded.replace(/"/g, '&quot;') + '" style="width:100%;padding:6px 8px;border:1px solid #3b82f6;border-radius:4px;font-size:13px;font-family:inherit;box-sizing:border-box;" onkeydown="if(event.key===\'Enter\'){event.preventDefault();saveEditPdFolder(' + rowIdx + ',' + folderId + ');}">';
    var input = document.getElementById('pdFolderEditInput_' + rowIdx);
    if (input) input.focus();
    var row = document.getElementById('pdFolderRow_' + rowIdx);
    if (row) {
        var actionCell = row.cells[2];
        actionCell.innerHTML = '<button type="button" onclick="saveEditPdFolder(' + rowIdx + ',' + folderId + ')" class="da-btn da-btn-sm da-btn-success">Lưu</button> <button type="button" onclick="loadPdFolderList()" class="da-btn da-btn-sm da-btn-ghost">Hủy</button>';
    }
}

function saveEditPdFolder(rowIdx, folderId) {
    var input = document.getElementById('pdFolderEditInput_' + rowIdx);
    if (!input) return;
    var newName = input.value.trim();
    if (!newName) {
        if (window.QHToast) window.QHToast.show('Tên thư mục không được để trống!', 'error');
        return;
    }
    var fd = new FormData();
    fd.append('folder_id', folderId);
    fd.append('name', newName);
    fetch('/product-images/folders/rename/', {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                if (window.QHToast) window.QHToast.show(data.message || 'Đã cập nhật!', 'success');
                loadPdFolderList();
            } else {
                if (window.QHToast) window.QHToast.show(data.message || 'Không thể cập nhật!', 'error');
            }
        })
        .catch(function () { if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error'); });
}

function savePdFolder() {
    var input = document.getElementById('pdFolderNameInput');
    var name = input ? input.value.trim() : '';
    if (!pdCurrentProductId) {
        if (window.QHToast) window.QHToast.show('Không xác định được sản phẩm.', 'error');
        return;
    }
    if (!name) {
        if (window.QHToast) window.QHToast.show('Vui lòng nhập tên thư mục!', 'error');
        return;
    }

    // Cần brand_id — lấy từ dữ liệu sản phẩm hiện tại
    // Fetch product info to get brand_id
    fetch('/products/list/json/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success) throw new Error('Không tải được danh sách sản phẩm');
            var product = (data.products || []).find(function (p) { return String(p.id) === String(pdCurrentProductId); });
            if (!product) throw new Error('Không tìm thấy sản phẩm');

            var fd = new FormData();
            fd.append('brand_id', product.brand_id || '');
            fd.append('product_id', pdCurrentProductId);
            fd.append('name', name);

            return fetch('/product-images/folders/create/', {
                method: 'POST',
                body: fd,
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
            });
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                if (window.QHToast) window.QHToast.show(data.message, 'success');
                if (input) input.value = '';
                loadPdFolderList();
            } else {
                if (window.QHToast) window.QHToast.show(data.message || 'Không thể tạo thư mục.', 'error');
            }
        })
        .catch(function (err) {
            console.error('Error creating folder:', err);
            if (window.QHToast) window.QHToast.show(err.message || 'Có lỗi xảy ra!', 'error');
        });
}

function deletePdFolder(folderId, folderName) {
    var msg = 'Xóa thư mục "' + folderName + '"? Tất cả ảnh trong thư mục sẽ bị xóa!';
    function doDelete() {
        var fd = new FormData();
        fd.append('folder_id', folderId);
        fetch('/product-images/folders/delete/', {
            method: 'POST',
            body: fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    if (window.QHToast) window.QHToast.show(data.message || 'Đã xóa!', 'success');
                    loadPdFolderList();
                } else {
                    if (window.QHToast) window.QHToast.show(data.message || 'Không thể xóa!', 'error');
                }
            })
            .catch(function () { if (window.QHToast) window.QHToast.show('Lỗi kết nối!', 'error'); });
    }
    if (window.QHConfirm && window.QHConfirm.show) {
        window.QHConfirm.show(msg, doDelete);
    } else {
        if (!confirm(msg)) return;
        doDelete();
    }
}

function togglePdFolderHistory() {
    var el = document.getElementById('pdFolderHistory');
    var text = document.getElementById('pdFolderToggleText');
    var icon = document.getElementById('pdFolderToggleIcon');
    if (!el) return;
    var isHidden = el.style.display === 'none';
    el.style.display = isHidden ? 'block' : 'none';
    if (text) text.textContent = isHidden ? 'Đóng danh sách đã thêm' : 'Xem danh sách đã thêm';
    if (icon) icon.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
    if (isHidden) loadPdFolderList();
}

// ==================== TAB 4: Màu - Ảnh sản phẩm ====================

function loadPdColorImageData() {
    // Load folders for this product + SKU list
    Promise.all([
        fetch('/product-images/folders/list/', { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } }).then(function (r) { return r.json(); }),
        fetch('/products/sku/list/', { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } }).then(function (r) { return r.json(); })
    ]).then(function (results) {
        var folderData = results[0];
        var skuData = results[1];

        // Populate folder dropdown
        var folderSelect = document.getElementById('pdColorFolderSelect');
        if (folderSelect && folderData.success) {
            var folders = (folderData.folders || []).filter(function (f) {
                return String(f.product_id) === String(pdCurrentProductId);
            });
            var html = '<option value="">-- Chọn thư mục --</option>';
            folders.forEach(function (f) {
                var label = f.product_name ? f.name + ' (' + f.product_name + ')' : f.name;
                html += '<option value="' + f.id + '">' + label.replace(/</g, '&lt;') + '</option>';
            });
            folderSelect.innerHTML = html;
        }

        // Populate SKU dropdown
        var skuSelect = document.getElementById('pdColorSkuSelect');
        if (skuSelect && skuData.success) {
            var skus = (skuData.skus || []).filter(function (s) { return String(s.product_id) === String(pdCurrentProductId); });
            var html = '<option value="">-- Chọn SKU --</option>';
            skus.forEach(function (s) {
                html += '<option value="' + (s.sku || '').replace(/"/g, '&quot;') + '">' + (s.sku || '').replace(/</g, '&lt;') + '</option>';
            });
            skuSelect.innerHTML = html;
        }

        // Load existing color image rows for history table
        if (folderData.success) {
            var rows = (folderData.rows || []).filter(function (r) {
                return String(r.folder_product_id) === String(pdCurrentProductId);
            });
            renderPdColorImageTable(rows);
        }
    }).catch(function (err) {
        console.error('Error loading color image data:', err);
    });
}

function renderPdColorImageTable(rows) {
    var tbody = document.getElementById('pdColorImageTableBody');
    if (!tbody) return;
    if (!rows || rows.length === 0) {
        tbody.innerHTML = '<tr class="da-table-empty"><td colspan="5">Chưa có ảnh nào.</td></tr>';
        return;
    }
    var html = '';
    rows.forEach(function (row, i) {
        var colorEsc = (row.color_name || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        var skuEsc = (row.sku || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        var folderEsc = (row.folder_name || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        var colorJs = (row.color_name || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        var skuJs = (row.sku || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        html += '<tr><td>' + (i + 1) + '</td><td>' + folderEsc + '</td><td>' + colorEsc + '</td><td>' + skuEsc + '</td>';
        html += '<td style="white-space:nowrap;"><button type="button" onclick="managePdColorImageRow(' + (row.folder_id || 'null') + ', \'' + skuJs + '\', \'' + colorJs + '\')" class="da-btn da-btn-sm da-btn-info">Quản lý</button> ';
        html += '<button type="button" onclick="deletePdColorImageRow(' + (row.folder_id || 'null') + ', \'' + skuJs + '\', \'' + colorJs + '\')" class="da-btn da-btn-sm da-btn-del">Xóa</button></td></tr>';
    });
    tbody.innerHTML = html;
}

function managePdColorImageRow(folderId, sku, colorName) {
    // Pre-fill the form dropdowns with this row's data
    var folderSelect = document.getElementById('pdColorFolderSelect');
    var skuSelect = document.getElementById('pdColorSkuSelect');
    var colorInput = document.getElementById('pdColorNameInput');
    if (folderSelect) folderSelect.value = String(folderId);
    if (skuSelect) skuSelect.value = sku;
    if (colorInput) colorInput.value = colorName;

    // Load existing images for this combination
    pdColorImagePreviewImages = [];
    fetch('/product-images/color/list/?folder_id=' + folderId + '&sku=' + encodeURIComponent(sku) + '&color_name=' + encodeURIComponent(colorName), {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success && data.images) {
                pdColorImagePreviewImages = data.images.map(function (img) { return { id: img.id, url: img.url }; });
            }
            renderPdColorImagePreview();
        })
        .catch(function () { renderPdColorImagePreview(); });

    // Scroll to the top of the tab panel
    var panel = document.getElementById('pdPanel-color-image');
    if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function handlePdColorImageFile(event) {
    var file = event.target.files[0];
    var el = document.getElementById('pdColorImageFileName');
    if (el) el.textContent = file ? file.name : '';
}

function uploadPdColorImage() {
    var folderSelect = document.getElementById('pdColorFolderSelect');
    var skuSelect = document.getElementById('pdColorSkuSelect');
    var colorInput = document.getElementById('pdColorNameInput');
    var fileInput = document.getElementById('pdColorImageFile');

    var folderId = folderSelect ? folderSelect.value : '';
    var sku = skuSelect ? skuSelect.value : '';
    var colorName = colorInput ? colorInput.value.trim() : '';
    var file = fileInput && fileInput.files ? fileInput.files[0] : null;

    if (!folderId || !sku || !colorName || !file) {
        if (window.QHToast) window.QHToast.show('Vui lòng chọn thư mục, SKU, nhập tên màu và chọn ảnh!', 'error');
        return;
    }

    var fd = new FormData();
    fd.append('folder_id', folderId);
    fd.append('sku', sku);
    fd.append('color_name', colorName);
    fd.append('image', file);

    fetch('/product-images/color/upload/', {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success && data.image) {
                pdColorImagePreviewImages.push({ id: data.image.id, url: data.image.url });
                renderPdColorImagePreview();
                if (window.QHToast) window.QHToast.show('Upload thành công!', 'success');
                if (fileInput) fileInput.value = '';
                var fn = document.getElementById('pdColorImageFileName');
                if (fn) fn.textContent = '';
                // Reload history
                loadPdColorImageData();
            } else {
                if (window.QHToast) window.QHToast.show(data.message || 'Không thể upload!', 'error');
            }
        })
        .catch(function () { if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error'); });
}

function renderPdColorImagePreview() {
    var grid = document.getElementById('pdColorImagePreviewGrid');
    if (!grid) return;
    if (!pdColorImagePreviewImages.length) {
        grid.innerHTML = '';
        return;
    }
    var html = '';
    pdColorImagePreviewImages.forEach(function (img, i) {
        html += '<div style="position:relative;">';
        html += '<img src="' + img.url + '" style="width:90px;height:90px;object-fit:cover;border-radius:6px;border:1px solid #e2e8f0;">';
        html += '<button type="button" onclick="deletePdColorImagePreview(' + img.id + ',' + i + ')" style="position:absolute;top:-6px;right:-6px;width:20px;height:20px;background:#dc2626;color:#fff;border:none;border-radius:50%;cursor:pointer;font-size:12px;line-height:20px;text-align:center;">×</button>';
        html += '</div>';
    });
    grid.innerHTML = html;
}

function deletePdColorImagePreview(imageId, index) {
    var fd = new FormData();
    fd.append('image_id', imageId);
    fetch('/product-images/color/delete/', {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                pdColorImagePreviewImages.splice(index, 1);
                renderPdColorImagePreview();
                if (window.QHToast) window.QHToast.show('Đã xóa ảnh.', 'success');
                loadPdColorImageData();
            } else {
                if (window.QHToast) window.QHToast.show(data.message || 'Không thể xóa!', 'error');
            }
        })
        .catch(function () { if (window.QHToast) window.QHToast.show('Có lỗi!', 'error'); });
}

function savePdColorImage() {
    if (window.QHToast) window.QHToast.show('Đã lưu.', 'success');
    pdColorImagePreviewImages = [];
    renderPdColorImagePreview();
}

function deletePdColorImageRow(folderId, sku, colorName) {
    if (!folderId || !sku || !colorName) {
        if (window.QHToast) window.QHToast.show('Thiếu thông tin!', 'error');
        return;
    }
    var msg = 'Xóa tất cả ảnh của màu "' + colorName + '" (SKU: ' + sku + ')?';
    function doDelete() {
        var fd = new FormData();
        fd.append('folder_id', folderId);
        fd.append('sku', sku);
        fd.append('color_name', colorName);
        fetch('/product-images/color/row-delete/', {
            method: 'POST',
            body: fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    if (window.QHToast) window.QHToast.show(data.message, 'success');
                    loadPdColorImageData();
                } else {
                    if (window.QHToast) window.QHToast.show(data.message || 'Không thể xóa!', 'error');
                }
            })
            .catch(function () { if (window.QHToast) window.QHToast.show('Lỗi kết nối!', 'error'); });
    }
    if (window.QHConfirm && window.QHConfirm.show) {
        window.QHConfirm.show(msg, doDelete);
    } else {
        if (!confirm(msg)) return;
        doDelete();
    }
}

function togglePdColorImageHistory() {
    var el = document.getElementById('pdColorImageHistory');
    var text = document.getElementById('pdColorImageToggleText');
    var icon = document.getElementById('pdColorImageToggleIcon');
    if (!el) return;
    var isHidden = el.style.display === 'none';
    el.style.display = isHidden ? 'block' : 'none';
    if (text) text.textContent = isHidden ? 'Đóng danh sách đã thêm' : 'Xem danh sách đã thêm';
    if (icon) icon.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
    if (isHidden) loadPdColorImageData();
}

// ==================== TAB 5: Dung lượng (Capacity / Variants) ====================

function loadPdCapacityData() {
    // Need detail + skus_with_color + variants
    fetch('/products/detail/get/?product_id=' + pdCurrentProductId, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                pdCurrentDetailId = data.detail_id || null;
                pdCurrentSkusWithColor = data.skus_with_color || [];
                populatePdCapColorOptions(pdCurrentSkusWithColor);
                renderPdCapVariants(data.variants || []);
            }
        })
        .catch(function (err) { console.error('Error loading capacity data:', err); });
}

function populatePdCapColorOptions(skusWithColor) {
    var container = document.getElementById('pdCapColorOptions');
    if (!container) return;
    pdCapSelectedColors = [];
    if (!skusWithColor || skusWithColor.length === 0) {
        container.innerHTML = '<span style="font-size:13px;color:#94a3b8;">Chưa có màu (SKU) nào.</span>';
        updatePdCapSelectedLabels();
        return;
    }
    var html = '';
    skusWithColor.forEach(function (s) {
        var rawSku = s.sku || '';
        var color = (s.color_name || '').trim();
        var label = color ? rawSku + ' - ' + color : rawSku;
        var skuEsc = rawSku.replace(/"/g, '&quot;');
        var labelEsc = label.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        var skuJs = rawSku.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        var labelJs = label.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        var colorJs = color.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        html += '<div class="pdc-color-option" data-sku="' + skuEsc + '" data-label="' + labelEsc + '" onclick="togglePdCapColorOption(\'' + skuJs + '\', \'' + labelJs + '\', \'' + colorJs + '\')">' + labelEsc + '</div>';
    });
    container.innerHTML = html;
    updatePdCapSelectedLabels();
}

function togglePdCapColorOption(sku, label, colorName) {
    var idx = pdCapSelectedColors.findIndex(function (x) { return x.sku === sku; });
    if (idx >= 0) {
        pdCapSelectedColors.splice(idx, 1);
    } else {
        pdCapSelectedColors.push({ sku: sku, label: label, color_name: colorName || '' });
    }
    updatePdCapSelectedLabels();
    var container = document.getElementById('pdCapColorOptions');
    if (container) {
        var box = container.querySelector('[data-sku="' + sku.replace(/"/g, '&quot;') + '"]');
        if (box) box.classList.toggle('selected', idx < 0);
    }
}

function updatePdCapSelectedLabels() {
    var el = document.getElementById('pdCapSelectedLabels');
    if (!el) return;
    if (!pdCapSelectedColors.length) {
        el.innerHTML = '<span style="font-size:11px;color:#9ca3af;">Chưa chọn màu nào.</span>';
        return;
    }
    var html = '';
    pdCapSelectedColors.forEach(function (x) {
        html += '<span style="font-size:11px;padding:4px 8px;border-radius:999px;background:#f1f5f9;color:#334155;border:1px solid #e2e8f0;">' + (x.label || x.sku) + '</span>';
    });
    el.innerHTML = html;
}

function calculatePdCapPrice() {
    var baseEl = document.getElementById('pdCapBasePrice');
    var discEl = document.getElementById('pdCapDiscount');
    var finalEl = document.getElementById('pdCapFinalPrice');
    if (!baseEl || !discEl || !finalEl) return 0;
    var orig = parseInt(baseEl.value) || 0;
    var disc = parseInt(discEl.value) || 0;
    var price = orig - (orig * disc / 100);
    if (price >= 5000) price = Math.round(price / 5000) * 5000;
    finalEl.value = price > 0 ? price.toLocaleString('vi-VN') + 'đ' : '';
    return price;
}

function addPdCapVariant() {
    if (!pdCurrentProductId) {
        if (window.QHToast) window.QHToast.show('Không xác định được sản phẩm.', 'error');
        return;
    }
    var storageEl = document.getElementById('pdCapStorage');
    var baseEl = document.getElementById('pdCapBasePrice');
    var discEl = document.getElementById('pdCapDiscount');
    if (!storageEl || !baseEl) return;

    var storage = storageEl.value.trim();
    var basePrice = baseEl.value.trim();
    var selected = pdCapSelectedColors.slice();

    if (!storage || !selected.length || !basePrice) {
        if (window.QHToast) window.QHToast.show('Vui lòng nhập đầy đủ: Dung lượng, ít nhất 1 màu (SKU) và giá gốc.', 'error');
        return;
    }

    var finalPrice = calculatePdCapPrice();
    if (!finalPrice || finalPrice <= 0) {
        if (window.QHToast) window.QHToast.show('Giá sau giảm không hợp lệ.', 'error');
        return;
    }
    var discountValue = discEl ? discEl.value : '0';

    var requests = selected.map(function (opt) {
        var colorName = opt.color_name || opt.label || opt.sku;
        var fd = new FormData();
        if (pdCurrentDetailId) fd.append('detail_id', pdCurrentDetailId);
        fd.append('product_id', pdCurrentProductId);
        fd.append('color_name', colorName);
        fd.append('color_hex', '');
        fd.append('storage', storage);
        fd.append('original_price', basePrice);
        fd.append('discount_percent', discountValue);
        fd.append('price', finalPrice);
        fd.append('sku', opt.sku);
        fd.append('stock_quantity', 0);
        return fetch('/products/variant/save/', {
            method: 'POST',
            body: fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(function (r) { return r.json(); });
    });

    Promise.all(requests).then(function (results) {
        var hasSuccess = results.some(function (d) { return d && d.success; });
        var hasError = results.some(function (d) { return d && d.success === false; });
        if (hasError) {
            results.forEach(function (d) {
                if (d && !d.success && window.QHToast) window.QHToast.show(d.message || 'Lỗi thêm biến thể.', 'error');
            });
        }
        if (hasSuccess) {
            if (window.QHToast) window.QHToast.show('Đã thêm dung lượng & màu.', 'success');
        }
        // Reset form
        storageEl.value = '';
        baseEl.value = '';
        if (discEl) discEl.value = 0;
        var finalEl = document.getElementById('pdCapFinalPrice');
        if (finalEl) finalEl.value = '';
        pdCapSelectedColors = [];
        var optsContainer = document.getElementById('pdCapColorOptions');
        if (optsContainer) optsContainer.querySelectorAll('.pdc-color-option').forEach(function (el) { el.classList.remove('selected'); });
        updatePdCapSelectedLabels();
        // Reload variants list
        loadPdCapacityData();
    }).catch(function () {
        if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error');
    });
}

function pdCapVariantDisplayLabel(v) {
    var sku = (v.sku || '').trim();
    var raw = (v.color_name || '').trim();
    if (!raw) return sku || '';
    var parts = raw.split(/\s*-\s*/).filter(Boolean);
    var colorOnly = parts.filter(function (p) { return p !== sku; }).join(' - ') || sku;
    return sku ? sku + ' - ' + colorOnly : raw;
}

function renderPdCapVariants(variants) {
    var container = document.getElementById('pdCapVariantsContainer');
    if (!container) return;
    if (!variants || variants.length === 0) {
        container.innerHTML = '<p style="color:#64748b;text-align:center;padding:20px;">Chưa có biến thể nào</p>';
        return;
    }
    // Group by storage
    var byStorage = {};
    variants.forEach(function (v) {
        var key = (v.storage || '').trim() || '(Trống)';
        if (!byStorage[key]) byStorage[key] = [];
        byStorage[key].push(v);
    });

    var html = '';
    Object.keys(byStorage).forEach(function (storage) {
        var group = byStorage[storage];
        var first = group[0];
        var orig = parseInt(first.original_price) || 0;
        var disc = parseInt(first.discount_percent) || 0;
        var price = parseInt(first.price) || 0;
        var variantsForSave = group.map(function (v) {
            return { id: v.id, sku: v.sku || '', color_name: pdCapVariantDisplayLabel(v) };
        });
        var variantIds = group.map(function (v) { return v.id; }).join(',');
        var variantsJsonEsc = JSON.stringify(variantsForSave).replace(/'/g, '&#39;');
        var colorsHtml = group.map(function (v) {
            var label = pdCapVariantDisplayLabel(v);
            return '<div class="vg-color-item">' + label.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>';
        }).join('');

        html += '<div class="variant-group" data-variant-ids="' + variantIds.replace(/"/g, '&quot;') + '" data-variants-json=\'' + variantsJsonEsc + '\'>';
        html += '<div class="vg-row">';
        html += '<div><label class="vg-label">Giá gốc</label><input type="number" class="vg-field variant-group-original-price" value="' + orig + '" min="0" data-group-variant-ids="' + variantIds.replace(/"/g, '&quot;') + '"></div>';
        html += '<div><label class="vg-label">Giá sau giảm</label><input type="text" class="vg-field variant-group-final-price" readonly value="' + price.toLocaleString('vi-VN') + 'đ" style="background:#f8fafc;color:#dc2626;font-weight:600;"></div>';
        html += '</div>';
        html += '<div class="vg-row">';
        html += '<div><label class="vg-label">Chọn màu</label><div class="vg-colors">' + colorsHtml + '</div></div>';
        html += '<div style="display:flex;flex-direction:column;gap:12px;">';
        html += '<div><label class="vg-label">Dung lượng</label><input type="text" class="vg-field variant-group-storage" value="' + (storage === '(Trống)' ? '' : storage).replace(/"/g, '&quot;') + '"></div>';
        html += '<div><label class="vg-label">% Giảm giá</label><input type="number" class="vg-field variant-group-discount-percent" value="' + disc + '" min="0" max="100" data-group-variant-ids="' + variantIds.replace(/"/g, '&quot;') + '"></div>';
        html += '</div></div>';
        html += '<div class="vg-footer"><button type="button" class="vg-delete" onclick="deletePdCapVariantGroup(this)" data-variant-ids="' + variantIds.replace(/"/g, '&quot;') + '">Xóa</button></div>';
        html += '</div>';
    });
    container.innerHTML = html;

    // Attach price recalculation
    container.querySelectorAll('.variant-group-original-price, .variant-group-discount-percent').forEach(function (el) {
        el.addEventListener('input', function () {
            var group = el.closest('.variant-group');
            if (group) calculatePdCapGroupPrice(group);
        });
    });
}

function calculatePdCapGroupPrice(groupEl) {
    var origEl = groupEl.querySelector('.variant-group-original-price');
    var discEl = groupEl.querySelector('.variant-group-discount-percent');
    var finalEl = groupEl.querySelector('.variant-group-final-price');
    if (!origEl || !discEl || !finalEl) return;
    var orig = parseInt(origEl.value) || 0;
    var disc = parseInt(discEl.value) || 0;
    var price = orig - (orig * disc / 100);
    if (price >= 5000) price = Math.round(price / 5000) * 5000;
    finalEl.value = price > 0 ? price.toLocaleString('vi-VN') + 'đ' : '';
}

function deletePdCapVariantGroup(btn) {
    var idsStr = btn.getAttribute('data-variant-ids') || '';
    var ids = idsStr.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    if (!ids.length) return;
    var msg = 'Xóa cả nhóm này (' + ids.length + ' màu)?';
    function doDelete() {
        var promises = ids.map(function (vid) {
            var fd = new FormData();
            fd.append('variant_id', vid);
            return fetch('/products/variant/delete/', {
                method: 'POST',
                body: fd,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            }).then(function (r) { return r.json(); });
        });
        Promise.all(promises).then(function () {
            if (window.QHToast) window.QHToast.show('Đã xóa nhóm biến thể.', 'success');
            loadPdCapacityData();
        }).catch(function () {
            if (window.QHToast) window.QHToast.show('Có lỗi khi xóa.', 'error');
        });
    }
    if (window.QHConfirm && window.QHConfirm.show) {
        window.QHConfirm.show(msg, doDelete);
    } else {
        if (!confirm(msg)) return;
        doDelete();
    }
}

function togglePdCapList() {
    var box = document.getElementById('pdCapVariantsList');
    var text = document.getElementById('pdCapToggleText');
    var icon = document.getElementById('pdCapToggleIcon');
    if (!box) return;
    var isHidden = box.style.display === 'none';
    box.style.display = isHidden ? 'block' : 'none';
    if (text) text.textContent = isHidden ? 'Đóng danh sách đã thêm' : 'Xem danh sách đã thêm';
    if (icon) icon.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
}

function savePdAllVariants() {
    var groups = document.querySelectorAll('#pdCapVariantsContainer .variant-group');
    if (!groups || groups.length === 0) {
        if (window.QHToast) window.QHToast.show('Chưa có biến thể nào để lưu.', 'error');
        return;
    }
    var promises = [];
    groups.forEach(function (group) {
        var variantsJson = group.getAttribute('data-variants-json');
        var storageEl = group.querySelector('.variant-group-storage');
        var origEl = group.querySelector('.variant-group-original-price');
        var discEl = group.querySelector('.variant-group-discount-percent');
        var finalEl = group.querySelector('.variant-group-final-price');
        if (!variantsJson || !storageEl) return;
        var list;
        try { list = JSON.parse(variantsJson); } catch (e) { return; }
        var storage = storageEl.value.trim();
        var originalPrice = origEl ? (origEl.value || '0') : '0';
        var discountPercent = discEl ? (discEl.value || '0') : '0';
        var finalStr = (finalEl && finalEl.value) ? finalEl.value.replace(/[^\d]/g, '') : '0';
        var price = parseInt(finalStr, 10) || 0;
        list.forEach(function (v) {
            var fd = new FormData();
            fd.append('variant_id', v.id);
            fd.append('detail_id', pdCurrentDetailId);
            fd.append('color_name', v.color_name || v.sku);
            fd.append('color_hex', '');
            fd.append('storage', storage);
            fd.append('original_price', originalPrice);
            fd.append('discount_percent', discountPercent);
            fd.append('price', price);
            fd.append('sku', v.sku || '');
            fd.append('stock_quantity', '0');
            promises.push(
                fetch('/products/variant/save/', { method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (!data.success && window.QHToast) window.QHToast.show(data.message || 'Lỗi cập nhật', 'error');
                    })
            );
        });
    });
    Promise.all(promises).then(function () {
        if (window.QHToast) window.QHToast.show('Đã lưu tất cả biến thể.', 'success');
        loadPdCapacityData();
    }).catch(function () {
        if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error');
    });
}

// ==================== TAB 6: Thông tin sản phẩm (Product Content) ====================

function loadPdInfoData() {
    // Load existing content for this product
    fetch('/product-content/list/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var contents = data.contents || [];
            var found = contents.find(function (c) { return String(c.product_id) === String(pdCurrentProductId); });
            initPdInfoEditor(found ? found.content_text : '', found ? found.id : null);
        })
        .catch(function (err) { console.error('Error loading product content:', err); });
}

var _pdInfoContentId = null;

function initPdInfoEditor(htmlContent, contentId) {
    _pdInfoContentId = contentId;
    var editorContainer = document.getElementById('pdInfoEditor');
    if (!editorContainer) return;

    // If CKEditor is available, use it
    if (pdInfoEditorInstance) {
        pdInfoEditorInstance.setData(htmlContent || '');
        return;
    }

    // Check if ClassicEditor is available (CKEditor 5)
    if (typeof ClassicEditor !== 'undefined') {
        ClassicEditor.create(editorContainer, {
            toolbar: ['heading', '|', 'bold', 'italic', 'link', '|', 'bulletedList', 'numberedList', '|', 'imageUpload', 'blockQuote', '|', 'undo', 'redo']
        }).then(function (editor) {
            pdInfoEditorInstance = editor;
            pdInfoEditorReady = true;
            editor.setData(htmlContent || '');
        }).catch(function (err) {
            console.error('CKEditor init error:', err);
            // Fallback to contenteditable div
            editorContainer.setAttribute('contenteditable', 'true');
            editorContainer.innerHTML = htmlContent || '';
        });
    } else {
        // Fallback: contenteditable div
        editorContainer.setAttribute('contenteditable', 'true');
        editorContainer.innerHTML = htmlContent || '';
    }
}

function savePdInfo() {
    if (!pdCurrentProductId) {
        if (window.QHToast) window.QHToast.show('Không xác định được sản phẩm!', 'error');
        return;
    }

    var contentText = '';
    if (pdInfoEditorInstance && pdInfoEditorReady) {
        contentText = pdInfoEditorInstance.getData();
    } else {
        var editable = document.getElementById('pdInfoEditor');
        contentText = editable ? editable.innerHTML : '';
    }

    // Need brand_id for API
    fetch('/products/list/json/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.success) throw new Error('Lỗi tải dữ liệu');
            var product = (data.products || []).find(function (p) { return String(p.id) === String(pdCurrentProductId); });
            if (!product) throw new Error('Không tìm thấy sản phẩm');

            var fd = new FormData();
            fd.append('brand_id', product.brand_id || '');
            fd.append('product_id', pdCurrentProductId);
            fd.append('content_text', contentText);

            return fetch('/product-content/add/', {
                method: 'POST',
                body: fd,
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': window.csrfToken }
            });
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                if (window.QHToast) window.QHToast.show('Lưu nội dung thành công!', 'success');
                if (data.content_id) _pdInfoContentId = data.content_id;
            } else {
                if (window.QHToast) window.QHToast.show(data.message || 'Lưu thất bại!', 'error');
            }
        })
        .catch(function (err) {
            console.error('Error saving product content:', err);
            if (window.QHToast) window.QHToast.show(err.message || 'Có lỗi xảy ra!', 'error');
        });
}
