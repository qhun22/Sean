from django.core.management.base import BaseCommand
from store.models import CustomUser


class Command(BaseCommand):
    help = 'Xóa tất cả users trừ 1 admin user'

    def handle(self, *args, **options):
        # Tìm admin user đầu tiên
        admin_user = CustomUser.objects.filter(
            is_superuser=True, 
            is_staff=True
        ).first()
        
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('Không tìm thấy admin user nào trong hệ thống!')
            )
            return
        
        # Đếm số lượng users trước khi xóa
        total_users = CustomUser.objects.count()
        
        # Xóa tất cả users trừ admin user
        deleted_count = CustomUser.objects.exclude(id=admin_user.id).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Đã xóa {deleted_count} users'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Giữ lại admin user: {admin_user.email}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Tổng users còn lại: {CustomUser.objects.count()}/{total_users}'
            )
        )
