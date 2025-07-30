from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    clave_cliente = models.CharField(
        max_length=50,
        unique=True,
        primary_key=True,
        help_text="Clave de cliente de Aspel SAE",
    )
    nombre = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    correo_electronico = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.clave_cliente})"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]


# Modelo modificado de TipoSistemaAspel a SistemaAspel
class Sistema(models.Model):  # <--- Nombre de clase cambiado aquí
    # Definir las opciones para la categoría
    ASPEL = "ASPEL"
    MICROSOFT_OFFICE_365 = "MICROSOFT_OFFICE_365"
    ANTIVIRUS = "ANTIVIRUS"
    OTROS = "OTROS"  # Opcional: para cualquier otra categoría que no encaje

    CATEGORIA_CHOICES = [
        (ASPEL, "Aspel"),
        (MICROSOFT_OFFICE_365, "Microsoft Office 365"),
        (ANTIVIRUS, "Antivirus"),
        (OTROS, "Otros"),  # Puedes quitar esta si solo quieres las 3 principales
    ]

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_CHOICES,
        default=OTROS,  # Puedes elegir un valor por defecto
        verbose_name="Categoría del Sistema",
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Sistema"  # <--- verbose_name cambiado aquí
        verbose_name_plural = "Sistemas"  # <--- verbose_name_plural cambiado aquí


class Licencia(models.Model):
    # --- DEFINICIÓN DE CONSTANTES DE CLASE ---

    # Constantes para ESTADO_LICENCIA_CHOICES
    ESTADO_ACTIVA = "ACTIVA"
    ESTADO_VENCIDA = "VENCIDA"
    ESTADO_PENDIENTE_RENOVACION = "PENDIENTE_RENOVACION"
    ESTADO_INACTIVA = "INACTIVA"

    # Constantes para TIPO_LICENCIA_CHOICES
    TIPO_FISICA = "FISICA"
    TIPO_ELECTRONICA = "ELECTRONICA"
    TIPO_SUSCRIPCION = "SUSCRIPCION"

    # Constantes para PERIODO_LICENCIA_CHOICES
    PERIODO_MENSUAL = "MENSUAL"
    PERIODO_TRIMESTRAL = "TRIMESTRAL"
    PERIODO_SEMESTRAL = "SEMESTRAL"
    PERIODO_ANUAL = "ANUAL"
    PERIODO_PERPETUA = "PERPETUA"  # La constante para el periodo perpetuo

    # --- DEFINICIÓN DE CHOICES USANDO LAS CONSTANTES ---

    ESTADO_LICENCIA_CHOICES = [
        (ESTADO_ACTIVA, "Activa"),
        (ESTADO_VENCIDA, "Vencida"),
        (ESTADO_PENDIENTE_RENOVACION, "Pendiente de Renovación"),
        (ESTADO_INACTIVA, "Inactiva"),
    ]

    TIPO_LICENCIA_CHOICES = [
        (TIPO_FISICA, "Física"),
        (TIPO_ELECTRONICA, "Electrónica"),
        (TIPO_SUSCRIPCION, "Suscripción"),
    ]

    PERIODO_LICENCIA_CHOICES = [
        (PERIODO_MENSUAL, "Mensual"),
        (PERIODO_TRIMESTRAL, "Trimestral"),
        (PERIODO_SEMESTRAL, "Semestral"),
        (PERIODO_ANUAL, "Anual"),
        (PERIODO_PERPETUA, "Perpetua"),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="licencias"
    )

    # Referencia al modelo SistemaAspel (antes TipoSistemaAspel)
    tipo_sistema = models.ForeignKey(
        Sistema, on_delete=models.PROTECT
    )  # <--- Referencia actualizada aquí

    identificador_licencia = models.CharField(
        max_length=255,
        unique=True,
        help_text="Número de serie o código de activación de la licencia",
    )
    version_software = models.CharField(max_length=50, blank=True, null=True)

    version_sistema = models.CharField(
        max_length=50,  # Una longitud suficiente para números de versión complejos
        blank=True,
        null=True,
        verbose_name="Versión del Sistema",
    )

    fecha_adquisicion = models.DateField(blank=True, null=True)
    fecha_inicio_vigencia = models.DateField(default=timezone.now)
    fecha_fin_vigencia = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de vencimiento de la licencia (si aplica)",
    )

    estado = models.CharField(
        max_length=20, choices=ESTADO_LICENCIA_CHOICES, default=ESTADO_ACTIVA
    )

    tipo_licencia = models.CharField(
        max_length=20,
        choices=TIPO_LICENCIA_CHOICES,
        default=TIPO_SUSCRIPCION,
        help_text="Tipo de licencia (Física, Electrónica, Suscripción)",
    )

    periodo_licencia = models.CharField(
        max_length=20,
        choices=PERIODO_LICENCIA_CHOICES,
        blank=True,
        null=True,
        help_text="Periodo de la licencia (Mensual, Anual, Perpetua, etc.)",
    )

    observaciones = models.TextField(blank=True, null=True)
    numero_usuarios = models.IntegerField(
        default=1, help_text="Número de usuarios permitidos por la licencia"
    )

    def __str__(self):
        # Actualiza esto también para reflejar el nuevo nombre del modelo
        return f"{self.tipo_sistema.nombre} - {self.identificador_licencia} para {self.cliente.nombre}"

    def _calculate_end_date(self):
        """
        Calcula la fecha de fin de vigencia basándose en la fecha de inicio y la periodicidad.
        """
        # La licencia es "perpetua" si su PERIODO es PERIODO_PERPETUA
        # NO DEBERÍA MARCAR ERROR AQUÍ SI PERIODO_PERPETUA ESTÁ DEFINIDO ARRIBA
        if self.periodo_licencia == Licencia.PERIODO_PERPETUA:  # <--- DEBE SER ASÍ
            return None

        if not self.fecha_inicio_vigencia:
            return None

        start_date = self.fecha_inicio_vigencia

        if self.periodo_licencia == Licencia.PERIODO_MENSUAL:
            return start_date + relativedelta(months=+1)
        elif self.periodo_licencia == Licencia.PERIODO_TRIMESTRAL:
            return start_date + relativedelta(months=+3)
        elif self.periodo_licencia == Licencia.PERIODO_SEMESTRAL:
            return start_date + relativedelta(months=+6)
        elif self.periodo_licencia == Licencia.PERIODO_ANUAL:
            return start_date + relativedelta(years=+1)

        return None

    def clean(self):
        if self.tipo_licencia == "SUSCRIPCION" and self.periodo_licencia == "PERPETUA":
            raise ValidationError(
                {
                    "periodo_licencia": "Una licencia de Suscripción no puede ser Perpetua."
                }
            )
        if self.periodo_licencia == "PERPETUA" and self.tipo_licencia not in [
            "FISICA",
            "ELECTRONICA",
        ]:
            raise ValidationError(
                {
                    "periodo_licencia": "El periodo Perpetua solo es válido para licencias Físicas o Electrónicas."
                }
            )

    def update_estado(self):
        """
        Actualiza el estado de la licencia basado en la fecha de fin de vigencia y el tipo.
        Este método DEBE ser llamado periódicamente (ej. en un cron job) o en cada acceso a la licencia.
        """
        # Guarda el estado actual ANTES de calcular el nuevo
        # old_estado = self.estado

        if self.periodo_licencia == Licencia.PERIODO_PERPETUA:
            self.estado = Licencia.ESTADO_ACTIVA
        elif self.fecha_fin_vigencia:
            today = timezone.now().date()
            if self.fecha_fin_vigencia < today:
                self.estado = Licencia.ESTADO_VENCIDA
            elif (
                self.fecha_fin_vigencia - timedelta(days=7) <= today
            ):  # Vence en los próximos 7 días
                self.estado = Licencia.ESTADO_PENDIENTE_RENOVACION
            else:
                self.estado = Licencia.ESTADO_ACTIVA
        # Si no tiene fecha_fin_vigencia y no es perpetua, o no tiene fecha de inicio, considerarla inactiva
        elif not self.fecha_inicio_vigencia:
            self.estado = (
                Licencia.ESTADO_INACTIVA
            )  # O el estado que consideres apropiado
        else:  # Si tiene fecha de inicio pero no de fin y no es perpetua, por defecto activa
            self.estado = Licencia.ESTADO_ACTIVA

        # Guardar solo si el estado cambió
        # if self._state.db:  # Solo si el objeto ya existe en la DB
        #     original_licencia = Licencia.objects.get(pk=self.pk)
        #     if original_licencia.estado != self.estado:
        #         self.save(update_fields=["estado"])  # Guarda solo el campo estado

    # Sobreescribe save para asegurar que el estado se actualiza al guardar si no se hace explícitamente
    def save(self, *args, **kwargs):
        # Lógica para fecha_fin_vigencia:
        # Se asegura que fecha_fin_vigencia sea None si es perpetua,
        # o la calcula si tiene fecha_inicio_vigencia.
        if self.periodo_licencia == Licencia.PERIODO_PERPETUA:
            self.fecha_fin_vigencia = None
        elif self.fecha_inicio_vigencia:
            self.fecha_fin_vigencia = self._calculate_end_date()
        else:
            self.fecha_fin_vigencia = None

        # Si el estado es ACTIVA y no tiene fecha_inicio_vigencia, la establece a la fecha actual.
        # Esto es útil si una licencia se crea y es activa sin una fecha de inicio explícita.
        if self.estado == Licencia.ESTADO_ACTIVA and not self.fecha_inicio_vigencia:
            self.fecha_inicio_vigencia = timezone.now().date()

        # # Llama a update_estado() para establecer el estado de la licencia en memoria
        # # basándose en las fechas y el tipo. Esto ocurre ANTES de guardar.
        self.update_estado()  # Llama al nuevo método para actualizar el estado

        # Finalmente, llama al método save original del ORM de Django.
        # Esto es lo que realmente guarda el objeto (y su estado actualizado) en la base de datos.
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Licencia"
        verbose_name_plural = "Licencias"
        ordering = ["fecha_fin_vigencia", "cliente"]
