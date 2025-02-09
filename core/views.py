from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.views import PasswordResetView
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .models import CustomUser
import uuid

# Create your views here.
def Home(request):
    return render(request, 'index.html')

def RegisterView(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Validación de campos vacíos
        if not all([name, last_name, email, password, password_confirm]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('register')

        # Validación de formato de correo
        if '@' not in email or '.' not in email:
            messages.error(request, 'Por favor, ingrese un correo electrónico válido.')
            return redirect('register')

        # Validación de contraseña mínima
        if len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return redirect('register')

        # Validación de coincidencia de contraseñas
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('register')

        # Verificar si el usuario ya existe
        if get_user_model().objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return redirect('register')

        # Crear usuario de forma segura
        try:
            # Crear un nuevo usuario de tipo CustomUser
            user = get_user_model().objects.create_user(email=email, password=password)
            user.first_name = name
            user.last_name = last_name
            user.save()

            # No necesitas crear un CustomUser separado, ya que 'user' es un CustomUser
            # Generar el token de verificación de correo
            user.generate_email_token()  # Si el método 'generate_email_token' está en CustomUser
            user.save()

            # Enviar el correo de verificación
            token_url = f"{request.scheme}://{get_current_site(request).domain}/verify-email/{user.email_token}/"
            email_subject = 'Verifica tu correo electrónico'
            email_message = render_to_string('verify_email.html', {
                'user': user,
                'token_url': token_url,
            })
            send_mail(email_subject, email_message, settings.DEFAULT_FROM_EMAIL, [email])

            messages.success(request, 'Usuario registrado exitosamente. Por favor verifica tu correo electrónico.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error al registrar usuario: {e}')
            return redirect('register')

    return render(request, 'register.html', {'title': 'Registro'})


def VerifyEmailView(request, token):
    try:
        user = CustomUser.objects.get(email_token=token)

        if user.is_token_expired():
            messages.error(request, 'El enlace de verificación ha expirado.')
            return redirect('login')

        user.email_verified = True
        user.email_token = ''  # Limpiamos el token después de la verificación
        user.save()
        messages.success(request, 'Correo electrónico verificado exitosamente. Ahora puedes iniciar sesión.')
        return redirect('login')

    except CustomUser.DoesNotExist:
        messages.error(request, 'El enlace de verificación es inválido o ha expirado.')
        return redirect('login')


def LoginView(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Correo y contraseña son obligatorios.', extra_tags='error')
            return redirect('login')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Inicio de sesión exitoso.', extra_tags='success')
            return redirect('home')
        else:
            # Guardamos el mensaje en la sesión con la clase adecuada
            request.session['error_message'] = 'Correo o contraseña incorrectos.'

            return redirect('login')

    # Recuperar mensaje de error almacenado en la sesión
    error_message = request.session.pop('error_message', None)

    return render(request, 'login.html', {'title': 'Iniciar Sesión', 'error_message': error_message})

class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        messages.success(self.request, 'Te hemos enviado un correo para restablecer tu contraseña.')
        return super().form_valid(form)

def LogoutView(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')