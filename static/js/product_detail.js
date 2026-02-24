/**
 * Product Detail Management JS
 */

let currentProductId = null;
let currentDetailId = null;

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
}

function closeProductDetailModal() {
    const modal = document.getElementById('productDetailModal');
    modal.style.display = 'none';
    currentProductId = null;
    currentDetailId = null;
}

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
            // Set basic info from Product model
            document.getElementById('detailOriginalPrice').value = data.product_original_price || 0;
            document.getElementById('detailDiscountPercent').value = data.product_discount_percent || 0;
            document.getElementById('detailStock').value = data.product_stock || 0;
            
            // Calculate discounted price
            calculateDetailDiscountedPrice();
            
            // Render SKU list
            renderSkuList(data.product_sku || '');
        }
    })
    .catch(error => {
        console.error('Error loading product detail:', error);
    });
}

// ==================== Price Calculation ====================
function calculateDetailDiscountedPrice() {
    const originalPrice = parseInt(document.getElementById('detailOriginalPrice').value) || 0;
    const discountPercent = parseInt(document.getElementById('detailDiscountPercent').value) || 0;
    
    let discountedPrice = originalPrice - (originalPrice * discountPercent / 100);
    
    // Round to nearest 5000 (only allow 5000 or 10000 ending)
    if (discountedPrice >= 5000) {
        discountedPrice = Math.round(discountedPrice / 5000) * 5000;
    }
    
    document.getElementById('detailDiscountedPrice').value = discountedPrice.toLocaleString('vi-VN') + 'đ';
}

// ==================== SKU Functions ====================
function renderSkuList(sku) {
    const skuListEl = document.getElementById('skuList');
    if (!sku) {
        skuListEl.innerHTML = '<p style="padding: 12px; color: #64748b; font-size: 13px; text-align: center;">Chưa có SKU</p>';
        return;
    }
    
    skuListEl.innerHTML = `
        <div style="padding: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9;">
            <span style="font-weight: 500; color: #1e293b;">${sku}</span>
            <button onclick="deleteSku('${sku}')" style="padding: 4px 10px; background: #fee2e2; color: #dc2626; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Xóa</button>
        </div>
    `;
}

function saveSkuOnly() {
    const sku = document.getElementById('detailSku').value.trim();
    if (!sku) {
        alert('Vui lòng nhập SKU!');
        return;
    }
    
    const formData = new FormData();
    formData.append('product_id', currentProductId);
    formData.append('sku', sku);
    formData.append('save_sku_only', 'true');
    
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
            alert(data.message);
            document.getElementById('detailSku').value = '';
            renderSkuList(data.sku);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error saving SKU:', error);
        alert('Có lỗi xảy ra!');
    });
}

function deleteSku(sku) {
    if (!confirm('Xóa SKU này?')) return;
    
    const formData = new FormData();
    formData.append('product_id', currentProductId);
    formData.append('delete_sku', 'true');
    formData.append('sku', sku);
    
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
            alert(data.message);
            renderSkuList(data.sku);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting SKU:', error);
    });
}

// ==================== Save Product Detail ====================
function saveProductDetail() {
    const originalPrice = document.getElementById('detailOriginalPrice').value;
    const discountPercent = document.getElementById('detailDiscountPercent').value;
    const sku = document.getElementById('detailSku').value;
    const stock = document.getElementById('detailStock').value;
    const description = document.getElementById('detailDescription') ? document.getElementById('detailDescription').value : '';
    
    const formData = new FormData();
    formData.append('product_id', currentProductId);
    formData.append('original_price', originalPrice);
    formData.append('discount_percent', discountPercent);
    formData.append('sku', sku);
    formData.append('stock', stock);
    formData.append('description', description);
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
            alert(data.message);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error saving product detail:', error);
        alert('Có lỗi xảy ra!');
    });
}

// ==================== Variants Management ====================
function renderVariants(variants) {
    const container = document.getElementById('variantsList');
    
    if (!variants || variants.length === 0) {
        container.innerHTML = '<p style="color: #64748b; text-align: center; padding: 20px;">Chưa có biến thể nào</p>';
        return;
    }
    
    let html = '';
    variants.forEach(v => {
        html += `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; border-bottom: 1px solid #e2e8f0;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="display: inline-block; width: 20px; height: 20px; border-radius: 50%; background: ${v.color_hex || '#ccc'}; border: 1px solid #ddd;"></span>
                <span style="font-weight: 500;">${v.color_name}</span>
                <span style="color: #64748b;">|</span>
                <span>${v.storage}</span>
                <span style="color: #64748b;">|</span>
                <span style="color: #dc2626; font-weight: 500;">${parseInt(v.price).toLocaleString('vi-VN')}đ</span>
                <span style="color: #64748b;">|</span>
                <span>Kho: ${v.stock_quantity}</span>
            </div>
            <div style="display: flex; gap: 6px;">
                <button onclick="editVariant(${v.id}, '${v.color_name}', '${v.color_hex || ''}', '${v.storage}', ${v.price}, '${v.sku || ''}', ${v.stock_quantity})" style="background: #fef3c7; color: #b45309; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer;">Sửa</button>
                <button onclick="deleteVariant(${v.id}, '${v.color_name} - ${v.storage}')" style="background: #fee2e2; color: #dc2626; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer;">Xóa</button>
            </div>
        </div>`;
    });
    container.innerHTML = html;
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

function deleteVariant(id, name) {
    if (!confirm(`Bạn có chắc muốn xóa biến thể "${name}"?`)) {
        return;
    }
    
    const formData = new FormData();
    formData.append('variant_id', id);
    
    fetch('/products/variant/delete/', {
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
            loadProductDetail(currentProductId);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting variant:', error);
        alert('Có lỗi xảy ra!');
    });
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
    if (!confirm('Bạn có chắc muốn xóa ảnh này?')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('image_id', imageId);
    
    fetch('/products/image/delete/', {
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
            loadProductDetail(currentProductId);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting image:', error);
        alert('Có lỗi xảy ra!');
    });
}

// ==================== Event Listeners ====================
document.addEventListener('DOMContentLoaded', function() {
    // Price calculation
    const detailOriginalPrice = document.getElementById('detailOriginalPrice');
    const detailDiscountPercent = document.getElementById('detailDiscountPercent');
    
    if (detailOriginalPrice) {
        detailOriginalPrice.addEventListener('input', calculateDetailDiscountedPrice);
    }
    if (detailDiscountPercent) {
        detailDiscountPercent.addEventListener('input', calculateDetailDiscountedPrice);
    }
});
