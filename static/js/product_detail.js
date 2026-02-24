/**
 * Product Detail Management JS
 */

let currentProductId = null;
let currentDetailId = null;
let productSkusForDetail = [];
let currentSkusWithColor = [];
/** Màu (SKU) đã chọn trong form Thêm biến thể - click ô không cần Ctrl */
let variantSimpleSelectedColors = [];

function toggleVariantColorOption(sku, label) {
    const idx = variantSimpleSelectedColors.findIndex(function (x) { return x.sku === sku; });
    if (idx >= 0) {
        variantSimpleSelectedColors.splice(idx, 1);
    } else {
        variantSimpleSelectedColors.push({ sku: sku, label: label });
    }
    updateVariantSimpleSelectedLabels();
    // Update selected state on the box
    const container = document.getElementById('variantSimpleColorOptions');
    if (container) {
        const box = container.querySelector('[data-sku="' + sku.replace(/"/g, '&quot;') + '"]');
        if (box) box.classList.toggle('selected', idx < 0);
    }
}

function updateVariantSimpleSelectedLabels() {
    const container = document.getElementById('variantSimpleSelectedLabels');
    if (!container) return;
    if (!variantSimpleSelectedColors.length) {
        container.innerHTML = '<span style="font-size: 11px; color: #9ca3af;">Chưa chọn màu nào.</span>';
        return;
    }
    let html = '';
    variantSimpleSelectedColors.forEach(function (x) {
        html += '<span style="font-size: 11px; padding: 4px 8px; border-radius: 999px; background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0;">' + (x.label || x.sku) + '</span>';
    });
    container.innerHTML = html;
}

// ==================== Open/Close Modal ====================
function openProductDetailModal(productId, productName) {
    currentProductId = productId;
    
    // Show modal
    const modal = document.getElementById('productDetailModal');
    modal.style.display = 'flex';
    
    // Set product name
    document.getElementById('detailProductName').textContent = productName;
    
    // Load product detail data
    loadProductDetail(productId);

    // Reset simple variant form
    const storageInput = document.getElementById('variantSimpleStorage');
    const basePriceInput = document.getElementById('variantSimpleBasePrice');
    const discountInput = document.getElementById('variantSimpleDiscountPercent');
    const finalPriceInput = document.getElementById('variantSimpleFinalPrice');
    if (storageInput) storageInput.value = '';
    variantSimpleSelectedColors = [];
    updateVariantSimpleSelectedLabels();
    if (basePriceInput) basePriceInput.value = '';
    if (discountInput) discountInput.value = 0;
    if (finalPriceInput) finalPriceInput.value = '';

    // Danh sách ô "Chọn màu" được fill từ loadProductDetail (skus_with_color)
}

function closeProductDetailModal() {
    const modal = document.getElementById('productDetailModal');
    modal.style.display = 'none';
    currentProductId = null;
    currentDetailId = null;
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    const modal = document.getElementById('productDetailModal');
    if (modal && modal.style.display === 'flex' && e.target === modal) {
        closeProductDetailModal();
    }
});

// ==================== Load Product Detail ====================
function loadProductDetail(productId) {
    fetch(`/products/detail/get/?product_id=${productId}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const stockEl = document.getElementById('detailStock');
            if (stockEl) stockEl.value = data.product_stock || 0;
            currentDetailId = data.detail_id || null;
            
            // Lưu list SKU + màu để dùng cho cả dropdown trên và các dòng bên dưới
            currentSkusWithColor = data.skus_with_color || [];
            populateVariantSimpleColorSelectFromSkusWithColor(currentSkusWithColor);

            renderVariants(data.variants || []);
        }
    })
    .catch(error => {
        console.error('Error loading product detail:', error);
    });
}

// ==================== Simple Variant by Storage + Color (SKU) ====================
function loadProductSkusForDetail(productId) {
    const container = document.getElementById('variantSimpleColorOptions');
    if (!container) return;
    
    fetch('/products/sku/list/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            productSkusForDetail = (data.skus || []).filter(s => String(s.product_id) === String(productId));
            populateVariantSimpleColorSelect();
        }
    })
    .catch(error => {
        console.error('Error loading product SKUs for detail:', error);
    });
}

/** Render danh sách ô click "Chọn màu" (SKU - Màu), click để chọn nhiều không cần Ctrl */
function populateVariantSimpleColorSelectFromSkusWithColor(skusWithColor) {
    const container = document.getElementById('variantSimpleColorOptions');
    if (!container) return;
    variantSimpleSelectedColors = [];
    var list = skusWithColor || [];
    if (list.length === 0) {
        container.innerHTML = '<span style="font-size: 13px; color: #94a3b8;">Chưa có màu (SKU) nào.</span>';
        updateVariantSimpleSelectedLabels();
        return;
    }
    var html = '';
    list.forEach(function (s) {
        var rawSku = s.sku || '';
        var color = (s.color_name || '').trim();
        var label = color ? rawSku + ' - ' + color : rawSku;
        var skuEsc = rawSku.replace(/"/g, '&quot;');
        var labelEsc = label.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        var skuJs = rawSku.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        var labelJs = label.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        html += '<div class="variant-color-option" data-sku="' + skuEsc + '" data-label="' + labelEsc + '" onclick="toggleVariantColorOption(\'' + skuJs + '\', \'' + labelJs + '\')">' + labelEsc + '</div>';
    });
    container.innerHTML = html;
    updateVariantSimpleSelectedLabels();
}

function populateVariantSimpleColorSelect() {
    if (!currentSkusWithColor.length) {
        var list = productSkusForDetail.map(function (s) {
            var color = (s.color_name || '').trim();
            return { sku: s.sku, color_name: color };
        });
        populateVariantSimpleColorSelectFromSkusWithColor(list);
        return;
    }
    populateVariantSimpleColorSelectFromSkusWithColor(currentSkusWithColor);
}

function calculateVariantSimplePrice() {
    const baseEl = document.getElementById('variantSimpleBasePrice');
    const discountEl = document.getElementById('variantSimpleDiscountPercent');
    const finalEl = document.getElementById('variantSimpleFinalPrice');
    if (!baseEl || !discountEl || !finalEl) return 0;

    const originalPrice = parseInt(baseEl.value) || 0;
    const discountPercent = parseInt(discountEl.value) || 0;
    let discountedPrice = originalPrice - (originalPrice * discountPercent / 100);

    if (discountedPrice >= 5000) {
        discountedPrice = Math.round(discountedPrice / 5000) * 5000;
    }

    finalEl.value = discountedPrice > 0 ? discountedPrice.toLocaleString('vi-VN') + 'đ' : '';
    return discountedPrice;
}

function addVariantSimple() {
    if (!currentProductId) {
        if (window.QHToast) {
            window.QHToast.show('Không xác định được sản phẩm.', 'error');
        } else {
            alert('Không xác định được sản phẩm.');
        }
        return;
    }

    const storageEl = document.getElementById('variantSimpleStorage');
    const baseEl = document.getElementById('variantSimpleBasePrice');

    if (!storageEl || !baseEl) return;

    const storage = storageEl.value.trim();
    const basePrice = baseEl.value.trim();
    const selectedOptions = variantSimpleSelectedColors.slice();

    if (!storage || !selectedOptions.length || !basePrice) {
        if (window.QHToast) {
            window.QHToast.show('Vui lòng nhập đầy đủ: Dung lượng, ít nhất 1 màu (SKU) và giá gốc.', 'error');
        } else {
            alert('Vui lòng nhập đầy đủ: Dung lượng, ít nhất 1 màu (SKU) và giá gốc.');
        }
        return;
    }

    const finalPrice = calculateVariantSimplePrice();
    if (!finalPrice || finalPrice <= 0) {
        if (window.QHToast) {
            window.QHToast.show('Giá sau giảm không hợp lệ.', 'error');
        } else {
            alert('Giá sau giảm không hợp lệ.');
        }
        return;
    }

    const discountInput = document.getElementById('variantSimpleDiscountPercent');
    const discountValue = discountInput ? discountInput.value : '0';

    // Gửi 1 request cho mỗi SKU được chọn (từ danh sách ô click)
    const requests = selectedOptions.map(function (opt) {
        const sku = opt.sku;
        const colorName = opt.label || sku;
        const formData = new FormData();
        if (currentDetailId) {
            formData.append('detail_id', currentDetailId);
        }
        formData.append('product_id', currentProductId);
        formData.append('color_name', colorName);
        formData.append('color_hex', '');
        formData.append('storage', storage);
        formData.append('original_price', baseEl.value.trim());
        formData.append('discount_percent', discountValue);
        formData.append('price', finalPrice);
        formData.append('sku', sku);
        formData.append('stock_quantity', 0);
        return fetch('/products/variant/save/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(function (response) { return response.json(); });
    });

    Promise.all(requests)
        .then(function (results) {
            let hasSuccess = false;
            let hasError = false;
            results.forEach(function (data) {
                if (data && data.success) {
                    hasSuccess = true;
                } else if (data && data.success === false) {
                    hasError = true;
                    if (window.QHToast) {
                        window.QHToast.show(data.message || 'Không thể thêm một số biến thể.', 'error');
                    }
                }
            });
            if (hasSuccess) {
                if (window.QHToast) {
                    window.QHToast.show('Đã thêm dung lượng & nhiều màu (SKU).', 'success');
                } else {
                    alert('Đã thêm dung lượng & nhiều màu (SKU).');
                }
            }
            // Clear fields for next entry
            storageEl.value = '';
            baseEl.value = '';
            if (discountInput) discountInput.value = 0;
            const finalEl = document.getElementById('variantSimpleFinalPrice');
            if (finalEl) finalEl.value = '';
            variantSimpleSelectedColors = [];
            const optsContainer = document.getElementById('variantSimpleColorOptions');
            if (optsContainer) {
                optsContainer.querySelectorAll('.variant-color-option').forEach(function (el) { el.classList.remove('selected'); });
            }
            updateVariantSimpleSelectedLabels();

            // Reload variants list so admin thấy ngay dòng mới
            loadProductDetail(currentProductId);
        })
        .catch(function (error) {
            console.error('Error saving simple variant:', error);
            if (window.QHToast) {
                window.QHToast.show('Có lỗi xảy ra khi thêm biến thể!', 'error');
            } else {
                alert('Có lỗi xảy ra khi thêm biến thể!');
            }
        });
}

/** Lưu tất cả block biến thể (mỗi block = 1 dung lượng + nhiều màu) */
function saveAllVariantRows() {
    const groups = document.querySelectorAll('.variant-group');
    if (!groups || groups.length === 0) return Promise.resolve();
    const promises = [];
    groups.forEach(function (group) {
        const variantsJson = group.getAttribute('data-variants-json');
        const storageEl = group.querySelector('.variant-group-storage');
        const origEl = group.querySelector('.variant-group-original-price');
        const discEl = group.querySelector('.variant-group-discount-percent');
        const finalEl = group.querySelector('.variant-group-final-price');
        if (!variantsJson || !storageEl) return;
        let list;
        try {
            list = JSON.parse(variantsJson);
        } catch (e) {
            return;
        }
        const storage = storageEl.value.trim();
        const originalPrice = origEl ? (origEl.value || '0') : '0';
        const discountPercent = discEl ? (discEl.value || '0') : '0';
        const finalStr = (finalEl && finalEl.value) ? finalEl.value.replace(/[^\d]/g, '') : '0';
        const price = parseInt(finalStr, 10) || 0;
        list.forEach(function (v) {
            const formData = new FormData();
            formData.append('variant_id', v.id);
            formData.append('detail_id', currentDetailId);
            formData.append('color_name', v.color_name || v.sku);
            formData.append('color_hex', '');
            formData.append('storage', storage);
            formData.append('original_price', originalPrice);
            formData.append('discount_percent', discountPercent);
            formData.append('price', price);
            formData.append('sku', v.sku || '');
            formData.append('stock_quantity', '0');
            promises.push(
                fetch('/products/variant/save/', { method: 'POST', body: formData, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (!data.success && window.QHToast) window.QHToast.show(data.message || 'Lỗi cập nhật biến thể', 'error');
                    })
            );
        });
    });
    return Promise.all(promises);
}

// ==================== Save Product Detail ====================
function saveProductDetail() {
    const stockEl = document.getElementById('detailStock');
    const stock = stockEl ? stockEl.value : 0;
    const description = document.getElementById('detailDescription') ? document.getElementById('detailDescription').value : '';
    
    // Trước tiên lưu từng dòng biến thể (giá gốc, % giảm, giá sau giảm)
    saveAllVariantRows().then(function () {
        const formData = new FormData();
        formData.append('product_id', currentProductId);
        formData.append('original_price', 0);
        formData.append('discount_percent', 0);
        formData.append('stock', stock);
        formData.append('description', description);
        
        fetch('/products/detail/save/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentDetailId = data.detail_id;
                if (window.QHToast) {
                    window.QHToast.show(data.message, 'success');
                } else {
                    alert(data.message);
                }
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                if (window.QHToast) {
                    window.QHToast.show(data.message, 'error');
                } else {
                    alert(data.message);
                }
            }
        })
        .catch(error => {
            console.error('Error saving product detail:', error);
            if (window.QHToast) {
                window.QHToast.show('Có lỗi xảy ra!', 'error');
            } else {
                alert('Có lỗi xảy ra!');
            }
        });
    });
}

// Hiển thị đúng 1 mã SKU + tên màu (bỏ phần lặp SKU trong color_name từ API)
function variantDisplayLabel(v) {
    var sku = (v.sku || '').trim();
    var raw = (v.color_name || '').trim();
    if (!raw) return sku || '';
    var parts = raw.split(/\s*-\s*/).filter(Boolean);
    var colorOnly = parts.filter(function (p) { return p !== sku; }).join(' - ') || sku;
    return (sku ? sku + ' - ' + colorOnly : raw);
}

// ==================== Variants Management (gộp theo dung lượng: 1 block = 1 dung lượng + nhiều màu) ====================
function renderVariants(variants) {
    const container = document.getElementById('variantsList');
    if (!container) return;

    if (!variants || variants.length === 0) {
        container.innerHTML = '<p style="color: #64748b; text-align: center; padding: 20px;">Chưa có biến thể nào</p>';
        return;
    }

    // Gộp theo storage (dung lượng)
    const byStorage = {};
    variants.forEach(function (v) {
        const key = (v.storage || '').trim() || '(Trống)';
        if (!byStorage[key]) byStorage[key] = [];
        byStorage[key].push(v);
    });

    let html = '';
    Object.keys(byStorage).forEach(function (storage) {
        const group = byStorage[storage];
        const first = group[0];
        const orig = parseInt(first.original_price) || 0;
        const disc = parseInt(first.discount_percent) || 0;
        const price = parseInt(first.price) || 0;
        const variantsForSave = group.map(function (v) {
            var displayLabel = variantDisplayLabel(v);
            return { id: v.id, sku: v.sku || '', color_name: displayLabel };
        });
        const variantIds = group.map(function (v) { return v.id; }).join(',');
        const variantsJsonEscaped = JSON.stringify(variantsForSave).replace(/'/g, '&#39;');
        const colorsHtml = group.map(function (v) {
            const label = variantDisplayLabel(v);
            return '<div class="vg-color-item">' + (label.replace(/</g, '&lt;').replace(/>/g, '&gt;')) + '</div>';
        }).join('');

        html += '<div class="variant-group" data-variant-ids="' + variantIds.replace(/"/g, '&quot;') + '" data-variants-json=\'' + variantsJsonEscaped + '\'>';
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
        html += '<div class="vg-footer"><button type="button" class="vg-delete" onclick="deleteVariantGroup(this)" data-variant-ids="' + variantIds.replace(/"/g, '&quot;') + '">Xóa</button></div>';
        html += '</div>';
    });
    container.innerHTML = html;

    // Gắn oninput cho giá gốc và % giảm để tính lại giá sau giảm trong từng block
    container.querySelectorAll('.variant-group-original-price, .variant-group-discount-percent').forEach(function (el) {
        el.addEventListener('input', function () {
            const group = el.closest('.variant-group');
            if (!group) return;
            const ids = (el.getAttribute('data-group-variant-ids') || group.getAttribute('data-variant-ids') || '').split(',');
            if (ids.length && ids[0]) calculateVariantGroupPrice(group);
        });
    });
}

function calculateVariantGroupPrice(groupEl) {
    const origEl = groupEl.querySelector('.variant-group-original-price');
    const discEl = groupEl.querySelector('.variant-group-discount-percent');
    const finalEl = groupEl.querySelector('.variant-group-final-price');
    if (!origEl || !discEl || !finalEl) return;
    const originalPrice = parseInt(origEl.value) || 0;
    const discountPercent = parseInt(discEl.value) || 0;
    let discountedPrice = originalPrice - (originalPrice * discountPercent / 100);
    if (discountedPrice >= 5000) discountedPrice = Math.round(discountedPrice / 5000) * 5000;
    finalEl.value = discountedPrice > 0 ? discountedPrice.toLocaleString('vi-VN') + 'đ' : '';
}

/** Tính giá sau giảm cho 1 dòng biến thể (giống calculateVariantSimplePrice) */
function calculateVariantRowPrice(variantId) {
    const row = document.querySelector('.variant-row[data-variant-id="' + variantId + '"]');
    if (!row) return;
    const baseEl = row.querySelector('.variant-original-price');
    const discountEl = row.querySelector('.variant-discount-percent');
    const finalEl = row.querySelector('.variant-final-price');
    if (!baseEl || !discountEl || !finalEl) return;
    const originalPrice = parseInt(baseEl.value) || 0;
    const discountPercent = parseInt(discountEl.value) || 0;
    let discountedPrice = originalPrice - (originalPrice * discountPercent / 100);
    if (discountedPrice >= 5000) {
        discountedPrice = Math.round(discountedPrice / 5000) * 5000;
    }
    finalEl.value = discountedPrice > 0 ? discountedPrice.toLocaleString('vi-VN') + 'đ' : '';
}

function openAddVariantForm() {
    if (!currentDetailId) {
        alert('Vui lòng lưu thông tin chi tiết sản phẩm trước!');
        return;
    }
    
    document.getElementById('variantFormTitle').textContent = 'Thêm biến thể mới';
    document.getElementById('variantId').value = '';
    document.getElementById('variantColorName').value = '';
    document.getElementById('variantColorHex').value = '';
    document.getElementById('variantStorage').value = '';
    document.getElementById('variantPrice').value = '';
    document.getElementById('variantSku').value = '';
    document.getElementById('variantStock').value = '';
    
    document.getElementById('variantFormSection').style.display = 'block';
}

function editVariant(id, colorName, colorHex, storage, price, sku, stock) {
    document.getElementById('variantFormTitle').textContent = 'Sửa biến thể';
    document.getElementById('variantId').value = id;
    document.getElementById('variantColorName').value = colorName;
    document.getElementById('variantColorHex').value = colorHex;
    document.getElementById('variantStorage').value = storage;
    document.getElementById('variantPrice').value = price;
    document.getElementById('variantSku').value = sku;
    document.getElementById('variantStock').value = stock;
    
    document.getElementById('variantFormSection').style.display = 'block';
}

function closeVariantForm() {
    document.getElementById('variantFormSection').style.display = 'none';
}

function saveVariant() {
    if (!currentDetailId) {
        alert('Vui lòng lưu thông tin chi tiết sản phẩm trước!');
        return;
    }
    
    const variantId = document.getElementById('variantId').value;
    const colorName = document.getElementById('variantColorName').value;
    const colorHex = document.getElementById('variantColorHex').value;
    const storage = document.getElementById('variantStorage').value;
    const price = document.getElementById('variantPrice').value;
    const sku = document.getElementById('variantSku').value;
    const stock = document.getElementById('variantStock').value;
    
    if (!colorName || !storage || !price) {
        alert('Vui lòng nhập đầy đủ thông tin!');
        return;
    }
    
    const formData = new FormData();
    if (variantId) {
        formData.append('variant_id', variantId);
    }
    formData.append('detail_id', currentDetailId);
    formData.append('color_name', colorName);
    formData.append('color_hex', colorHex);
    formData.append('storage', storage);
    formData.append('price', price);
    formData.append('sku', sku);
    formData.append('stock_quantity', stock || 0);
    
    fetch('/products/variant/save/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            closeVariantForm();
            loadProductDetail(currentProductId);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error saving variant:', error);
        alert('Có lỗi xảy ra!');
    });
}

/** Xóa cả nhóm biến thể (1 dung lượng + nhiều màu) — dùng QHConfirm của hệ thống */
function deleteVariantGroup(btn) {
    const idsStr = btn.getAttribute('data-variant-ids') || '';
    const ids = idsStr.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    if (!ids.length) return;
    const n = ids.length;
    const message = 'Xóa cả nhóm này (' + n + ' màu)?';
    if (window.QHConfirm && typeof window.QHConfirm.show === 'function') {
        window.QHConfirm.show(message, function () {
            doDeleteVariantGroup(ids);
        });
    } else {
        if (!confirm(message)) return;
        doDeleteVariantGroup(ids);
    }
}
function doDeleteVariantGroup(ids) {
    const deleteOne = function (variantId) {
        const fd = new FormData();
        fd.append('variant_id', variantId);
        return fetch('/products/variant/delete/', {
            method: 'POST',
            body: fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(function (r) { return r.json(); });
    };
    Promise.all(ids.map(deleteOne)).then(function () {
        if (window.QHToast) window.QHToast.show('Đã xóa nhóm biến thể.', 'success');
        else alert('Đã xóa nhóm biến thể.');
        loadProductDetail(currentProductId);
    }).catch(function (err) {
        console.error(err);
        if (window.QHToast) window.QHToast.show('Có lỗi khi xóa.', 'error');
        else alert('Có lỗi khi xóa.');
    });
}

function deleteVariant(id, name) {
    const message = 'Bạn có chắc muốn xóa biến thể "' + (name || 'này') + '"?';
    function doDelete() {
        const formData = new FormData();
        formData.append('variant_id', id);
        fetch('/products/variant/delete/', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (window.QHToast) window.QHToast.show(data.message, 'success');
                else alert(data.message);
                loadProductDetail(currentProductId);
            } else {
                if (window.QHToast) window.QHToast.show(data.message, 'error');
                else alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error deleting variant:', error);
            if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error');
            else alert('Có lỗi xảy ra!');
        });
    }
    if (window.QHConfirm && typeof window.QHConfirm.show === 'function') {
        window.QHConfirm.show(message, doDelete);
    } else {
        if (!confirm(message)) return;
        doDelete();
    }
}

// ==================== Image Management ====================
function renderDetailImages(images, variantImages, productName) {
    const container = document.getElementById('detailImagesList');
    
    let html = '';
    
    // Cover images
    const coverImages = images.filter(img => img.image_type === 'cover');
    if (coverImages.length > 0) {
        html += '<div style="margin-bottom: 20px;"><h4 style="margin-bottom: 10px;">Ảnh đại diện</h4><div style="display: flex; flex-wrap: wrap; gap: 10px;">';
        coverImages.forEach(img => {
            html += `
            <div style="position: relative;">
                <img src="${img.image}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px;">
                <button onclick="deleteProductImage(${img.id})" style="position: absolute; top: -8px; right: -8px; background: #dc2626; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer;">×</button>
            </div>`;
        });
        html += '</div></div>';
    }
    
    // Variant images grouped by color
    const colors = [...new Set(variantImages.map(vi => vi.color_name))];
    colors.forEach(color => {
        const colorImages = variantImages.filter(vi => vi.color_name === color);
        html += `<div style="margin-bottom: 20px;"><h4 style="margin-bottom: 10px;">Màu: ${color}</h4><div style="display: flex; flex-wrap: wrap; gap: 10px;">`;
        colorImages.forEach(img => {
            html += `
            <div style="position: relative;">
                <img src="${img.image}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">
                <button onclick="deleteProductImage(${img.id})" style="position: absolute; top: -8px; right: -8px; background: #dc2626; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer;">×</button>
            </div>`;
        });
        html += '</div></div>';
    });
    
    if (!html) {
        html = '<p style="color: #64748b; text-align: center; padding: 20px;">Chưa có ảnh nào</p>';
    }
    
    container.innerHTML = html;
}

function openUploadImageForm(imageType, variantId = null) {
    if (!currentDetailId && !variantId) {
        alert('Vui lòng lưu thông tin chi tiết sản phẩm trước!');
        return;
    }
    
    document.getElementById('uploadImageType').value = imageType;
    document.getElementById('uploadVariantId').value = variantId || '';
    document.getElementById('uploadImageSection').style.display = 'block';
}

function closeUploadImageForm() {
    document.getElementById('uploadImageSection').style.display = 'none';
}

function uploadProductImages() {
    const imageType = document.getElementById('uploadImageType').value;
    const variantId = document.getElementById('uploadVariantId').value;
    const files = document.getElementById('uploadImageFiles').files;
    
    if (files.length === 0) {
        alert('Vui lòng chọn ảnh!');
        return;
    }
    
    const formData = new FormData();
    formData.append('image_type', imageType);
    if (variantId) {
        formData.append('variant_id', variantId);
    } else {
        formData.append('detail_id', currentDetailId);
    }
    
    for (let i = 0; i < files.length; i++) {
        formData.append('images', files[i]);
    }
    
    fetch('/products/image/upload/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            closeUploadImageForm();
            loadProductDetail(currentProductId);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error uploading images:', error);
        alert('Có lỗi xảy ra!');
    });
}

function deleteProductImage(imageId) {
    function doDelete() {
        const formData = new FormData();
        formData.append('image_id', imageId);
        fetch('/products/image/delete/', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (window.QHToast) window.QHToast.show(data.message, 'success');
                else alert(data.message);
                loadProductDetail(currentProductId);
            } else {
                if (window.QHToast) window.QHToast.show(data.message, 'error');
                else alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error deleting image:', error);
            if (window.QHToast) window.QHToast.show('Có lỗi xảy ra!', 'error');
            else alert('Có lỗi xảy ra!');
        });
    }
    if (window.QHConfirm && typeof window.QHConfirm.show === 'function') {
        window.QHConfirm.show('Bạn có chắc muốn xóa ảnh này?', doDelete);
    } else {
        if (!confirm('Bạn có chắc muốn xóa ảnh này?')) return;
        doDelete();
    }
}

// ==================== Product Images Functions ====================
function openAddProductImageModal() {
    // Placeholder - will be implemented
    alert('Tính năng đang được phát triển!');
}

function loadProductImages(productId) {
    // Placeholder - will be implemented
    console.log('Loading images for product:', productId);
}
