from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from django.db import connection
from .models import Project, Complaint
from .serializers import (
    ProjectPublicSerializer, ProjectOwnerSerializer, ProjectAdminRegSerializer,
    ComplaintSerializer, ComplaintCreateSerializer, ComplaintResponseSerializer
)
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    filterset_fields = ["status"]
    search_fields = ["name", "site_url"]
    ordering_fields = ["created_at", "trust_score", "name"]
    def get_permissions(self):
        if self.action in ["catalog", "retrieve_public", "list"]:
            return [permissions.AllowAny()]
        if self.action in ["retrieve"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    def get_serializer_class(self):
        user = self.request.user
        if not user.is_authenticated:
            return ProjectPublicSerializer
        if user.is_superuser or getattr(user, 'role', '') in ("admin", "regulator"):
            return ProjectAdminRegSerializer
        if getattr(user, 'role', '') == 'owner':
            return ProjectOwnerSerializer
        return ProjectPublicSerializer
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not user.is_authenticated:
            return qs.only("id","name","site_url","status","trust_score","created_at")
        if user.is_superuser or getattr(user, 'role', '') in ("admin","regulator"):
            return qs.all()
        if getattr(user, 'role', '') == 'owner':
            return qs.filter(owner=user).all()
        return qs.only("id","name","site_url","status","trust_score","created_at")
    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def catalog(self, request):
        qs = Project.objects.all().only("id","name","site_url","status","trust_score","created_at")
        page = self.paginate_queryset(qs)
        ser = ProjectPublicSerializer(page, many=True)
        return self.get_paginated_response(ser.data)
    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=401)
        if getattr(user, 'role', '') in ('admin', 'regulator'):
            return Response({"detail": "Admins and regulators cannot create projects"}, status=403)
        data = request.data.copy()
        ser = ProjectOwnerSerializer(data=data)
        ser.is_valid(raise_exception=True)
        ser.save(owner=user)
        return Response(ser.data, status=201)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if user.is_superuser or getattr(user, 'role', '') == 'admin':
            return super().destroy(request, *args, **kwargs)
        if getattr(user, 'role', '') == 'owner' and instance.owner_id == user.id:
            return super().destroy(request, *args, **kwargs)
        return Response({"detail": "Forbidden"}, status=403)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def submit(self, request, pk=None):
        project = self.get_object()
        user = request.user
        if not (user.is_superuser or getattr(user, 'role','')=='admin' or (getattr(user,'role','')=='owner' and project.owner_id==user.id)):
            return Response({"detail": "Forbidden"}, status=403)
        project.status = Project.Status.SUBMITTED
        project.save(update_fields=["status","updated_at"])
        return Response({"id": str(project.id), "status": project.status})
    @action(detail=True, methods=["post"], url_path="complaints", permission_classes=[permissions.IsAuthenticated])
    def create_complaint(self, request, pk=None):
        user = request.user
        if user.is_superuser or getattr(user, 'role', '') in ('admin', 'regulator', 'owner'):
            return Response({
                "detail": "Government officials and business owners cannot submit complaints"
            }, status=status.HTTP_403_FORBIDDEN)
        project = self.get_object()
        serializer = ComplaintCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complaint = serializer.save(
            project=project,
            author=user
        )
        return Response({
            "id": str(complaint.id),
            "message": "Complaint submitted successfully"
        }, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=["get"], url_path="complaints", permission_classes=[permissions.IsAuthenticated])
    def list_complaints(self, request, pk=None):
        user = request.user
        if not (user.is_superuser or getattr(user,'role','') in ("admin","regulator")):
            return Response({"detail": "Forbidden"}, status=403)
        project = self.get_object()
        qs = project.complaints.all().select_related("author", "responded_by")
        serializer = ComplaintSerializer(qs, many=True)
        return Response(serializer.data)
class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all().select_related("project", "author", "responded_by")
    serializer_class = ComplaintSerializer
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    def create(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser or getattr(user, 'role', '') in ('admin', 'regulator'):
            return Response({
                "detail": "Government officials cannot submit complaints. You can only view and respond to complaints."
            }, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Complaint.objects.none()
        if user.is_superuser or getattr(user, 'role', '') in ('admin', 'regulator'):
            return super().get_queryset()
        return super().get_queryset().filter(author=user)
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def respond(self, request, pk=None):
        complaint = self.get_object()
        user = request.user
        if not (user.is_superuser or getattr(user, 'role', '') in ('admin', 'regulator')):
            return Response({"detail": "Only regulators can respond to complaints"},
                          status=status.HTTP_403_FORBIDDEN)
        serializer = ComplaintResponseSerializer(complaint, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        complaint.responded_by = user
        if complaint.status == Complaint.Status.OPEN:
            complaint.status = Complaint.Status.INVESTIGATING
        if serializer.validated_data.get('status') == Complaint.Status.RESOLVED:
            complaint.resolved_at = timezone.now()
        serializer.save()
        return Response({
            "message": "Response submitted successfully",
            "complaint": ComplaintSerializer(complaint).data
        })
class DashboardStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        stats = {}
        total_projects = Project.objects.count()
        stats['total_projects'] = total_projects
        if user.is_superuser or getattr(user, 'role', '') in ('admin', 'regulator'):
            complaints = Complaint.objects.all()
            stats.update({
                'market_integrity_index': 78,
                'active_complaints': complaints.filter(status=Complaint.Status.OPEN).count(),
                'avg_response_time_days': 12.5,
                'enforcement_rate': 34,
                'complaint_stats': {
                    'total': complaints.count(),
                    'open': complaints.filter(status=Complaint.Status.OPEN).count(),
                    'investigating': complaints.filter(status=Complaint.Status.INVESTIGATING).count(),
                    'resolved': complaints.filter(status=Complaint.Status.RESOLVED).count(),
                    'dismissed': complaints.filter(status=Complaint.Status.DISMISSED).count(),
                }
            })
            projects = Project.objects.all()
            avg_trust = projects.aggregate(avg_trust=Avg('trust_score'))['avg_trust'] or 0
            stats['project_stats'] = {
                'avg_trust_score': round(avg_trust, 1),
                'total_projects': projects.count(),
                'high_risk_projects': projects.filter(trust_score__lt=50).count(),
                'medium_risk_projects': projects.filter(trust_score__gte=50, trust_score__lt=75).count(),
                'low_risk_projects': projects.filter(trust_score__gte=75).count(),
            }
        elif getattr(user, 'role', '') == 'owner':
            user_projects = Project.objects.filter(owner=user)
            avg_trust = user_projects.aggregate(avg_trust=Avg('trust_score'))['avg_trust'] or 0
            stats.update({
                'trust_score': round(avg_trust, 1),
                'compliance_rate': 98,
                'total_evaluations': user_projects.count(),
                'issues_to_resolve': 2,
            })
        else:
            stats.update({
                'verified_evaluations': 0,
                'avg_transparency_score': 0,
                'dark_patterns_found': 0,
            })
        recent_projects = Project.objects.all().order_by('-created_at')[:5]
        stats['recent_evaluations'] = [
            {
                'id': str(p.id),
                'name': p.name,
                'site_url': p.site_url,
                'status': p.status,
                'trust_score': p.trust_score or 0,
                'created_at': p.created_at.isoformat(),
            }
            for p in recent_projects
        ]
        return Response(stats)
        return Response(ser.data)
class RegulatorStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        if not (user.is_superuser or getattr(user,'role','') in ("admin","regulator")):
            return Response({"detail": "Forbidden"}, status=403)
        agg = Project.objects.aggregate(total=Count("id"), avg_score=Avg("trust_score"))
        by_status = Project.objects.values("status").annotate(c=Count("id")).order_by()
        return Response({"projects": agg, "by_status": list(by_status)})
class RegulatorExpandedStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        if not (user.is_superuser or getattr(user,'role','') in ("admin","regulator")):
            return Response({"detail": "Forbidden"}, status=403)
        days = int(request.query_params.get('days', 30))
        now = timezone.now()
        since = now - timedelta(days=days)
        agg = Project.objects.aggregate(total=Count("id"), avg_score=Avg("trust_score"))
        by_status = list(Project.objects.values("status").annotate(c=Count("id")).order_by())
        daily_projects = list(
            Project.objects.filter(created_at__gte=since)
            .extra(select={'day': "DATE(created_at)"}).values('day').annotate(c=Count('id')).order_by('day')
        )
        return Response({"window_days": days, "projects": {"summary": agg, "by_status": by_status, "daily_created": daily_projects}})
class RegulatorLatencyStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        from app.processing.models import Task
        user = request.user
        if not (user.is_superuser or getattr(user,'role','') in ("admin","regulator")):
            return Response({"detail": "Forbidden"}, status=403)
        days = int(request.query_params.get('days', 30))
        table = Task._meta.db_table
        with connection.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                  EXTRACT(EPOCH FROM percentile_cont(0.5) WITHIN GROUP (ORDER BY (finished_at - started_at))) AS p50,
                  EXTRACT(EPOCH FROM percentile_cont(0.95) WITHIN GROUP (ORDER BY (finished_at - started_at))) AS p95
                FROM {table}
                WHERE status = 'done' AND started_at IS NOT NULL AND finished_at IS NOT NULL
                  AND finished_at >= NOW() - INTERVAL %s
                """,
                [f"{days} days"]
            )
            row = cur.fetchone()
        return Response({"window_days": days, "p50_seconds": row[0], "p95_seconds": row[1]})
class DashboardStatsView(APIView):
    """API endpoint for dashboard statistics"""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        role = getattr(user, 'role', '')
        if role in ('admin', 'regulator'):
            return self.get_regulator_stats()
        elif role == 'owner':
            return self.get_business_stats(user)
        else:
            return self.get_individual_stats(user)
    def get_regulator_stats(self):
        """Get regulatory dashboard statistics"""
        from django.db.models import Q, F
        complaint_stats = Complaint.objects.aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(status='open')),
            investigating=Count('id', filter=Q(status='investigating')),
            resolved=Count('id', filter=Q(status='resolved')),
            dismissed=Count('id', filter=Q(status='dismissed'))
        )
        resolved_complaints = Complaint.objects.filter(
            status='resolved',
            resolved_at__isnull=False
        ).annotate(
            response_time_days=F('resolved_at') - F('created_at')
        )
        avg_response_time = 0
        if resolved_complaints.exists():
            total_seconds = sum([
                c.response_time_days.total_seconds()
                for c in resolved_complaints
            ])
            avg_response_time = total_seconds / (resolved_complaints.count() * 86400)
        enforcement_rate = 0
        if complaint_stats['total'] > 0:
            enforcement_rate = (complaint_stats['resolved'] / complaint_stats['total']) * 100
        project_stats = Project.objects.aggregate(
            avg_trust_score=Avg('trust_score'),
            total_projects=Count('id'),
            high_risk_projects=Count('id', filter=Q(trust_score__lt=30)),
            medium_risk_projects=Count('id', filter=Q(trust_score__gte=30, trust_score__lt=70)),
            low_risk_projects=Count('id', filter=Q(trust_score__gte=70))
        )
        market_integrity_index = project_stats['avg_trust_score'] or 0
        return Response({
            'market_integrity_index': round(market_integrity_index, 1),
            'active_complaints': complaint_stats['open'] + complaint_stats['investigating'],
            'avg_response_time_days': round(avg_response_time, 1),
            'enforcement_rate': round(enforcement_rate, 1),
            'complaint_stats': complaint_stats,
            'project_stats': project_stats,
            'recent_evaluations': self.get_recent_evaluations()
        })
    def get_business_stats(self, user):
        """Get business dashboard statistics"""
        user_projects = Project.objects.filter(owner=user)
        project_stats = user_projects.aggregate(
            total=Count('id'),
            avg_trust_score=Avg('trust_score'),
            pending=Count('id', filter=Q(status='pending')),
            submitted=Count('id', filter=Q(status='submitted')),
            approved=Count('id', filter=Q(status='approved'))
        )
        compliance_rate = 100
        if project_stats['total'] > 0:
            compliant_projects = user_projects.filter(trust_score__gte=70).count()
            compliance_rate = (compliant_projects / project_stats['total']) * 100
        issues_to_resolve = user_projects.filter(trust_score__lt=50).count()
        return Response({
            'trust_score': round(project_stats['avg_trust_score'] or 85, 1),
            'compliance_rate': round(compliance_rate, 1),
            'total_evaluations': project_stats['total'],
            'issues_to_resolve': issues_to_resolve,
            'project_stats': project_stats,
            'recent_evaluations': self.get_recent_evaluations(user)
        })
    def get_individual_stats(self, user):
        """Get individual user dashboard statistics"""
        project_stats = Project.objects.aggregate(
            total=Count('id'),
            avg_trust_score=Avg('trust_score'),
            verified=Count('id', filter=Q(status='approved')),
            dark_patterns_found=Count('id', filter=Q(trust_score__lt=50))
        )
        return Response({
            'total_evaluations': project_stats['total'],
            'verified_evaluations': project_stats['verified'],
            'avg_transparency_score': round(project_stats['avg_trust_score'] or 0, 1),
            'dark_patterns_found': project_stats['dark_patterns_found'],
            'recent_evaluations': self.get_recent_evaluations()
        })
    def get_recent_evaluations(self, user=None):
        """Get recent evaluations"""
        queryset = Project.objects.all()
        if user:
            queryset = queryset.filter(owner=user)
        recent = queryset.order_by('-created_at')[:5].values(
            'id', 'name', 'site_url', 'status', 'trust_score', 'created_at'
        )
        return list(recent)
