from rest_framework import viewsets, permissions
from .models import CV
from .serializers import CVSerializer

class CVViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions for CVs.
    """
    serializer_class = CVSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see and edit their own CVs
        return CV.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically attach the logged-in user to the CV
        serializer.save(user=self.request.user)
