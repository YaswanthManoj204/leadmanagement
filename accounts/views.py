from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import UserCreateForm, UserEditForm
from leads.models import Lead


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin))


@ensure_csrf_cookie
def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    my_leads = Lead.objects.filter(assigned_to=request.user)
    context = {
        'profile': profile,
        'total_assigned': my_leads.count(),
        'total_won': my_leads.filter(status=Lead.STATUS_CLOSED_WON).count(),
        'total_active': my_leads.exclude(status__in=[Lead.STATUS_CLOSED_WON, Lead.STATUS_CLOSED_LOST]).count(),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
@user_passes_test(is_admin)
def user_list_view(request):
    users = User.objects.select_related('profile').prefetch_related('assigned_leads').order_by('-is_active', 'username')
    user_stats = []
    for u in users:
        total = u.assigned_leads.count()
        won = u.assigned_leads.filter(status=Lead.STATUS_CLOSED_WON).count()
        active = u.assigned_leads.exclude(status__in=[Lead.STATUS_CLOSED_WON, Lead.STATUS_CLOSED_LOST]).count()
        user_stats.append({
            'user': u,
            'total_leads': total,
            'won_leads': won,
            'active_leads': active,
            'conversion_rate': round((won / total * 100), 1) if total > 0 else 0
        })

    return render(request, 'accounts/user_list.html', {'user_stats': user_stats})


@login_required
@user_passes_test(is_admin)
def user_create_view(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create New Team Member'})


@login_required
@user_passes_test(is_admin)
def user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user.username}' updated successfully.")
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': f'Edit Member: {user.username}', 'edit_user': user})
