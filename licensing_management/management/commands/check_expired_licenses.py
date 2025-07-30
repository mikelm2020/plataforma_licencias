# licensing_management/management/commands/check_expired_licenses.py
from django.conf import settings  # Importar settings para acceder a EMAIL_ADMON
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from licensing_management.models import (  # Asegúrate de importar Sistema
    Licencia,
    Sistema,
)


class Command(BaseCommand):
    help = (
        "Verifica licencias vencidas de suscripción y envía notificaciones por correo."
    )

    def handle(self, *args, **kwargs):
        # Encontrar licencias de suscripción vencidas
        # ¡IMPORTANTE! Usar select_related para precargar cliente y tipo_sistema
        vencidas_suscripciones = Licencia.objects.filter(
            tipo_licencia=Licencia.TIPO_SUSCRIPCION, estado=Licencia.ESTADO_VENCIDA
        ).select_related("cliente", "tipo_sistema")  # Precarga el Sistema también

        if not vencidas_suscripciones.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    "No se encontraron licencias de suscripción vencidas para notificar."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Encontradas {vencidas_suscripciones.count()} licencias de suscripción vencidas."
            )
        )

        for licencia in vencidas_suscripciones:
            # Determinar el destinatario del correo
            recipient_email = []
            subject = ""

            # Verificar la categoría del sistema
            if (
                licencia.tipo_sistema.categoria == Sistema.ASPEL
            ):  # Asumiendo que tienes una constante ASPEL en tu modelo Sistema
                recipient_email.append(settings.EMAIL_ADMON)
                subject = f"Notificación Interna: Licencia Aspel Vencida - {licencia.cliente.nombre} ({licencia.identificador_licencia})"
                self.stdout.write(
                    self.style.WARNING(
                        f"Licencia Aspel vencida para {licencia.cliente.nombre}. Enviando notificación a {settings.EMAIL_ADMON}"
                    )
                )
            else:
                if (
                    licencia.cliente.correo_electronico
                ):  # Asegúrate de que el cliente tenga un correo
                    recipient_email.append(licencia.cliente.correo_electronico)
                    subject = f"URGENTE: Su Licencia de {licencia.tipo_sistema.nombre} ha Vencido - {licencia.identificador_licencia}"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Licencia no-Aspel vencida para {licencia.cliente.nombre}. Enviando notificación a {licencia.cliente.correo_electronico}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Cliente {licencia.cliente.nombre} no tiene correo electrónico. No se pudo enviar notificación para licencia {licencia.identificador_licencia}."
                        )
                    )
                    continue  # Saltar a la siguiente licencia si no hay correo de cliente

            if not recipient_email:  # Si por alguna razón no se definió un destinatario
                self.stdout.write(
                    self.style.ERROR(
                        f"No se pudo determinar el destinatario para la licencia {licencia.identificador_licencia}. Saltando."
                    )
                )
                continue

            # Generar el contenido del correo desde una plantilla HTML
            context = {
                "cliente_nombre": licencia.cliente.nombre,
                "cliente_rfc": licencia.cliente.rfc,
                "licencia_id": licencia.identificador_licencia,
                "licencia_periodicidad": licencia.get_periodo_licencia_display(),
                "fecha_vencimiento": licencia.fecha_fin_vigencia.strftime("%d/%m/%Y"),
                "licencia_tipo": licencia.get_tipo_licencia_display(),
                "sistema_nombre": licencia.tipo_sistema.nombre,
                "licencia_estado": licencia.get_estado_display(),
                "es_aspel": licencia.tipo_sistema.categoria
                == Sistema.ASPEL,  # Pasa esta variable a la plantilla si quieres adaptar el contenido
            }

            html_message = render_to_string(
                "emails/expired_license_notification.html", context
            )
            plain_message = f"""
            Estimado/a responsable de la empresa:  {licencia.cliente.nombre},

            Le informamos que su licencia de suscripción para {licencia.tipo_sistema.nombre} (ID: {licencia.identificador_licencia}) ha vencido el {licencia.fecha_fin_vigencia.strftime("%d/%m/%Y")}.

            Por favor, contacteme para renovar su servicio.

            Atentamente,
            Ing. Miguel Angel López Monroy
            TECNOIT
            """
            # Si es para el admin, puedes adaptar el plain_message también
            if licencia.tipo_sistema.categoria == Sistema.ASPEL:
                plain_message = f"""
                Notificación interna: Licencia Aspel vencida.

                Detalles del Cliente:
                Nombre: {licencia.cliente.nombre}
                RFC: {licencia.cliente.rfc}

                Detalles de la Licencia:
                Sistema: {licencia.tipo_sistema.nombre}
                Identificador: {licencia.identificador_licencia}
                Periodicidad: {licencia.get_periodo_licencia_display()}
                Fecha de Vencimiento: {licencia.fecha_fin_vigencia.strftime("%d/%m/%Y")}
                Estado: {licencia.get_estado_display()}

                Acción requerida: Contactar al cliente para renovación.
                """

            try:
                send_mail(
                    subject,
                    plain_message,
                    None,  # DEFAULT_FROM_EMAIL se usa si es None
                    recipient_email,
                    html_message=html_message,
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Notificación enviada exitosamente para licencia {licencia.identificador_licencia}."
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error al enviar notificación para licencia {licencia.identificador_licencia}: {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Proceso de verificación de licencias vencidas completado."
            )
        )
