import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# Si necesitas agregar algún campo extra al usuario puedes extender el modelo User
# Crea un administrador de usuarios personalizado
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Crea un nuevo usuario con email"""
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):  # Ahora hereda de PermissionsMixin
    email = models.EmailField(unique=True)
    email_token = models.CharField(max_length=64, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    email_token_created_at = models.DateTimeField(null=True, blank=True)

    # Información adicional para la autenticación
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # Agregado para manejar permisos de superusuario

    # Campos obligatorios para la autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['is_staff', 'is_superuser']  # Cambia si es necesario

    objects = CustomUserManager()

    def generate_email_token(self):
        self.email_token = str(uuid.uuid4())
        self.email_token_created_at = timezone.now()
        self.save()

    def is_token_expired(self):
        if self.email_token_created_at:
            return (timezone.now() - self.email_token_created_at).total_seconds() > 3600  # 1 hora
        return False

    def __str__(self):
        return self.email

# Modelo para los mensajes de error y éxito (en caso de que necesites guardarlos para algún proceso)
class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('info', 'Info'),
    ]
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message_type.capitalize()} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
