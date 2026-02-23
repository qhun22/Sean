"""
Custom Authentication Backend cho QHUN22
Sử dụng email để đăng nhập thay vì username
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom Authentication Backend
    - Cho phép đăng nhập bằng email thay vì username
    - Kế thừa từ ModelBackend để giữ các tính năng bảo mật
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return
        
        try:
            # Tìm user theo email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Chạy hash password để tránh timing attack
            User().set_password(password)
            return
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
