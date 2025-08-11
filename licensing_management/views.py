from django.contrib import messages
from django.db import transaction  # Importa transaction para asegurar atomicidad
from django.db.models import Exists, OuterRef  # Importar Exists y OuterRef
from django.shortcuts import get_object_or_404, redirect, render  # Importa redirect
from django.utils import timezone  # Importa timezone para fechas y horas actuales

from .forms import (  # Importa el formulario que acabas de crear
    LicenciaForm,
    LicenciaUpdateForm,
)
from .models import (
    Cliente,
    Licencia,
    # Sistema,
)


# Vista para la página de inicio
def home_view(request):
    return render(request, "licensing_management/home.html")


# Nueva vista para listar clientes
def client_list_view(request):
    # clientes = Cliente.objects.all()
    # La fecha actual para comparar
    today = timezone.now().date()

    # Anotamos si el cliente tiene ALGUNA licencia de suscripción vencida
    # Usamos Subquery con Exists para eficiencia: evita cargar todas las licencias
    clientes = Cliente.objects.annotate(
        has_expired_subscription_license=Exists(
            Licencia.objects.filter(
                cliente=OuterRef(
                    "pk"
                ),  # Se refiere al cliente de la consulta principal
                tipo_licencia=Licencia.TIPO_SUSCRIPCION,
                fecha_fin_vigencia__lt=today,  # Licencias cuya fecha_fin_vigencia es anterior a hoy
            )
        )
    )

    # Obtener parámetros de filtro de la URL
    filtro_rfc = request.GET.get("rfc", "").strip()
    filtro_clave = request.GET.get("clave", "").strip()
    filtro_nombre = request.GET.get("nombre", "").strip()

    # Aplicar filtros
    if filtro_rfc:
        clientes = clientes.filter(
            rfc__icontains=filtro_rfc
        )  # icontains para LIKE insensible a mayúsculas

    if filtro_clave:
        # Aquí manejamos la lógica de "acompletar espacios" para la clave.
        # Quitamos espacios y rellenamos a la derecha con espacios si es necesario para 16 caracteres.
        # Asegúrate de que el campo `clave_cliente` en tu modelo `Cliente` tiene max_length suficiente (ej. 16).
        clave_formateada = filtro_clave.rjust(
            10
        )  # Rellena a la izquierda con espacios hasta 16 caracteres
        clientes = clientes.filter(
            clave_cliente__exact=clave_formateada
        )  # exact para coincidencia exacta

    if filtro_nombre:
        clientes = clientes.filter(
            nombre__icontains=filtro_nombre
        )  # icontains para LIKE insensible a mayúsculas

    clientes = clientes.order_by("nombre")  # Ordenar después de filtrar

    context = {
        "clientes": clientes,
        "filtro_rfc": filtro_rfc,  # Pasa los valores de filtro de vuelta a la plantilla
        "filtro_clave": filtro_clave,
        "filtro_nombre": filtro_nombre,
    }
    return render(request, "licensing_management/client_list.html", context)


# Nueva vista para los detalles de un cliente específico
def client_detail_view(request, clave_cliente):
    # Usamos get_object_or_404 para que Django devuelva un 404 si el cliente no existe
    cliente = get_object_or_404(Cliente, clave_cliente=clave_cliente)
    # También podemos obtener las licencias relacionadas con este cliente
    licencias = cliente.licencias.all().order_by(
        "-fecha_fin_vigencia"
    )  # Ordenar por fecha de vencimiento descendente

    context = {
        "cliente": cliente,
        "licencias": licencias,
    }
    return render(request, "licensing_management/client_detail.html", context)


# Nueva vista para añadir una licencia a un cliente específico
def add_license_view(request, clave_cliente):
    cliente = get_object_or_404(Cliente, clave_cliente=clave_cliente)

    if request.method == "POST":
        form = LicenciaForm(request.POST)
        if form.is_valid():
            licencia = form.save(
                commit=False
            )  # No guardes aún, primero asigna el cliente
            licencia.cliente = cliente  # Asigna el cliente a la licencia
            licencia.save()  # Ahora guarda la licencia
            return redirect(
                "client_detail", clave_cliente=cliente.clave_cliente
            )  # Redirige a los detalles del cliente
    else:
        form = LicenciaForm()  # Crea un formulario vacío para GET request

    context = {
        "cliente": cliente,
        "form": form,
    }
    return render(request, "licensing_management/add_license.html", context)


# Nueva vista para actualizar/renovar una licencia
def update_license_view(request, clave_cliente, licencia_id):
    cliente = get_object_or_404(Cliente, clave_cliente=clave_cliente)
    licencia = get_object_or_404(Licencia, id=licencia_id, cliente=cliente)

    if request.method == "POST":
        form = LicenciaUpdateForm(request.POST, instance=licencia)
        if form.is_valid():
            pago_realizado = form.cleaned_data.get("pago_realizado")
            fecha_form_inicio_vigencia = form.cleaned_data.get("fecha_inicio_vigencia")

            # Inicia una transacción para asegurar que todo se guarde o nada
            with transaction.atomic():
                # Guarda la versión y observaciones
                licencia_actualizada = form.save(commit=False)

                # Si el pago fue realizado y la licencia no es perpetua y no está ACTIVA
                # (o si se quiere renovar una ACTIVA, según tu lógica de negocio)
                # Aquí la lógica es para renovación de periodos que venzan.
                # Podemos ajustar esta lógica si solo quieres que renueve si está "VENCIDA" o "PENDIENTE_RENOVACION"
                if (
                    pago_realizado
                    and licencia.tipo_licencia != Licencia.PERIODO_PERPETUA
                ):
                    # Si estaba VENCIDA o PENDIENTE_RENOVACION, o simplemente se está renovando una ACTIVA
                    # Actualiza fecha de inicio a HOY y la fecha de fin se recalculará
                    # licencia_actualizada.fecha_inicio_vigencia = timezone.now().date()
                    licencia_actualizada.fecha_inicio_vigencia = (
                        fecha_form_inicio_vigencia
                    )
                    licencia_actualizada.fecha_fin_vigencia = (
                        None  # Forzar recálculo en save()
                    )
                    licencia_actualizada.estado = (
                        Licencia.ESTADO_ACTIVA
                    )  # Marcar como activa después de pago

                licencia_actualizada.save()  # Guarda los cambios

            return redirect("client_detail", clave_cliente=cliente.clave_cliente)
    else:
        form = LicenciaUpdateForm(
            instance=licencia
        )  # Carga el formulario con los datos de la licencia

    context = {
        "cliente": cliente,
        "licencia": licencia,
        "form": form,
    }
    return render(request, "licensing_management/update_license.html", context)


def delete_license_view(request, clave_cliente, licencia_id):
    cliente = get_object_or_404(Cliente, clave_cliente=clave_cliente)
    licencia = get_object_or_404(Licencia, id=licencia_id, cliente=cliente)

    if request.method == "POST":
        licencia.delete()
        messages.success(
            request,
            f'La licencia "{licencia.identificador_licencia}" ha sido eliminada exitosamente.',
        )
        return redirect("client_detail", clave_cliente=cliente.clave_cliente)

    # Si no es POST, puedes renderizar una página de confirmación si lo deseas,
    # pero para una eliminación simple, a menudo se maneja directamente con POST.
    # Aquí, simplemente redirigimos de vuelta a los detalles del cliente si no es POST.
    messages.error(request, "Método no permitido para eliminar la licencia.")
    return redirect("client_detail", clave_cliente=cliente.clave_cliente)
