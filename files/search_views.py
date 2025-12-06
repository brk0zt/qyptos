# search_views.py
# -*- coding: utf-8 -*-
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Q
from .models import CloudGroup, GroupFile, File
from .serializers import CloudGroupSerializer, GroupFileSerializer, FileSerializer

class SearchView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        type_ = request.query_params.get('type', 'all').lower()
        
        if not q:
            return Response({"detail": "q param is required"}, status=400)

        results = {}

        try:
            if type_ in ['all', 'groups']:
                groups_qs = CloudGroup.objects.filter(
                    is_public=True
                ).filter(
                    Q(name__icontains=q)
                ).order_by('-id')
                
                groups_ser = CloudGroupSerializer(groups_qs, many=True, context={'request': request})
                results['groups'] = groups_ser.data

            if type_ in ['all', 'files']:
                files_qs = File.objects.filter(
                    is_public=True
                ).filter(
                    Q(file__icontains=q) | 
                    Q(owner__username__icontains=q)
                ).order_by('-uploaded_at')
                
                files_ser = FileSerializer(files_qs, many=True, context={'request': request})
                results['files'] = files_ser.data

            if type_ in ['all', 'group_files']:
                gf_qs = GroupFile.objects.filter(
                    is_public=True, 
                    group__is_public=True
                ).filter(
                    Q(file__icontains=q) | 
                    Q(uploader__username__icontains=q)
                ).order_by('-uploaded_at')
                
                gf_ser = GroupFileSerializer(gf_qs, many=True, context={'request': request})
                results['group_files'] = gf_ser.data

            return Response({'results': results})

        except Exception as e:
            return Response({"error": f"Search error: {str(e)}"}, status=500)

@api_view(['GET'])
def search_view(request):
    query = request.GET.get("q", "")
    search_type = request.GET.get("type", "all")

    try:
        results = {}

        if search_type in ["all", "groups"]:
            groups = CloudGroup.objects.filter(
                is_public=True,
                name__icontains=query
            )
            results["groups"] = CloudGroupSerializer(groups, many=True, context={'request': request}).data

        if search_type in ["all", "files"]:
            files = File.objects.filter(
                is_public=True,
                file__icontains=query
            )
            results["files"] = FileSerializer(files, many=True, context={'request': request}).data

        if search_type in ["all", "group_files"]:
            group_files = GroupFile.objects.filter(
                is_public=True,
                file__icontains=query
            )
            results["group_files"] = GroupFileSerializer(group_files, many=True, context={'request': request}).data

        return Response(results)
    
    except Exception as e:
        return Response({"error": f"Search error: {str(e)}"}, status=500)