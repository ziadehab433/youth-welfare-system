from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.accounts.permissions import IsRole
from apps.accounts.permissions import require_permission
from apps.accounts.utils import get_current_admin

from apps.event.models import Plans

from .serializers import (
    PlanListSerializer,
    PlanDetailSerializer,
    PlanCreateSerializer,
    PlanUpdateSerializer,
    AddEventToPlanSerializer,
    PlanEventSerializer,
)
from .services import PlanService


@extend_schema(tags=["Plans APIs"])
class PlansViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية', 'مدير ادارة']
    queryset = Plans.objects.all()
    serializer_class = PlanListSerializer

    # ───────────────── LIST ─────────────────

    @extend_schema(
        description="List all plans (any admin can view)",
        responses={200: PlanListSerializer(many=True)},
    )
    @action(detail=False, methods=['get'], url_path='list')
    @require_permission('read')
    def list_plans(self, request):
        plans = PlanService.get_all_plans()
        serializer = PlanListSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ───────────────── DETAIL ─────────────────

    @extend_schema(
        description="Retrieve a plan with full event details",
        responses={200: PlanDetailSerializer},
    )
    @action(detail=True, methods=['get'], url_path='details')
    @require_permission('read')
    def get_plan(self, request, pk=None):
        plan = PlanService.get_plan_detail(pk)
        serializer = PlanDetailSerializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ───────────────── CREATE ─────────────────

    @extend_schema(
        description="Create a new plan. مسؤول كلية → faculty auto-set. مدير ادارة → faculty optional.",
        request=PlanCreateSerializer,
        responses={201: PlanDetailSerializer},
    )
    @action(detail=False, methods=['post'], url_path='create')
    @require_permission('create')
    def create_plan(self, request):
        admin = get_current_admin(request)
        serializer = PlanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            plan = PlanService.create_plan(admin, serializer.validated_data)
        except ValidationError as e:
            return Response(
                {"error": e.message if hasattr(e, 'message') else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PlanDetailSerializer(plan).data,
            status=status.HTTP_201_CREATED,
        )

    # ───────────────── UPDATE ─────────────────

    @extend_schema(
        description="Update a plan (name, term). مسؤول كلية → own faculty plans. مدير ادارة → global plans only.",
        request=PlanUpdateSerializer,
        responses={200: PlanDetailSerializer},
    )
    @action(detail=True, methods=['patch'], url_path='update')
    @require_permission('update')
    def update_plan(self, request, pk=None):
        admin = get_current_admin(request)
        serializer = PlanUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            plan = PlanService.update_plan(admin, pk, serializer.validated_data)
        except ValidationError as e:
            return Response(
                {"error": e.message if hasattr(e, 'message') else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PlanDetailSerializer(plan).data,
            status=status.HTTP_200_OK,
        )

    # ───────────────── ADD EVENT ─────────────────

    @extend_schema(
        description="Add an existing event to a plan by event_id, with optional event detail updates",
        request=AddEventToPlanSerializer,
        responses={200: PlanEventSerializer},
    )
    @action(detail=True, methods=['post'], url_path='add-event')
    @require_permission('update')
    def add_event(self, request, pk=None):
        admin = get_current_admin(request)
        serializer = AddEventToPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            event = PlanService.add_event_to_plan(
                admin, pk, serializer.validated_data
            )
        except ValidationError as e:
            return Response(
                {"error": e.message if hasattr(e, 'message') else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "تم إضافة النشاط إلى الخطة بنجاح",
                "event": PlanEventSerializer(event).data,
            },
            status=status.HTTP_200_OK,
        )

    # ───────────────── REMOVE EVENT ─────────────────

    @extend_schema(
        description="Remove an event from a plan (unlink + deactivate)",
        responses={200: dict},
        parameters=[
            OpenApiParameter(
                name='event_id',
                location=OpenApiParameter.PATH,
                type=int,
                description='The ID of the event to remove',
            )
        ],
    )
    @action(detail=True, methods=['delete'], url_path=r'remove-event/(?P<event_id>\d+)')
    @require_permission('delete')
    def remove_event(self, request, pk=None, event_id=None):
        admin = get_current_admin(request)

        try:
            event = PlanService.remove_event_from_plan(admin, pk, event_id)
        except ValidationError as e:
            return Response(
                {"error": e.message if hasattr(e, 'message') else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "تم إزالة النشاط من الخطة وإلغاء تفعيله بنجاح",
                "event_id": event.event_id,
            },
            status=status.HTTP_200_OK,
        )