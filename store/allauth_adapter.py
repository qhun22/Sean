from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpResponseRedirect
from django.urls import reverse


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom Social Account Adapter cho CustomUser
    Auto signup user khi login Google
    """
    
    def is_auto_signup(self, request, sociallogin):
        return True
    
    def save(self, request, sociallogin):
        """
        Override save to ensure user is saved and can login
        """
        return super().save(request, sociallogin)
    
    def pre_social_login(self, request, sociallogin):
        """
        Called after user authenticates with provider but before login
        """
        # Check if user already exists by email
        email = sociallogin.user.email
        if email:
            from store.models import CustomUser
            try:
                user = CustomUser.objects.get(email=email)
                sociallogin.user = user
            except CustomUser.DoesNotExist:
                pass
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user info từ Google OAuth
        """
        user = super().populate_user(request, sociallogin, data)
        
        email = data.get('email', '')
        if email:
            user.email = email
            user.username = email.split('@')[0][:150]
        
        # Get full name from Google
        full_name = data.get('name', '')
        if not full_name:
            given_name = data.get('given_name', '')
            family_name = data.get('family_name', '')
            full_name = f"{family_name} {given_name}".strip()
        
        user.last_name = full_name or email.split('@')[0]
        user.is_oauth_user = True
        
        return user


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True
    
    def get_login_redirect_url(self, request):
        """
        Redirect to home after successful login
        """
        return reverse('store:home')
