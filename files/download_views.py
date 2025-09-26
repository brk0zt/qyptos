import os
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import File


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id)

    file_path = file_obj.file.path
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range", "").strip()

    if range_header:
        # Örn: "bytes=0-1023"
        range_value = range_header.split("=")[1]
        start, end = range_value.split("-")
        start = int(start)
        end = int(end) if end else file_size - 1
        length = end - start + 1

        with open(file_path, "rb") as f:
            f.seek(start)
            data = f.read(length)

        response = HttpResponse(data, status=206, content_type="application/octet-stream")
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(length)
        response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response

    else:
        # Normal indirme (tam dosya)
        response = FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))
        response["Accept-Ranges"] = "bytes"
        return response

