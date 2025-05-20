from django.contrib.sessions.models import Session
from django.utils import timezone
from .models import Utilisateurs
import logging

logger = logging.getLogger(__name__)

class SessionManagementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_cleanup = timezone.now()

    def __call__(self, request):
        # Process request
        if 'user_id' in request.session:
            try:
                # Get user from session
                user = Utilisateurs.objects.get(id=request.session['user_id'])
                
                # Update session expiry
                request.session.set_expiry(86400)  # 24 hours
                
                # Clean up expired sessions only once per hour
                current_time = timezone.now()
                if (current_time - self.last_cleanup).total_seconds() > 3600:
                    Session.objects.filter(expire_date__lt=current_time).delete()
                    self.last_cleanup = current_time
                
                # Ensure user's session is valid
                if not request.session.get('username') or not request.session.get('role'):
                    request.session['username'] = user.username
                    request.session['role'] = user.role
                    request.session.save()
                
            except Utilisateurs.DoesNotExist:
                # If user doesn't exist, clear the session
                request.session.flush()
                logger.warning(f"Invalid session for user_id: {request.session.get('user_id')}")

        response = self.get_response(request)
        return response 