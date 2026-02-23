from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    """Custom Manager cho CustomUser - không cần username"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email là bắt buộc')
        email = self.normalize_email(email)
        
        # Loại bỏ username khỏi extra_fields nếu có
        extra_fields.pop('username', None)
        
        # Tự động tạo username từ email nếu không được cung cấp
        # Lấy phần trước @ của email
        username = email.split('@')[0]
        extra_fields['username'] = username[:150]  # Django limit
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Loại bỏ username
        extra_fields.pop('username', None)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser phải có is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser phải có is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom User Model cho QHUN22
    - Bỏ username, chỉ dùng email để đăng nhập
    - Thêm số điện thoại
    - Sử dụng last_name làm Họ tên đầy đủ
    - Hỗ trợ cả đăng ký thường và OAuth (Google)
    """
    username = models.CharField(max_length=150, null=True, blank=True)  # Giữ field cho allauth tương thích
    email = models.EmailField(unique=True)  # Email là unique identifier
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Số điện thoại')
    
    # Sử dụng last_name làm tên đầy đủ (Họ tên)
    # Bỏ first_name
    
    # Trường để đánh dấu nguồn đăng ký
    is_oauth_user = models.BooleanField(default=False, verbose_name='Người dùng OAuth')
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'  # Dùng email để đăng nhập
    REQUIRED_FIELDS = []  # Không yêu cầu fields khác khi tạo superuser
    
    class Meta:
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Lấy tên đầy đủ của người dùng
        - Nếu có last_name thì dùng last_name (cả regular và OAuth users)
        - Nếu không có thì dùng email (bỏ @domain)
        """
        if self.last_name:
            return self.last_name.strip()
        # Fallback: lấy phần trước @ của email
        if self.email:
            return self.email.split('@')[0]
        return 'Người dùng'
    
    def get_short_name(self):
        """Lấy tên ngắn (dùng cho chào hỏi)"""
        full_name = self.get_full_name()
        # Nếu là tên đầy đủ có nhiều từ, lấy từ cuối cùng (họ)
        # Nếu chỉ là một từ, dùng từ đó
        names = full_name.split()
        return names[-1] if names else 'Khách'


class Category(models.Model):
    """Danh mục sản phẩm"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Tên danh mục')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Danh mục'
        verbose_name_plural = 'Danh mục'
    
    def __str__(self):
        return self.name


class Brand(models.Model):
    """Hãng sản phẩm (Apple, Samsung, Xiaomi, etc.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Tên hãng')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, verbose_name='Logo')
    is_active = models.BooleanField(default=True, verbose_name='Hoạt động')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Hãng sản phẩm'
        verbose_name_plural = 'Hãng sản phẩm'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Sản phẩm điện thoại"""
    name = models.CharField(max_length=200, verbose_name='Tên sản phẩm')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='Slug')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='Hãng')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='Danh mục')
    description = models.TextField(verbose_name='Mô tả')
    price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='Giá (VNĐ)')
    original_price = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name='Giá gốc')
    image = models.ImageField(upload_to='products/%Y/%m/', blank=True, null=True, verbose_name='Hình ảnh')
    stock = models.PositiveIntegerField(default=0, verbose_name='Số lượng trong kho')
    is_featured = models.BooleanField(default=False, verbose_name='Sản phẩm nổi bật')
    is_active = models.BooleanField(default=True, verbose_name='Hiển thị')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Sản phẩm'
        verbose_name_plural = 'Sản phẩm'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_discount_percent(self):
        """Tính phần trăm giảm giá"""
        if self.original_price and self.original_price > self.price:
            return int((self.original_price - self.price) / self.original_price * 100)
        return 0


class SiteVisit(models.Model):
    """
    Model theo dõi lượt truy cập website
    Mỗi lần vào trang chủ (click logo hoặc refresh) tính là 1 lượt
    """
    visit_time = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian truy cập')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Địa chỉ IP')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='visits', verbose_name='Người dùng')
    
    class Meta:
        verbose_name = 'Lượt truy cập'
        verbose_name_plural = 'Lượt truy cập'
        ordering = ['-visit_time']
    
    def __str__(self):
        return f"Visit at {self.visit_time.strftime('%Y-%m-%d %H:%M')}"


class Order(models.Model):
    """
    Model đơn hàng để theo dõi doanh thu
    """
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('processing', 'Đang xử lý'),
        ('shipped', 'Đang giao hàng'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders', verbose_name='Khách hàng')
    total_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='Tổng tiền')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Trạng thái')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')
    
    class Meta:
        verbose_name = 'Đơn hàng'
        verbose_name_plural = 'Đơn hàng'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id}"
