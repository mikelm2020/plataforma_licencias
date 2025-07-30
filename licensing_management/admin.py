from django.contrib import admin

from .models import Cliente, Licencia, Sistema

# Registra tus modelos aquí para que aparezcan en el panel de administración
admin.site.register(Cliente)
admin.site.register(Sistema)
admin.site.register(Licencia)
