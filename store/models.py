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
