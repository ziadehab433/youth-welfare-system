from jsonschema import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from apps.family.serializers import AvailableFamiliesSerializer, CreateFamilyRequestSerializer, FamilyMembersDetailSerializer, JoinFamilySerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiTypes

from apps.family.serializers import * 
from apps.family.services.family_service import FamilyService
from apps.accounts.utils import get_current_student
from apps.accounts.permissions import IsRole

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

class StudentFamilyViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['student']  # Student role - adjust based on your role names
    serializer_class = StudentFamiliesSerializer
    
    @extend_schema(
        tags=["Student Family APIs"],
        description="Retrieve all families the student is a member of",
        responses={200: StudentFamiliesSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='families')
    def list_families(self, request):
        """Get all families where current student is a member"""
        try:
            student = get_current_student(request)  # You'll need to implement this
            
            family_memberships = FamilyService.get_families_for_student(student)
            serializer = StudentFamiliesSerializer(family_memberships, many=True)
            
            return Response({
                'count': family_memberships.count(),
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        



    
    @extend_schema(
        tags=["Student Family APIs"],
        description="Get all families available for student to join",
        responses={200: AvailableFamiliesSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='available')
    def available_families(self, request):
        """Get families student can join (not full, not member, meets faculty/type criteria)"""
        try:
            student = get_current_student(request)
            
            # Check if student has a faculty assigned
            if not student.faculty:
                return Response(
                    {'error': 'Student is not assigned to any faculty'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            available_families = FamilyService.get_available_families_for_student(student)
            serializer = AvailableFamiliesSerializer(available_families, many=True)
            
            return Response({
                'count': len(available_families),
                'data': serializer.data
            })
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        



    @extend_schema(
        tags=["Student Family APIs"],
        description="Get all members of a family (founders only)",
        responses={200: FamilyMembersDetailSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='members')
    def family_members(self, request, pk=None):
        """Get all members of a family - FOUNDERS ONLY"""
        try:
            student = get_current_student(request)
            
            family, members = FamilyService.get_family_members(
                family_id=pk,
                requester_student=student
            )
            
            # Optional: Filter by role
            role = request.query_params.get('role')
            if role:
                members = members.filter(role=role)
            
            # Optional: Filter by status
            status_filter = request.query_params.get('status')
            if status_filter:
                members = members.filter(status=status_filter)
            
            # Optional: Search by name
            search = request.query_params.get('search')
            if search:
                members = members.filter(student__name__icontains=search)
            
            serializer = FamilyMembersDetailSerializer(members, many=True)
            
            return Response({
                'family_id': family.family_id,
                'family_name': family.name,
                'total_members': members.count(),
                'members': serializer.data
            })
        
        except ValidationError as e:
            error_msg = str(e)
            if "founders" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif "not found" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

#join


    
    @extend_schema(
        tags=["Student Family APIs"],
        description="Join a family",
        request=None,
        responses={
            201: JoinFamilySerializer,
            400: OpenApiResponse(description="Bad request"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='join')
    def join_family(self, request, pk=None):
        """Join a family"""
        try:
            student = get_current_student(request)
            
            # Join the family
            member = FamilyService.join_family(
                family_id=pk,
                student=student
            )
            
            # Get family info for response
            family = member.family
            
            return Response({
                'message': f'Successfully joined {family.name}',
                'family_id': family.family_id,
                'family_name': family.name,
                'role': member.role,
                'status': member.status,
                'joined_at': member.joined_at
            }, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            error_msg = str(e)
            
            if "already a member" in error_msg:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif "not found" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_404_NOT_FOUND
                )
            elif "full" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif "only for" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif "not assigned" in error_msg:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        




# CREATE REQUEST TO CREATE FAMILY 

    @extend_schema(
        tags=["Student Family APIs"],
        description="Create a new family request with detailed configuration",
        request=CreateFamilyRequestSerializer,
        responses={
            201: FamilyRequestDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            409: OpenApiResponse(description="Conflict error"),
            500: OpenApiResponse(description="Server error")
        }
    )
    @action(detail=False, methods=['post'], url_path='create')
    def create_family_request(self, request):
        """
        Create a new family request with complete configuration:
        - Family type (نوعية/مركزية)
        - 9 default role members (4 admins + 5 students)
        - 7 committees with heads, assistants, and activities

        All student UIDs refer to university ID (student_id), not national ID
        """
        try:
            student = get_current_student(request)

            # Validate request data
            serializer = CreateFamilyRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            # Create family request
            family = FamilyService.create_family_request(
                request_data=validated_data,
                created_by_student=student
            )

            # Serialize and return the created family
            response_serializer = FamilyRequestDetailSerializer(family)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)

            # Check for conflict errors
            if any(keyword in error_msg for keyword in [
                "مسؤول بالفعل",
                "طلب أسرة قيد الانتظار",
                "مكلفين بأدوار"
            ]):
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_409_CONFLICT
                )

            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'خطأ غير متوقع: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

###########

    
    @extend_schema(
        tags=["Student Family APIs"],
        description="Retrieve all family creation requests submitted by the student",
        responses={200: FamilyRequestListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='family_creation_request')
    def family_creation_requests(self, request):
        """Get all family creation requests submitted by student"""
        try:
            student = get_current_student(request)
            
            # Get all requests
            requests_qs = FamilyService.get_student_family_requests(student)
            
            # Optional: Filter by status
            status_filter = request.query_params.get('status')
            if status_filter:
                requests_qs = requests_qs.filter(status=status_filter)
            
            # Serialize
            serializer = FamilyRequestListSerializer(requests_qs, many=True)
            
            # Get statistics
            stats = FamilyService.get_request_statistics(student)
            
            return Response({
                'count': requests_qs.count(),
                'statistics': stats,
                'requests': serializer.data
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    



#Posts

    
    @extend_schema(
        tags=["Student Family APIs"],
        description="Create a new post in a family (president/vice president only)",
        request=CreatePostSerializer,
        responses={
            201: FamilyPostSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Forbidden - not president/vice president"),
            404: OpenApiResponse(description="Family not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='post')
    def create_family_post(self, request, pk=None):
        """Create a new post in a family (president/vice president only)"""
        try:
            student = get_current_student(request)
            
            # Validate request data
            serializer = CreatePostSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            
            # Create post
            post = FamilyService.create_family_post(
                family_id=pk,
                student=student,
                title=validated_data['title'],
                description=validated_data['description']
            )

            
            result_serializer = FamilyPostSerializer(post)
            return Response(
                {
                    'message': 'Post created successfully',
                    'post': result_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            error_msg = str(e)
            
            if "not found" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_404_NOT_FOUND
                )
            elif "president" in error_msg.lower() or "vice president" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_403_FORBIDDEN
                )
            else:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @extend_schema(
        tags=["Student Family APIs"],
        description="Get all posts in a family (members only)",
        responses={200: FamilyPostSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='posts')
    def list_family_posts(self, request, pk=None):
        """Get all posts in a family (members only)"""
        try:
            student = get_current_student(request)
            
            # Get posts
            posts = FamilyService.get_family_posts(
                family_id=pk,
                student=student
            )
            
            # Optional: Filter by search
            search = request.query_params.get('search')
            if search:
                posts = posts.filter(title__icontains=search) | \
                        posts.filter(description__icontains=search)
            
            # Optional: Sort (default: newest first)
            sort_by = request.query_params.get('sort_by', '-created_at')
            if sort_by in ['created_at', '-created_at', 'updated_at', '-updated_at']:
                posts = posts.order_by(sort_by)
            
            serializer = FamilyPostSerializer(posts, many=True)
            
            return Response({
                'count': posts.count(),
                'posts': serializer.data
            })
        
        except ValidationError as e:
            error_msg = str(e)
            
            if "not found" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_404_NOT_FOUND
                )
            elif "not a member" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_403_FORBIDDEN
                )
            else:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        



# fam std dash board
    
    @extend_schema(
        tags=["Student Family APIs"],
        description="Get family dashboard data (founders only)",
        responses={
            200: FamilyDashboardSerializer,
            403: OpenApiResponse(description="Not a founder"),
            404: OpenApiResponse(description="Family not found")
        }
    )
    @action(detail=True, methods=['get'], url_path='dashboard')
    def family_dashboard(self, request, pk=None):
        """Get family dashboard for founder"""
        try:
            student = get_current_student(request)
            
            # Get dashboard data
            dashboard_data = FamilyService.get_family_dashboard(
                family_id=pk,
                student=student
            )
            
            return Response(dashboard_data)
        
        except ValidationError as e:
            error_msg = str(e)
            
            if "not found" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_404_NOT_FOUND
                )
            elif "not a founder" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_403_FORBIDDEN
                )
            else:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

# fam events


    @extend_schema(
        tags=["Student Family Event Requests"],
        description="Create a new event request (president/vice president only)",
        request=CreateEventRequestSerializer,
        responses={
            201: EventRequestResponseSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Family not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='event_request')
    def create_event_request(self, request, pk=None):
        """Create a new event request"""
        try:
            student = get_current_student(request)
            
            # Validate request data
            serializer = CreateEventRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            
            # Create event request
            event, student_creator, admin = FamilyService.create_event_request(
                family_id=pk,
                student=student,
                event_data=validated_data
            )
            
            # Refresh with related data
            event = Events.objects.select_related(
                'family', 'faculty', 'created_by'
            ).get(event_id=event.event_id)
            
            result_serializer = EventRequestResponseSerializer(
                event,
                context={'created_by_student': student_creator}
            )
            return Response(
                {
                    'message': 'Event request created successfully. Waiting for faculty admin approval.',
                    'event': result_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            error_msg = str(e)
            
            if "not found" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_404_NOT_FOUND
                )
            elif "president" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif "no admin" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @extend_schema(
        tags=["Student Family Event Requests"],
        description="Get all event requests for a family",
        responses={200: EventRequestResponseSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='event_requests')
    def list_event_requests(self, request, pk=None):
        """Get all event requests for the family"""
        try:
            student = get_current_student(request)
            
            # Check if user is president
            is_president = FamilyMembers.objects.filter(
                family_id=pk,
                student=student,
                role__in=['أخ أكبر', 'أخت كبرى']
            ).exists()
            
            if is_president:
                # Presidents see all event requests
                events = FamilyService.get_family_event_requests(
                    family_id=pk,
                    student=student
                )
            else:
                # Regular members see only approved events
                events = FamilyService.get_family_approved_events(
                    family_id=pk,
                    student=student
                )
            
            # Optional: Filter by status (presidents only)
            if is_president:
                status_filter = request.query_params.get('status')
                if status_filter:
                    events = events.filter(status=status_filter)
            
            events = events.select_related('family', 'faculty', 'created_by')
            
            serializer = EventRequestResponseSerializer(
                events,
                many=True,
                context={'created_by_student': student}
            )
            
            return Response({
                'count': events.count(),
                'is_president': is_president,
                'events': serializer.data
            })
        
        except ValidationError as e:
            error_msg = str(e)
            
            if "not found" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_404_NOT_FOUND
                )
            elif "not a member" in error_msg.lower():
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_403_FORBIDDEN
                )
            else:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )