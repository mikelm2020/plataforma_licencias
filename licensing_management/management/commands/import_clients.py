from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from licensing_management.firebird_connector import fetch_data_from_firebird
from licensing_management.models import Cliente


class Command(BaseCommand):
    help = "Importa o actualiza clientes desde la base de datos Firebird (Aspel SAE) a Django."

    def add_arguments(self, parser):
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Elimina todos los clientes existentes en Django antes de importar.",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Iniciando la importación de clientes desde Firebird...")
        )

        # Define tu consulta SQL para obtener clientes de Aspel SAE
        # AJUSTA ESTA CONSULTA a la estructura real de tu tabla de clientes en Firebird
        # Por ejemplo: 'SELECT CLAVE, NOMBRE, RFC, TELEFONO1, EMAIL FROM CLIENTES'
        # Asegúrate de que los nombres de las columnas ('CLAVE', 'NOMBRE', etc.) coincidan con las de tu DB Firebird
        firebird_query = "SELECT CLAVE, NOMBRE, RFC, EMAILPRED, TELEFONO FROM CLIE01 WHERE STATUS='A'"  # Ejemplo: solo clientes activos

        try:
            # Obtener datos de Firebird
            firebird_clients = fetch_data_from_firebird(firebird_query)

            if not firebird_clients:
                self.stdout.write(
                    self.style.WARNING(
                        "No se encontraron clientes en la base de datos Firebird o hubo un error de conexión/consulta."
                    )
                )
                return

            self.stdout.write(
                f"Se encontraron {len(firebird_clients)} clientes en Firebird."
            )

            # Si se usó la opción --truncate, eliminar todos los clientes existentes
            if options["truncate"]:
                self.stdout.write(
                    self.style.WARNING(
                        "Eliminando todos los clientes existentes en Django (opción --truncate activa)..."
                    )
                )
                Cliente.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("Clientes existentes eliminados."))

            # Usar una transacción para asegurar la atomicidad de la operación
            with transaction.atomic():
                created_count = 0
                updated_count = 0

                for client_data in firebird_clients:
                    # Asume que 'CLAVE' es el campo único y clave primaria en Firebird y Django
                    clave_cliente = client_data.get("CLAVE")

                    if not clave_cliente:
                        self.stderr.write(
                            self.style.ERROR(
                                f"Cliente sin CLAVE encontrado en Firebird, se omite: {client_data}"
                            )
                        )
                        continue

                    # --- INICIO DE LA SECCIÓN A MODIFICAR ---
                    # Extracción y limpieza segura de datos
                    # Usamos .get() con un valor por defecto para asegurar que siempre haya algo que evaluar.
                    # Luego, aplicamos .strip() solo si es una cadena, si no, lo dejamos como está o None.
                    nombre_raw = client_data.get("NOMBRE")
                    rfc_raw = client_data.get("RFC")
                    correo_electronico_raw = client_data.get("EMAILPRED")
                    telefono_raw = client_data.get("TELEFONO")

                    client_defaults = {
                        "nombre": nombre_raw.strip()
                        if isinstance(nombre_raw, str)
                        else nombre_raw,
                        "rfc": rfc_raw.strip() if isinstance(rfc_raw, str) else rfc_raw,
                        "correo_electronico": correo_electronico_raw.strip()
                        if isinstance(correo_electronico_raw, str)
                        else correo_electronico_raw,
                        "telefono": telefono_raw.strip()
                        if isinstance(telefono_raw, str)
                        else telefono_raw,
                    }

                    # Aseguramos que los valores que quedaron como None no intenten actualizar
                    # un campo en Django si su valor en Firebird es realmente nulo y el campo Django no lo acepta.
                    # O, si el campo Django es blank=True/null=True, se aceptará el None.
                    client_defaults = {
                        k: v for k, v in client_defaults.items() if v is not None
                    }
                    # --- FIN DE LA SECCIÓN A MODIFICAR ---

                    # Django usa update_or_create para manejar esto de forma eficiente
                    # La clave_cliente es la primary_key, así que solo se usa como lookup
                    client, created = Cliente.objects.update_or_create(
                        clave_cliente=clave_cliente, defaults=client_defaults
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Importación completada: {created_count} clientes creados, {updated_count} clientes actualizados."
                )
            )

        except Exception as e:
            raise CommandError(f"Error durante la importación: {e}")
