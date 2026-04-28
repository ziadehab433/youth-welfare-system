from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from apps.accounts.permissions import IsRole
from ..serializers import (
    ClanSerializer,
    ScoutStatusSerializer,
)
from ..utils import (
    success_response,
    error_response,
)
from ..services.student_services import (
    ScoutValidationError,
    get_student_clan,
    get_student_clan_or_error,
    get_membership_with_details,
    get_accepted_membership,
    join_clan,
    get_dashboard_data,
)


# ============================================
# Messages
# ============================================
MSG = {
    'no_clan': "لا توجد عشيرة متاحة لكليتك حالياً",
    'clan_fetched': "تم جلب بيانات العشيرة بنجاح",
    'join_success': "تم تقديم طلب الانضمام بنجاح",
    'reapply_success': "تم إعادة تقديم طلب الانضمام بنجاح",
    'no_application': "لم تقم بتقديم طلب انضمام بعد",
    'status_fetched': "تم جلب حالة العضوية بنجاح",
    'dashboard_fetched': "تم جلب بيانات لوحة التحكم بنجاح",
}


@extend_schema(tags=["Student Scouts"])
class StudentScoutViewSet(ViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['student', 'طالب']

    # ==========================================
    # Helpers
    # ==========================================

    def _error(self, e):
        return Response(
            error_response(e.message),
            status=e.status_code
        )

    def _safe(self, fn):
        try:
            return fn()
        except ScoutValidationError as e:
            return self._error(e)

    # ==========================================
    # 1. View Clan
    # ==========================================

    @extend_schema(tags=["Student Scouts"])
    @action(detail=False, methods=['get'])
    def clan(self, request):
        """View the clan associated with student's faculty"""
        student = request.user
        clan = get_student_clan(student.faculty_id)

        if not clan:
            return Response(
                success_response(MSG['no_clan'], data=None),
                status=status.HTTP_200_OK
            )

        return Response(
            success_response(
                MSG['clan_fetched'],
                data=ClanSerializer(clan).data
            ),
            status=status.HTTP_200_OK
        )

    # ==========================================
    # 2. Join Clan
    # ==========================================

    @extend_schema(tags=["Student Scouts"])
    @action(detail=False, methods=['post'])
    def join(self, request):
        """Submit a join request — allows re-application after rejection"""
        student = request.user

        result = self._safe(
            lambda: get_student_clan_or_error(student.faculty_id)
        )
        if isinstance(result, Response):
            return result
        clan = result

        result = self._safe(
            lambda: join_clan(student.student_id, clan)
        )
        if isinstance(result, Response):
            return result

        join_type, _ = result

        if join_type == 'reapply':
            return Response(
                success_response(MSG['reapply_success']),
                status=status.HTTP_201_CREATED
            )

        return Response(
            success_response(MSG['join_success']),
            status=status.HTTP_201_CREATED
        )

    # ==========================================
    # 3. My Status
    # ==========================================

    @extend_schema(tags=["Student Scouts"])
    @action(detail=False, methods=['get'])
    def my_status(self, request):
        """Check membership request status"""
        student = request.user
        membership = get_membership_with_details(student.student_id)

        if not membership:
            return Response(
                success_response(MSG['no_application'], data=None),
                status=status.HTTP_200_OK
            )

        return Response(
            success_response(
                MSG['status_fetched'],
                data=ScoutStatusSerializer(membership).data
            ),
            status=status.HTTP_200_OK
        )

    # ==========================================
    # 4. Dashboard
    # ==========================================

    @extend_schema(tags=["Student Scouts"])
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Full dashboard for accepted members"""
        student = request.user

        result = self._safe(
            lambda: get_accepted_membership(student.student_id)
        )
        if isinstance(result, Response):
            return result

        membership = result
        dashboard = get_dashboard_data(membership)

        return Response(
            success_response(
                MSG['dashboard_fetched'],
                data=dashboard
            ),
            status=status.HTTP_200_OK
        )