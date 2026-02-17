from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from apps.event.models import Events, Prtcps
from apps.accounts.utils import get_current_student
from apps.accounts.permissions import require_permission, IsRole
from .serializers import (
    EventAvailableSerializer, 
    EventJoinedSerializer,
)
from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(tags=["Event Student APIs"])
class StudentEventViewSet(viewsets.ViewSet):
    """
    ViewSet for student-facing event operations
    """
    permission_classes = [IsRole]
    allowed_roles = ['student']

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=False, methods=['get'], url_path='available')
    def available_events(self, request):
        """
        GET /events/available/
        Returns events available for the current student based on faculty
        """
        try:
            student = get_current_student(request)
            
            today = timezone.now().date()
            print(student.faculty.faculty_id)
            
            available_events = Events.objects.filter(
                Q(faculty_id=student.faculty.faculty_id) | 
                Q(selected_facs__contains=[student.faculty.faculty_id]),
                active=True,
                status='مقبول',
                end_date__gte=today  
            ).exclude(
                prtcps_set__student=student
            ).distinct().order_by('st_date')
            
            serializer = EventAvailableSerializer(
                available_events, 
                many=True, 
                context=self.get_serializer_context()
            )
            
            return Response({
                'status': 'success',
                'count': available_events.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='join')
    def join_event(self, request, pk=None):
        """
        POST /events/{id}/join/
        Adds student to prtcps table for the specified event
        """
        try:
            student = get_current_student(request)
            
            event = get_object_or_404(Events, event_id=pk, active=True)
            
            today = timezone.now().date()
            
            if event.st_date <= today:
                return Response({
                    'status': 'error',
                    'message': 'Cannot join an event that has already started or passed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if event.end_date < today:
                return Response({
                    'status': 'error',
                    'message': 'Cannot join an event that has already ended'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            is_eligible = (
                event.faculty_id == student.faculty_id or 
                (event.selected_facs and student.faculty_id in event.selected_facs)
            )
            
            if not is_eligible:
                return Response({
                    'status': 'error',
                    'message': 'You are not eligible to join this event based on your faculty'
                }, status=status.HTTP_403_FORBIDDEN)
            
            existing_participation = Prtcps.objects.filter(
                event=event, 
                student=student
            ).first()
            
            if existing_participation:
                return Response({
                    'status': 'error',
                    'message': f'You have already joined this event (Status: {existing_participation.status})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            current_participants = Prtcps.objects.filter(
                event=event, 
                status='مقبول'
            ).count()
            
            if event.s_limit and current_participants >= event.s_limit:
                return Response({
                    'status': 'error',
                    'message': 'This event has reached its maximum participant limit'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            participation = Prtcps.objects.create(
                event=event,
                student=student,
                status='منتظر'
            )
            
            return Response({
                'status': 'success',
                'message': 'Successfully joined the event',
                'data': {
                    'participation_id': participation.id,
                    'event_id': event.event_id,
                    'event_title': event.title,
                    'status': participation.status,
                    'event_start_date': event.st_date,
                    'event_end_date': event.end_date
                }
            }, status=status.HTTP_201_CREATED)
            
        except Events.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Event not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='joined')
    def joined_events(self, request):
        """
        GET /events/joined/
        Returns events that the student has joined with status 'مقبول'
        """
        try:
            student = get_current_student(request)
            
            joined_events = Events.objects.filter(
                prtcps_set__student=student,
                prtcps_set__status='مقبول'
            ).distinct().order_by('-st_date')
            
            serializer = EventJoinedSerializer(
                joined_events, 
                many=True, 
                context=self.get_serializer_context()
            )
            
            return Response({
                'status': 'success',
                'count': joined_events.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='joined')
    def joined_events(self, request):
        """
        GET /events/joined/
        Returns events that the student has joined with status 'مقبول'
        """
        try:
            student = get_current_student(request)
            
            joined_events = Events.objects.filter(
                prtcps_set__student=student,
                prtcps_set__status='مقبول'
            ).distinct().order_by('-st_date')
            
            serializer = EventJoinedSerializer(
                joined_events, 
                many=True, 
                context=self.get_serializer_context()
            )
            
            return Response({
                'status': 'success',
                'count': joined_events.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='my-result')
    def my_result(self, request, pk=None):
        """
        GET /events/{id}/my-result/
        Returns the student's rank and reward for a specific event they participated in
        """
        try:
            student = get_current_student(request)
            
            participation = get_object_or_404(
                Prtcps,
                event_id=pk,
                student=student
            )
            
            event = get_object_or_404(Events, event_id=pk, active=True)
            
            result_data = {
                'event_id': event.event_id,
                'event_title': event.title,
                'rank': participation.rank,
                'reward': participation.reward,
                'event_start_date': event.st_date,
                'event_end_date': event.end_date
            }
            
            if participation.rank is None and participation.reward is None:
                result_data['message'] = 'Results have not been published yet for this event'
            
            return Response({
                'status': 'success',
                'data': result_data
            }, status=status.HTTP_200_OK)
            
        except Prtcps.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'You have not participated in this event'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)