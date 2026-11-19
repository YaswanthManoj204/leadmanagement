from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin / Manager'),
        ('SALESPERSON', 'Salesperson'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SALESPERSON')
    phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, blank=True, default='Sales Executive')
    bio = models.TextField(blank=True)
    monthly_target = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    avatar_color = models.CharField(max_length=20, default='#2563eb')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.user.is_superuser or self.user.is_staff

    @property
    def is_salesperson(self):
        return self.role == 'SALESPERSON' and not self.user.is_superuser


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'ADMIN' if instance.is_superuser else 'SALESPERSON'
        UserProfile.objects.create(user=instance, role=role)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
