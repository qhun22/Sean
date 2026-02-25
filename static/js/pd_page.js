/* ========================================================
   QHUN22 – Product Detail Page Logic
   ======================================================== */

// ========== State ==========
let selectedColor = null;
let selectedStorage = null;
let currentImages = [];
let currentImageIndex = 0;
let autoSlideInterval = null;
let isAutoSlideActive = true;

// Gallery lightbox state
let galleryImages = [];
let galleryIndex = 0;
let galleryCurrentSku = null;

// ========== Init ==========
document.addEventListener('DOMContentLoaded', function () {
    const firstStorageBtn = document.querySelector('.pd-storage-btn');
    if (firstStorageBtn) selectStorage(firstStorageBtn);

    const firstColorBtn = document.querySelector('.pd-color-btn');
    if (firstColorBtn) selectColor(firstColorBtn);

    updateStoragePrices();
    updateColorButtons();
    renderBottomTabs();

    if (typeof specData !== 'undefined' && specData) renderSpec(specData);

    setTimeout(function () { startAutoSlide(); }, 2000);
});

window.addEventListener('beforeunload', function () { stopAutoSlide(); });

document.addEventListener('visibilitychange', function () {
    if (document.hidden) pauseAutoSlide();
    else resumeAutoSlide();
});

// ========== Storage Selection ==========
function selectStorage(btn) {
    document.querySelectorAll('.pd-storage-btn').forEach(function (b) { b.classList.remove('selected'); });
    btn.classList.add('selected');
    selectedStorage = btn.dataset.storage;
    updatePriceDisplay();
    updateStoragePrices();
}

function updateStoragePrices() {
    document.querySelectorAll('.pd-storage-btn').forEach(function (btn) {
        var storage = btn.dataset.storage;
        var v = variantsData.find(function (x) { return x.storage === storage; });
        var priceEl = btn.querySelector('.pd-storage-price');
        if (v && priceEl) priceEl.textContent = formatPrice(v.price) + ' đ';
    });
}

// ========== Color Selection ==========
function selectColor(btn) {
    document.querySelectorAll('.pd-color-btn').forEach(function (b) { b.classList.remove('selected'); });
    btn.classList.add('selected');
    selectedColor = btn.dataset.color;

    var sku = btn.dataset.sku;
    loadColorImages(sku);
    updatePriceDisplay();

    document.querySelectorAll('.pd-bottom-tab[data-color]').forEach(function (t) {
        t.classList.toggle('active', t.dataset.color === selectedColor);
    });
}

function updateColorButtons() {
    document.querySelectorAll('.pd-color-btn').forEach(function (btn, idx) {
        var sku = btn.dataset.sku;
        var thumbEl = document.getElementById('colorThumb_' + idx);
        var nameEl = btn.querySelector('.pd-color-name');

        if (colorImagesData[sku]) {
            if (thumbEl && colorImagesData[sku].images.length > 0) {
                thumbEl.innerHTML = '<img src="' + colorImagesData[sku].images[0] + '" alt="">';
            }
            if (nameEl && colorImagesData[sku].color_name) {
                nameEl.textContent = colorImagesData[sku].color_name;
            }
        }
    });
}

// ========== Image Gallery ==========
function loadColorImages(sku) {
    if (colorImagesData[sku] && colorImagesData[sku].images.length > 0) {
        currentImages = colorImagesData[sku].images;
    } else {
        var fallbackImg = document.getElementById('pdMainImg').dataset.fallback || '/static/logos/sean.gif';
        currentImages = [fallbackImg];
    }
    currentImageIndex = 0;
    renderGallery();
    stopAutoSlide();
    setTimeout(function () { startAutoSlide(); }, 1000);
}

function renderGallery() {
    var mainImg = document.getElementById('pdMainImg');
    if (!mainImg || currentImages.length === 0) return;

    var newSrc = currentImages[currentImageIndex];
    // If same image, skip
    if (mainImg.src && mainImg.src.endsWith(newSrc.replace(/^.*\/\/[^\/]+/, ''))) return;

    // Quick fade out (150ms)
    mainImg.classList.add('pd-fade-out');
    setTimeout(function () {
        mainImg.src = newSrc;
        mainImg.onload = function () {
            mainImg.classList.remove('pd-fade-out');
            mainImg.onload = null;
        };
        // Fallback: if image is cached and onload doesn't fire
        setTimeout(function () {
            mainImg.classList.remove('pd-fade-out');
        }, 100);
    }, 150);
}

// ========== Auto Slide ==========
function startAutoSlide() {
    if (autoSlideInterval) clearInterval(autoSlideInterval);
    if (currentImages && currentImages.length > 1 && isAutoSlideActive) {
        autoSlideInterval = setInterval(function () {
            currentImageIndex = (currentImageIndex + 1) % currentImages.length;
            renderGallery();
        }, 3000);
    }
}

function stopAutoSlide() {
    if (autoSlideInterval) { clearInterval(autoSlideInterval); autoSlideInterval = null; }
}

function pauseAutoSlide() { isAutoSlideActive = false; stopAutoSlide(); }

function resumeAutoSlide() { isAutoSlideActive = true; startAutoSlide(); }

function prevImage() {
    if (currentImages.length === 0) return;
    pauseAutoSlide();
    setTimeout(function () { resumeAutoSlide(); }, 5000);
    currentImageIndex = (currentImageIndex - 1 + currentImages.length) % currentImages.length;
    renderGallery();
}

function nextImage() {
    if (currentImages.length === 0) return;
    pauseAutoSlide();
    setTimeout(function () { resumeAutoSlide(); }, 5000);
    currentImageIndex = (currentImageIndex + 1) % currentImages.length;
    renderGallery();
}

// ========== Price Display ==========
function updatePriceDisplay() {
    if (!selectedColor || !selectedStorage) return;

    var variant = variantsData.find(function (v) {
        return v.color_name === selectedColor && v.storage === selectedStorage;
    });
    if (!variant) return;

    document.getElementById('pdPrice').textContent = formatPrice(variant.price) + ' đ';

    var origEl = document.getElementById('pdOriginalPrice');
    if (variant.original_price > variant.price) {
        origEl.textContent = formatPrice(variant.original_price) + ' đ';
        origEl.style.display = '';
    } else {
        origEl.style.display = 'none';
    }

    document.getElementById('pdSku').textContent = variant.sku || '-';

    var installEl = document.getElementById('pdInstallment');
    if (variant.price > 0) {
        var monthly = Math.round(variant.price / 6);
        installEl.textContent = 'Trả góp 0% thẻ TD/CTTC chỉ từ ' + formatPrice(monthly) + ' đ x 6 tháng >';
    } else {
        installEl.textContent = '';
    }
}

// ========== Bottom Tabs ==========
function renderBottomTabs() {
    var container = document.getElementById('pdBottomTabs');
    if (!container) return;

    var html = '';
    var colorBtns = document.querySelectorAll('.pd-color-btn');

    colorBtns.forEach(function (btn) {
        var sku = btn.dataset.sku;
        var color = btn.dataset.color;
        var imgData = colorImagesData[sku];
        var thumbUrl = (imgData && imgData.images.length > 0) ? imgData.images[0] : '';
        var displayName = (imgData && imgData.color_name) ? imgData.color_name : color;

        html += '<div class="pd-bottom-tab' + (color === selectedColor ? ' active' : '') + '" data-color="' + color + '" onclick="selectColorByName(\'' + color.replace(/'/g, "\\'") + '\')">';
        html += '<div class="pd-bottom-tab-icon">';
        if (thumbUrl) html += '<img src="' + thumbUrl + '" alt="">';
        html += '</div>';
        html += '<div class="pd-bottom-tab-label">' + displayName + '</div>';
        html += '</div>';
    });

    if (typeof specData !== 'undefined' && specData) {
        html += '<div class="pd-bottom-tab" onclick="scrollToSpec()">';
        html += '<div class="pd-bottom-tab-icon"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><circle cx="12" cy="12" r="3"/></svg></div>';
        html += '<div class="pd-bottom-tab-label">Thông số kỹ thuật</div>';
        html += '</div>';
    }

    html += '<div class="pd-bottom-tab" onclick="scrollToDescription()">';
    html += '<div class="pd-bottom-tab-icon"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div>';
    html += '<div class="pd-bottom-tab-label">Thông tin sản phẩm</div>';
    html += '</div>';

    html += '<div class="pd-bottom-tab" onclick="openGallery()">';
    html += '<div class="pd-bottom-tab-icon"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg></div>';
    html += '<div class="pd-bottom-tab-label">Xem chi tiết ảnh</div>';
    html += '</div>';

    container.innerHTML = html;
    var totalTabs = container.children.length;
    if (totalTabs > 0) {
        container.style.gridTemplateColumns = 'repeat(' + totalTabs + ', 1fr)';
    }
}

function selectColorByName(colorName) {
    var btn = document.querySelector('.pd-color-btn[data-color="' + colorName + '"]');
    if (btn) selectColor(btn);
}

function scrollToSpec() {
    var el = document.getElementById('pdSpecSection');
    if (el) {
        el.style.display = 'block';
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function scrollToDescription() {
    var el = document.getElementById('pdDescSection');
    if (el) {
        el.style.display = 'block';
        var content = document.getElementById('pdDescContent');
        if (content && !content.innerHTML.trim()) {
            content.textContent = productDescription || 'Chưa có thông tin sản phẩm.';
        }
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ========== Gallery Lightbox ==========
function openGallery() {
    var overlay = document.getElementById('pdGalleryOverlay');
    if (!overlay) return;

    buildGalleryColorTabs();

    var activeBtn = document.querySelector('.pd-color-btn.selected');
    if (activeBtn) {
        galleryCurrentSku = activeBtn.dataset.sku;
    } else {
        var firstSku = Object.keys(colorImagesData)[0];
        galleryCurrentSku = firstSku || null;
    }

    loadGalleryColor(galleryCurrentSku);
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function buildGalleryColorTabs() {
    var container = document.getElementById('pdGalleryColorTabs');
    if (!container) return;
    var html = '';
    document.querySelectorAll('.pd-color-btn').forEach(function (btn) {
        var sku = btn.dataset.sku;
        var imgData = colorImagesData[sku];
        var displayName = (imgData && imgData.color_name) ? imgData.color_name : btn.dataset.color;
        html += '<div class="pd-gallery-color-tab" data-sku="' + sku + '" onclick="switchGalleryColor(\'' + sku.replace(/'/g, "\\'") + '\')">' + displayName + '</div>';
    });
    html += '<button class="pd-gallery-close" onclick="closeGallery()">';
    html += '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>';
    html += '</button>';
    container.innerHTML = html;
}

function switchGalleryColor(sku) {
    galleryCurrentSku = sku;
    loadGalleryColor(sku);
}

function loadGalleryColor(sku) {
    var images = [];
    if (sku && colorImagesData[sku]) {
        images = colorImagesData[sku].images || [];
    } else {
        images = currentImages;
    }
    galleryImages = images;
    galleryIndex = 0;

    document.querySelectorAll('.pd-gallery-color-tab').forEach(function (tab) {
        tab.classList.toggle('active', tab.dataset.sku === sku);
    });

    updateGalleryMainImg();
    buildGalleryThumbs();
}

function updateGalleryMainImg() {
    var img = document.getElementById('pdGalleryMainImg');
    if (!img) return;
    if (galleryImages.length === 0) {
        img.src = '';
        img.alt = 'Chưa có ảnh';
        return;
    }
    img.classList.add('pd-slide-out');
    setTimeout(function () {
        img.src = galleryImages[galleryIndex];
        img.alt = 'Ảnh ' + (galleryIndex + 1);
        img.onload = function () {
            img.classList.remove('pd-slide-out');
        };
        setTimeout(function () {
            img.classList.remove('pd-slide-out');
        }, 600);
    }, 400);
    document.querySelectorAll('.pd-gallery-thumb').forEach(function (t, i) {
        t.classList.toggle('active', i === galleryIndex);
    });
}

function buildGalleryThumbs() {
    var container = document.getElementById('pdGalleryThumbs');
    if (!container) return;
    if (galleryImages.length === 0) {
        container.innerHTML = '<p style="color:#94a3b8;font-size:13px;">Chưa có ảnh cho màu này.</p>';
        return;
    }
    var html = '';
    galleryImages.forEach(function (url, idx) {
        html += '<div class="pd-gallery-thumb' + (idx === galleryIndex ? ' active' : '') + '" onclick="galleryGoTo(' + idx + ')">';
        html += '<img src="' + url + '" alt="" draggable="false">';
        html += '</div>';
    });
    container.innerHTML = html;
}

function galleryGoTo(idx) { galleryIndex = idx; updateGalleryMainImg(); }
function galleryPrev() { if (galleryImages.length === 0) return; galleryIndex = (galleryIndex - 1 + galleryImages.length) % galleryImages.length; updateGalleryMainImg(); }
function galleryNext() { if (galleryImages.length === 0) return; galleryIndex = (galleryIndex + 1) % galleryImages.length; updateGalleryMainImg(); }

function closeGallery() {
    var overlay = document.getElementById('pdGalleryOverlay');
    if (overlay) overlay.classList.remove('show');
    document.body.style.overflow = '';
}

function closeGalleryOverlay(e) {
    if (e.target === document.getElementById('pdGalleryOverlay')) closeGallery();
}

document.addEventListener('keydown', function (e) {
    var overlay = document.getElementById('pdGalleryOverlay');
    if (!overlay || !overlay.classList.contains('show')) return;
    if (e.key === 'ArrowLeft') galleryPrev();
    else if (e.key === 'ArrowRight') galleryNext();
    else if (e.key === 'Escape') closeGallery();
});

// ========== Specifications ==========
function renderSpec(data) {
    var section = document.getElementById('pdSpecSection');
    var content = document.getElementById('pdSpecContent');
    if (!section || !content || !data) return;

    section.style.display = 'block';
    var html = '';

    if (data.groups && Array.isArray(data.groups)) {
        data.groups.forEach(function (group) {
            html += '<div class="pd-spec-group-title">' + (group.name || '') + '</div>';
            html += '<table class="pd-spec-table">';
            if (group.specs && Array.isArray(group.specs)) {
                group.specs.forEach(function (spec) {
                    html += '<tr><td>' + (spec.name || spec.key || '') + '</td><td>' + (spec.value || '') + '</td></tr>';
                });
            }
            html += '</table>';
        });
    } else if (typeof data === 'object') {
        html += '<table class="pd-spec-table">';
        for (var key in data) {
            if (!data.hasOwnProperty(key)) continue;
            var value = data[key];
            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                html += '</table>';
                html += '<div class="pd-spec-group-title">' + key + '</div>';
                html += '<table class="pd-spec-table">';
                for (var k2 in value) {
                    if (!value.hasOwnProperty(k2)) continue;
                    html += '<tr><td>' + k2 + '</td><td>' + value[k2] + '</td></tr>';
                }
            } else {
                html += '<tr><td>' + key + '</td><td>' + value + '</td></tr>';
            }
        }
        html += '</table>';
    }

    content.innerHTML = html;
}

// ========== Utilities ==========
function formatPrice(value) {
    if (!value) return '0';
    return parseInt(value).toLocaleString('vi-VN').replace(/,/g, '.');
}

function buyNow() {
    alert('Chức năng mua hàng đang được phát triển!');
}

function addToCart() {
    alert('Đã thêm vào giỏ hàng!');
}
