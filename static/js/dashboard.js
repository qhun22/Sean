// Dashboard JavaScript

// Custom Confirm Modal (QHConfirm style)
const QHConfirm = {
    show: function(message, onConfirm, onCancel = null) {
        // Remove existing modal if any
        const existing = document.querySelector('.qh-confirm-modal');
        if (existing) existing.remove();

        // Create modal
        const modal = document.createElement('div');
        modal.className = 'qh-confirm-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 99999;
        `;
        
        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 12px;
                padding: 24px;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                font-family: 'Signika', sans-serif;
            ">
                <h3 style="
                    margin: 0 0 12px 0;
                    font-size: 18px;
                    font-weight: 600;
                    color: #1e293b;
                ">Xác nhận</h3>
                <p style="
                    margin: 0 0 20px 0;
                    font-size: 14px;
                    color: #475569;
                    line-height: 1.5;
                ">${message}</p>
                <div style="
                    display: flex;
                    gap: 12px;
                    justify-content: flex-end;
                ">
                    <button class="qh-btn-cancel-confirm" style="
                        padding: 10px 20px;
                        border: none;
                        border-radius: 8px;
                        background: #E0E0E0;
                        color: #333;
                        font-size: 14px;
                        font-weight: 500;
                        cursor: pointer;
                        font-family: 'Signika', sans-serif;
                        transition: background 0.2s;
                    ">Hủy</button>
                    <button class="qh-btn-confirm" style="
                        padding: 10px 20px;
                        border: none;
                        border-radius: 8px;
                        background: #2563eb;
                        color: white;
                        font-size: 14px;
                        font-weight: 500;
                        cursor: pointer;
                        font-family: 'Signika', sans-serif;
                        transition: background 0.2s;
                    ">Xác nhận</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Event handlers
        modal.querySelector('.qh-btn-confirm').onclick = () => {
            modal.remove();
            if (onConfirm) onConfirm();
        };
        
        modal.querySelector('.qh-btn-cancel-confirm').onclick = () => {
            modal.remove();
            if (onCancel) onCancel();
        };
        
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.remove();
                if (onCancel) onCancel();
            }
        };
    }
};

window.QHConfirm = QHConfirm;

// Modal Functions
function openAddBrandModal() {
    document.getElementById('addBrandModal').style.display = 'flex';
}

function closeAddBrandModal() {
    document.getElementById('addBrandModal').style.display = 'none';
    document.getElementById('addBrandForm').reset();
}

function openEditBrandModal(id, name, desc) {
    document.getElementById('editBrandId').value = id;
    document.getElementById('editBrandName').value = name;
    document.getElementById('editBrandModal').style.display = 'flex';
}

function closeEditBrandModal() {
    document.getElementById('editBrandModal').style.display = 'none';
    document.getElementById('editBrandForm').reset();
}

// User Modal Functions
function openEditUserModal(id, email, lastName, firstName, phone) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editUserEmail').value = email;
    document.getElementById('editUserLastName').value = lastName;
    document.getElementById('editUserFirstName').value = firstName;
    document.getElementById('editUserPhone').value = phone || '';
    document.getElementById('editUserModal').style.display = 'flex';
}

function closeEditUserModal() {
    document.getElementById('editUserModal').style.display = 'none';
    document.getElementById('editUserForm').reset();
}

// Delete User
function deleteUser(id, email) {
    const message = 'Bạn có chắc muốn xóa người dùng "' + email + '"?';
    
    QHConfirm.show(
        message,
        function() {
            doDeleteUser(id);
        },
        function() {
            // User cancelled
        }
    );
}

function doDeleteUser(id) {
    const formData = new FormData();
    formData.append('user_id', id);
    
    fetch(window.userDeleteUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.csrfToken
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.QHToast.show(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            window.QHToast.show(data.message, 'error');
        }
    })
    .catch(err => {
        window.QHToast.show('Có lỗi xảy ra!', 'error');
    });
}

// Search Brands - Server Side
function searchBrands(event) {
    if (event && event.key !== 'Enter') return;
    const searchTerm = document.getElementById('brandSearchInput').value.trim();
    
    if (searchTerm) {
        window.location.href = '?section=brands&brand_search=' + encodeURIComponent(searchTerm);
    } else {
        window.location.href = '?section=brands';
    }
}

function resetBrandSearch() {
    window.location.href = '?section=brands';
}

// Search Users - Server Side
function searchUsers(event) {
    if (event && event.key !== 'Enter') return;
    const searchTerm = document.getElementById('userSearchInput').value.trim();
    
    if (searchTerm) {
        window.location.href = '?section=users&user_search=' + encodeURIComponent(searchTerm);
    } else {
        window.location.href = '?section=users';
    }
}

function resetUserSearch() {
    window.location.href = '?section=users';
}

// Delete Brand
function deleteBrand(id, name) {
    const message = 'Bạn có chắc muốn xóa hãng "' + name + '"?';
    
    QHConfirm.show(
        message,
        function() {
            doDeleteBrand(id);
        },
        function() {
            // User cancelled
        }
    );
}

function doDeleteBrand(id) {
    const formData = new FormData();
    formData.append('brand_id', id);
    
    fetch(window.brandDeleteUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.csrfToken
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.QHToast.show(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            window.QHToast.show(data.message, 'error');
        }
    })
    .catch(err => {
        window.QHToast.show('Có lỗi xảy ra!', 'error');
    });
}

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Lấy section từ URL hoặc mặc định là stats
    const urlParams = new URLSearchParams(window.location.search);
    const currentSection = urlParams.get('section') || 'stats';
    
    // Cập nhật sidebar active
    const sidebarItems = document.querySelectorAll('.qh-sidebar-item');
    sidebarItems.forEach(item => {
        const section = item.getAttribute('data-section');
        if (section === currentSection) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Hiển thị section đúng
    const statsSection = document.getElementById('stats-section');
    const usersSection = document.getElementById('users-section');
    const brandsSection = document.getElementById('brands-section');
    const productsSection = document.getElementById('products-section');
    
    if (statsSection) statsSection.style.display = (currentSection === 'stats') ? 'block' : 'none';
    if (usersSection) usersSection.style.display = (currentSection === 'users') ? 'block' : 'none';
    if (brandsSection) brandsSection.style.display = (currentSection === 'brands') ? 'block' : 'none';
    if (productsSection) productsSection.style.display = (currentSection === 'products') ? 'block' : 'none';
    
    // Add Brand Form Submit
    const addBrandForm = document.getElementById('addBrandForm');
    if (addBrandForm) {
        addBrandForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(window.brandAddUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.csrfToken
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.QHToast.show(data.message, 'success');
                    closeAddBrandModal();
                    setTimeout(() => location.reload(), 1000);
                } else {
                    window.QHToast.show(data.message, 'error');
                }
            })
            .catch(err => {
                window.QHToast.show('Có lỗi xảy ra!', 'error');
            });
        });
    }
    
    // Edit Brand Form Submit
    const editBrandForm = document.getElementById('editBrandForm');
    if (editBrandForm) {
        editBrandForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(window.brandEditUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.csrfToken
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.QHToast.show(data.message, 'success');
                    closeEditBrandModal();
                    setTimeout(() => location.reload(), 1000);
                } else {
                    window.QHToast.show(data.message, 'error');
                }
            })
            .catch(err => {
                window.QHToast.show('Có lỗi xảy ra!', 'error');
            });
        });
    }
    
    // Edit User Form Submit
    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
        editUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(window.userEditUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.csrfToken
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.QHToast.show(data.message, 'success');
                    closeEditUserModal();
                    setTimeout(() => location.reload(), 1000);
                } else {
                    window.QHToast.show(data.message, 'error');
                }
            })
            .catch(err => {
                window.QHToast.show('Có lỗi xảy ra!', 'error');
            });
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target.id === 'addBrandModal') closeAddBrandModal();
        if (e.target.id === 'editBrandModal') closeEditBrandModal();
        if (e.target.id === 'editUserModal') closeEditUserModal();
    });
});
