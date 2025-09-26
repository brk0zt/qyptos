from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import CloudGroup, GroupFeed, GroupFile
from .serializers import GroupFeedSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def group_feed(request, group_id):
    try:
        group = CloudGroup.objects.get(id=group_id)
    except CloudGroup.DoesNotExist:
        return Response({"error": "Group not found"}, status=404)

    feed_items = GroupFeed.objects.filter(group=group)
    serializer = GroupFeedSerializer(feed_items, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_announcement(request, group_id):
    try:
        group = CloudGroup.objects.get(id=group_id, owner=request.user)
    except CloudGroup.DoesNotExist:
        return Response({"error": "Only group owner can add announcements"}, status=403)

    content = request.data.get("content")
    if not content:
        return Response({"error": "Content required"}, status=400)

    feed_item = GroupFeed.objects.create(
        group=group,
        user=request.user,
        feed_type="announcement",
        content=content,
    )
    serializer = GroupFeedSerializer(feed_item)
    return Response(serializer.data, status=201)

