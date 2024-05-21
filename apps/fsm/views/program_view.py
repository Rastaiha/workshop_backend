from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.views.decorators.cache import cache_page
from apps.fsm.models import Program
from apps.fsm.permissions import IsProgramModifier, HasActiveRegistration
from django.utils.decorators import method_decorator

from apps.fsm.serializers.program_serializers import ProgramSerializer


class ProgramViewSet(ModelViewSet):
    serializer_class = ProgramSerializer
    queryset = Program.objects.all()
    my_tags = ['program']
    filterset_fields = ['website', 'is_private']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'user': self.request.user})
        return context

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'retrieve' or self.action == 'list':
            permission_classes = [permissions.AllowAny]
        elif self.action == 'get_fsms':
            permission_classes = [HasActiveRegistration]
        else:
            permission_classes = [IsProgramModifier]
        return [permission() for permission in permission_classes]

    # @method_decorator(cache_page(60 * 1,  key_prefix="program"))
    def list(self, request, *args, **kwargs):
        return super().list(self, request, *args, **kwargs)
