from .models import AdminOnboardingStatus


def admin_onboarding_processor(request):
    """
    Adds admin onboarding status to the context.
    """
    context = {}
    
    if request.user.is_authenticated and request.user.is_admin:
        try:
            status = AdminOnboardingStatus.objects.get(admin=request.user)
            context['admin_onboarding_status'] = status.status
        except AdminOnboardingStatus.DoesNotExist:
            context['admin_onboarding_status'] = AdminOnboardingStatus.Status.NOT_STARTED
    
    return context
