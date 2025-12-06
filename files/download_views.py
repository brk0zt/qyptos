import os
from django.http import FileResponse, HttpResponse, JsonResponse, HttpResponseGone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import File

def consume_file(request, file_id):
    if request.method == 'POST':
        file_obj = get_object_or_404(File, id=file_id)
        
        if not file_obj.one_time_view:
            return JsonResponse({'detail': 'Bu dosya tek gösterimlik deðil.'}, status=400)
            
        if file_obj.is_consumed:
            return JsonResponse({'detail': 'Bu dosya zaten tüketildi.'}, status=410)
            
        # Sadece bu POST isteði gelince tüketildi olarak iþaretle
        file_obj.is_consumed = True
        file_obj.save()
        
        # Dosyayý sunucudan silmek isterseniz:
        # file_obj.file.delete()
        
        return JsonResponse({'detail': 'Dosya baþarýyla tüketildi.'}, status=200)
    
    return JsonResponse({'detail': 'Sadece POST metoduna izin verilir.'}, status=405)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id)

    if file_obj.one_time_view and file_obj.is_consumed:
        # Zaten tüketilmiþse 410 döndür.
        return HttpResponseGone('{"detail": "Bu dosya zaten görüntülendi ve artýk kullanýlamaz."}', 
                                content_type='application/json')

    file_path = file_obj.file.path
    if not os.path.exists(file_path):    file_size = os.path.getsize(file_path)
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
        response = FileResponse(open(file_path, 'rb'), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_obj.filename}"'
        return response

    else:
        # Normal indirme (tam dosya)
        response = FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))
        response["Accept-Ranges"] = "bytes"
        return response

