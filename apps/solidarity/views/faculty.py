import asyncio
from asyncio.log import logger
from django.db import DatabaseError
from django.http import HttpResponse
from django.template.loader import render_to_string

from apps.solidarity.models import Solidarities

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError , PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiTypes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound 

from apps.accounts.permissions import IsRole
from apps.solidarity.models import Solidarities
from apps.solidarity.serializers import (
    SolidarityListSerializer,
    SolidarityDetailSerializer,
    FacultyDiscountUpdateSerializer,
)
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from apps.solidarity.serializers import DeptFacultySummarySerializer
from apps.solidarity.services.solidarity_service import SolidarityService
from ..serializers import FacultyApprovedResponseSerializer, SolidarityApprovedRowSerializer
from ..serializers import DiscountAssignSerializer, SolidarityDocsSerializer
from apps.solidarity.utils import get_current_student, get_current_admin, handle_report_data, html_to_pdf_buffer, get_client_ip
from apps.solidarity.services.solidarity_service import SolidarityService
from ..utils import get_arabic_discount_type


class FacultyAdminSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [ IsRole]
    allowed_roles = ['مسؤول كلية']
    serializer_class = SolidarityListSerializer

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="List all solidarity applications for the current faculty admin",
        responses={200: SolidarityListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='applications')
    def list_applications(self, request):
        admin = get_current_admin(request)
        qs = SolidarityService.get_applications_for_review(admin)
        return Response(SolidarityListSerializer(qs, many=True).data)

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Retrieve details of a specific solidarity application",
        responses={200: SolidarityDetailSerializer, 403: OpenApiResponse(description="Forbidden"), 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['get'], url_path='applications')
    def get_application(self, request, pk=None):
        client_ip = get_client_ip(request)

        admin = get_current_admin(request)
        try:
            solidarity = SolidarityService.get_application_detail(pk, admin)
        except ValidationError as e:
            msg = str(e)
            if "from your faculty" in msg:
                return Response({'error': msg}, status=status.HTTP_403_FORBIDDEN)
            elif "not found" in msg.lower():
                return Response({'error': msg}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
            #  Log that this admin viewed the solidarity details

        SolidarityService.log_data_access(
            actor_id=admin.admin_id,
            actor_type=admin.role,
            action='عرض بيانات الطلب',      # “Viewed solidarity details”
            target_type='تكافل',
            solidarity_id=pk,
            ip_address=client_ip

        )
        return Response(SolidarityDetailSerializer(solidarity).data)

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Retrieve all uploaded documents for a specific solidarity application",
        responses={200: SolidarityDocsSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='documents')
    def get_documents(self, request, pk=None):

        admin = get_current_admin(request)
        docs_qs = SolidarityService.get_docs_by_solidarity_id(pk)

        docs = SolidarityService.get_docs_by_solidarity_id(pk)
        if not docs.exists():
            return Response({'detail': 'No documents found for this solidarity_id'}, status=404)
           # # Log document access
        solidarity = docs_qs.first().solidarity 
        if admin.faculty_id != solidarity.faculty_id:
           raise PermissionDenied("You can only view applications from your faculty.")      
        client_ip = get_client_ip(request)

        SolidarityService.log_data_access(
        actor_id=admin.admin_id,
        actor_type=admin.role,
        action='عرض مستندات الطلب',     # “Viewed solidarity documents”
        target_type='تكافل',
        solidarity_id=pk,
        ip_address=client_ip
    )
       # ""

        return Response(SolidarityDocsSerializer(docs, many=True , context={'request': request}).data)


    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Approve a solidarity application",
        responses={200: OpenApiResponse(description="Application approved successfully")}
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        admin = get_current_admin(request)
        result = SolidarityService.approve_application(pk, admin)
        return Response({'message': result['message']})

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Pre-approve a solidarity application before final approval",
        responses={200: OpenApiResponse(description="Application pre-approved successfully")}
    )
    @action(detail=True, methods=['post'], url_path='pre_approve')
    def pre_approve(self, request, pk=None):
        admin = get_current_admin(request)
        result = SolidarityService.pre_approve_application(pk, admin)
        return Response({'message': result['message']})

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Reject a solidarity application",
        responses={200: OpenApiResponse(description="Application rejected successfully")}
    )
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        admin = get_current_admin(request)
        result = SolidarityService.reject_application(pk, admin)
        return Response({'message': result['message']})





    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Assign discount(s) to a solidarity application",
        request=DiscountAssignSerializer,
        responses={
            200: OpenApiResponse(description="Discount assigned successfully"),
            400: OpenApiResponse(description="Invalid input data"),
            404: OpenApiResponse(description="Solidarity application not found")
        }
    )
    @action(detail=True, methods=['patch'], url_path='assign_discount')
    def assign_discount(self, request, pk=None):
        try:
            admin = get_current_admin(request)
            serializer = DiscountAssignSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            discount_data = serializer.validated_data['discounts']
            
            solidarity = SolidarityService.get_application_detail(pk, admin)
            updated_solidarity = SolidarityService.assign_discounts(
                admin, 
                solidarity, 
                discount_data
            )

            return Response({
                "message": "تم تطبيق الخصم بنجاح",
                "solidarity_id": updated_solidarity.solidarity_id,
                "total_discount": float(updated_solidarity.total_discount) if updated_solidarity.total_discount else None,
                "discount_types": updated_solidarity.discount_type,  # Returns Arabic
                "discounts_applied": [
                    {
                        "type": get_arabic_discount_type(d['discount_type']),  # Convert to Arabic
                        "value": float(d['discount_value'])
                    } for d in discount_data
                ],
                "updated_at": updated_solidarity.updated_at.isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in assign_discount: {str(e)}")
            return Response({
                "error": f"حدث خطأ أثناء تطبيق الخصم: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
    

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Update faculty discount values for the current faculty",
        request=FacultyDiscountUpdateSerializer,
        responses={200: OpenApiResponse(description="Faculty discounts updated successfully")}
    )
    @action(detail=False, methods=['patch'], url_path='update_faculty_discounts')
    def update_faculty_discounts(self, request):
        admin = get_current_admin(request)
        serializer = FacultyDiscountUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_faculty = SolidarityService.update_faculty_discounts(admin, serializer.validated_data)
        return Response({
            "message": "تم تحديث خصومات الكلية بنجاح",
            "faculty_discounts": {
                "aff_discount": updated_faculty.aff_discount,
                "reg_discount": updated_faculty.reg_discount,
                "bk_discount": updated_faculty.bk_discount,
                "full_discount": updated_faculty.full_discount,
            }
        })

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Get current faculty discount values",
        responses={200: OpenApiResponse(description="Faculty discounts retrieved successfully")}
    )
    @action(detail=False, methods=['get'], url_path='faculty/discounts')
    def get_faculty_discounts(self, request):
        admin = get_current_admin(request)
        faculty = admin.faculty
        data = {
            "aff_discount": faculty.aff_discount,
            "reg_discount": faculty.reg_discount,
            "bk_discount": faculty.bk_discount,
            "full_discount": faculty.full_discount
        }
        return Response({
            "message": "تم جلب خصومات الكلية بنجاح",
            "discounts": data
        })
    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Get approved applications summary for faculty admin",
        responses={200: FacultyApprovedResponseSerializer}  
    )
    @action(detail=False, methods=['get'], url_path='faculty_approved')
    def faculty_approved(self, request):
        admin = get_current_admin(request)
        rows_qs, totals = SolidarityService.get_approved_for_faculty_admin(admin)

        rows = []
        for r in rows_qs:
            rows.append({
                'solidarity_id': r['solidarity_id'],
                'student_name': r['student_name'],
                'student_id': r['student_pk'],
                'total_income': r.get('total_income') or 0,
                'discount_amount': r.get('total_discount_coalesced') or 0
            })

        serializer = SolidarityApprovedRowSerializer(rows, many=True)
        return Response({
            'total_approved': totals['total_approved'],
            'total_discount': totals['total_discount'],
            'results': serializer.data
        })

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="pdf",
        responses={
            200: OpenApiResponse(
                description="PDF file download",
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        admin = get_current_admin(request)

        try: 
            data = Solidarities.objects.filter(faculty=admin.faculty)
        except DatabaseError:
            return Response({'detail': 'database error while fetching data'}, status=500)

        if not data.exists:
            return Response({'detail': 'Cant generate a report (no data)'}, status=422)

        html_content = render_to_string("api/solidarity-report.html", handle_report_data(data))

        try:
            buffer = asyncio.new_event_loop().run_until_complete(
                html_to_pdf_buffer(html_content)
            )        
        except Exception:
            return Response({'detail': 'could not generate pdf'}, status=500)
        
        response = HttpResponse( 
            buffer,
            content_type='application/pdf'
        )

        response['Content-Disposition'] = f'attachment; filename="generated_pdf.pdf"'
        
        return response