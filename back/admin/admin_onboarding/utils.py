import os
import logging

from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django.utils.translation import gettext as _

from admin.sequences.models import Sequence
from users.models import User

from .models import AdminOnboardingStatus

logger = logging.getLogger(__name__)


def setup_admin_onboarding(admin_user):
    """
    Sets up the admin onboarding process for a new admin user.
    
    Args:
        admin_user: The admin user to set up onboarding for
    
    Returns:
        bool: True if setup was successful, False otherwise
    """
    try:
        # Check if the admin onboarding sequence exists
        if not Sequence.objects.filter(pk=100).exists():
            # Load the admin onboarding fixtures
            fixture_path = os.path.join(settings.BASE_DIR, "fixtures/admin_onboarding.json")
            call_command("loaddata", fixture_path, verbosity=0)
            
        # Get the admin onboarding sequence
        sequence = Sequence.objects.get(pk=100)
        
        # Create or update the admin onboarding status
        with transaction.atomic():
            status, created = AdminOnboardingStatus.objects.get_or_create(
                admin=admin_user,
                defaults={"status": AdminOnboardingStatus.Status.IN_PROGRESS}
            )
            
            if not created and status.status == AdminOnboardingStatus.Status.COMPLETED:
                # Admin has already completed onboarding
                return False
                
            # Add the sequence to the admin user
            admin_user.add_sequences([sequence])
            
            # Update the status
            status.status = AdminOnboardingStatus.Status.IN_PROGRESS
            status.save()
            
        return True
    except Exception as e:
        logger.error(f"Error setting up admin onboarding: {e}")
        return False


def check_admin_first_login(admin_user):
    """
    Checks if this is the admin's first login and sets up onboarding if needed.
    
    Args:
        admin_user: The admin user to check
    
    Returns:
        bool: True if this is the first login, False otherwise
    """
    if not admin_user.is_admin:
        return False
        
    # Check if the admin has an onboarding status
    try:
        status = AdminOnboardingStatus.objects.get(admin=admin_user)
        if status.status == AdminOnboardingStatus.Status.NOT_STARTED:
            setup_admin_onboarding(admin_user)
            return True
        return False
    except AdminOnboardingStatus.DoesNotExist:
        # Create a new onboarding status and set up onboarding
        AdminOnboardingStatus.objects.create(
            admin=admin_user,
            status=AdminOnboardingStatus.Status.NOT_STARTED
        )
        setup_admin_onboarding(admin_user)
        return True


def mark_admin_onboarding_completed(admin_user):
    """
    Marks the admin onboarding as completed.
    
    Args:
        admin_user: The admin user to mark as completed
    
    Returns:
        bool: True if marking was successful, False otherwise
    """
    try:
        status, created = AdminOnboardingStatus.objects.get_or_create(
            admin=admin_user,
            defaults={"status": AdminOnboardingStatus.Status.COMPLETED}
        )
        
        if not created:
            status.status = AdminOnboardingStatus.Status.COMPLETED
            status.save()
            
        return True
    except Exception as e:
        logger.error(f"Error marking admin onboarding as completed: {e}")
        return False
