from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from users.forms import ProfileForm, RegisterForm
from users.models import Profile

# Create your views here.

ORDERS_PER_PAGE = 10


def register_view(request):
    if request.user.is_authenticated:
        return redirect('products:list')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Добро пожаловать в магазин Bikeshop!')
            return redirect('products:list')


    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('products:list')

    if request.method == 'POST':
        password = request.POST.get('password')
        username = request.POST.get('username').lower()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Добро пожаловать!')
            return redirect('products:list')
        else:
            messages.error(request, 'Неверный логин или пароль')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('products:list')


@login_required
def profile(request):
    user_profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            request.user.email = form.cleaned_data['email']
            request.user.save(update_fields=['email'])
            messages.success(request, 'Данные сохранены')
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=user_profile, initial={'email': request.user.email})

    orders = request.user.orders.order_by('-created_at')
    orders_page = Paginator(orders, ORDERS_PER_PAGE).get_page(request.GET.get('page'))

    return render(request, 'account.html', {'form': form, 'orders_page': orders_page})



