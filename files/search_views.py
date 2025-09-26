from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Q
from .models import CloudGroup, GroupFile, File
from .serializers import CloudGroupSerializer, GroupFileSerializer, FileSerializer
from rest_framework.pagination import LimitOffsetPagination

class PublicSearchPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100

class SearchView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = PublicSearchPagination

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        type_ = request.query_params.get('type', 'all').lower()  # 'groups', 'group_files', 'files', or 'all'
        if not q:
            return Response({"detail": "q param is required"}, status=400)

        paginator = self.get_paginator()
        results = []

        if type_ in ['all', 'groups']:
            groups_qs = CloudGroup.objects.filter(is_public=True).filter(
                Q(name__icontains=q)
            ).order_by('-id')
            page = paginator.paginate_queryset(groups_qs, request)
            groups_ser = CloudGroupSerializer(page, many=True, context={'request': request})
            results.append({'type': 'groups', 'items': groups_ser.data})
            # if specific type requested, return only groups
            if type_ == 'groups':
                return paginator.get_paginated_response(groups_ser.data)

        if type_ in ['all', 'group_files']:
            gf_qs = GroupFile.objects.filter(is_public=True, group__is_public=True).filter(
                Q(file__icontains=q) | Q(uploader__username__icontains=q)
            ).order_by('-uploaded_at')
            page = paginator.paginate_queryset(gf_qs, request)
            gf_ser = GroupFileSerializer(page, many=True, context={'request': request})
            results.append({'type': 'group_files', 'items': gf_ser.data})
            if type_ == 'group_files':
                return paginator.get_paginated_response(gf_ser.data)

        if type_ in ['all', 'files']:
            files_qs = File.objects.filter(is_public=True).filter(
                Q(file__icontains=q) | Q(owner__username__icontains=q)
            ).order_by('-uploaded_at')
            page = paginator.paginate_queryset(files_qs, request)
            f_ser = FileSerializer(page, many=True, context={'request': request})
            results.append({'type': 'files', 'items': f_ser.data})
            if type_ == 'files':
                return paginator.get_paginated_response(f_ser.data)

                    # If 'all', return aggregated results (note: pagination used per-section above)
        return Response({'results': results})

@api_view(['GET'])
def search_view(request):
    query = request.GET.get("q", "")
    search_type = request.GET.get("type", "all")

    limit = int(request.GET.get("limit", 10))
    offset = int(request.GET.get("offset", 0))

    results = {}

    if search_type in ["all", "groups"]:
        groups = CloudGroup.objects.filter(
            is_public=True,
            name__icontains=query
        )[offset:offset+limit]
        results["groups"] = CloudGroupSerializer(groups, many=True).data

    if search_type in ["all", "files"]:
        files = File.objects.filter(
            is_public=True,
            file__icontains=query
        )[offset:offset+limit]
        results["files"] = FileSerializer(files, many=True).data

    if search_type in ["all", "group_files"]:
        group_files = GroupFile.objects.filter(
            is_public=True,
            file__icontains=query
        )[offset:offset+limit]
        results["group_files"] = GroupFileSerializer(group_files, many=True).data

    return Response(results)
