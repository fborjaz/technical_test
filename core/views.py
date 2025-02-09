from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
from .models import *
from django.core.exceptions import ValidationError

# Create your views here.
def Home(request):
    return render(request, 'index.html')

def RegisterView(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('conf_password', '')

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
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return redirect('register')

        # Crear usuario de forma segura
        try:
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = name
            user.last_name = last_name
            user.save()
        except ValidationError as e:
            messages.error(request, f'Error al registrar usuario: {e}')
            return redirect('register')

        messages.success(request, 'Usuario registrado exitosamente. Inicia sesión.')
        return redirect('login')

    return render(request, 'register.html', {'title': 'Registro'})


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


def LogoutView(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')