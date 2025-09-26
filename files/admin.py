# admin.py
from django.contrib import admin
from .models import *

admin.site.register(File)
admin.site.register(CloudGroup)
admin.site.register(GroupFile)
admin.site.register(FileComment)
admin.site.register(GroupInvite)
admin.site.register(SecureLink)
admin.site.register(GroupMember)
admin.site.register(GroupFeed)
admin.site.register(Ad)
admin.site.register(UserEarning)
