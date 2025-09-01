from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView  # Make sure UpdateView is imported
from django.urls import reverse_lazy
from django.http import Http404
from .models import CustomUser
from .forms import UserRegistrationForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('projects:project_list')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_page = request.GET.get('next')
                return redirect(next_page) if next_page else redirect('projects:project_list')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('users:login')

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_object(self):
        username = self.kwargs.get('username')
        try:
            if username:
                return CustomUser.objects.get(username=username)
            return self.request.user
        except CustomUser.DoesNotExist:
            raise Http404("User does not exist")

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserUpdateForm
    template_name = 'users/profile_form.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = ProfileUpdateForm(
                self.request.POST, self.request.FILES, instance=self.request.user
            )
        else:
            context['profile_form'] = ProfileUpdateForm(instance=self.request.user)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        profile_form = context['profile_form']
        if profile_form.is_valid():
            profile_form.save()
            messages.success(self.request, 'Your profile has been updated!')
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

@login_required
def profile(request):
    return redirect('users:profile_detail', username=request.user.username)

@login_required
def dashboard(request):
    user = request.user
    owned_projects = user.owned_projects.all()
    member_projects = user.projects.all()
    assigned_tasks = user.assigned_tasks.select_related('project')
    
    context = {
        'owned_projects': owned_projects,
        'member_projects': member_projects.exclude(id__in=owned_projects),
        'assigned_tasks': assigned_tasks,
        'total_projects': owned_projects.count() + member_projects.count(),
        'total_tasks': assigned_tasks.count(),
    }
    return render(request, 'users/dashboard.html', context)

@login_required
def dashboard(request):
    user = request.user
    
    # Get user's projects and tasks
    owned_projects = user.owned_projects.all()
    member_projects = user.projects.all()
    assigned_tasks = user.assigned_tasks.select_related('project')
    
    # Calculate counts manually instead of using template filter
    todo_count = assigned_tasks.filter(status='todo').count()
    in_progress_count = assigned_tasks.filter(status='in_progress').count()
    
    # Get recent tasks (limit to 5)
    recent_tasks = assigned_tasks[:5]
    
    context = {
        'owned_projects': owned_projects,
        'member_projects': member_projects.exclude(id__in=owned_projects),
        'assigned_tasks': assigned_tasks,
        'recent_tasks': recent_tasks,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'total_projects': owned_projects.count() + member_projects.count(),
        'total_tasks': assigned_tasks.count(),
    }
    
    return render(request, 'users/dashboard.html', context)

# Add to users/views.py if you want custom views
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView,
    PasswordChangeView, PasswordChangeDoneView
)

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = '/users/password-reset/done/'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

# ... and similarly for other views
# Add this function to your views
from django.core.mail import send_mail
from django.http import HttpResponse

def test_email(request):
    send_mail(
        'Test Email from Django',
        'This is a test email to verify your email configuration.',
        'from@example.com',  # From address
        ['to@example.com'],  # To address (use your email)
        fail_silently=False,
    )
    return HttpResponse("Test email sent! Check your console/email.")