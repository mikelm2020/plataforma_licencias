from django import forms

from .models import Licencia, Sistema


class LicenciaForm(forms.ModelForm):
    tipo_sistema = forms.ModelChoiceField(
        queryset=Sistema.objects.all(),
        label="Software",
        empty_label="Seleccione un software",
    )

    class Meta:
        model = Licencia
        fields = [
            "tipo_sistema",
            "identificador_licencia",
            "tipo_licencia",
            "periodo_licencia",
            "fecha_inicio_vigencia",
            "estado",
            "numero_usuarios",
            "version_sistema",
            "observaciones",
        ]
        widgets = {
            "fecha_inicio_vigencia": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "observaciones": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "identificador_licencia": forms.TextInput(attrs={"class": "form-control"}),
            "numero_usuarios": forms.NumberInput(attrs={"class": "form-control"}),
            "version_sistema": forms.TextInput(
                attrs={"class": "form-control"}
            ),  # <--- CAMBIO AQUÍ: de CheckboxInput a TextInput
            "tipo_licencia": forms.Select(attrs={"class": "form-select"}),
            "periodo_licencia": forms.Select(attrs={"class": "form-select"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "identificador_licencia": "Identificador de Licencia",
            "tipo_licencia": "Tipo de Licencia",
            "periodo_licencia": "Período de Licencia",
            "fecha_inicio_vigencia": "Fecha de Inicio de Vigencia",
            "estado": "Estado de la Licencia",
            "numero_usuarios": "Número de Usuarios",
            "version_sistema": "Versión del Sistema",  # <--- CAMBIO AQUÍ: de ¿Es Reinstalable?
            "observaciones": "Observaciones Adicionales",
        }


class LicenciaUpdateForm(forms.ModelForm):
    # Campo para confirmar el pago, que no es parte del modelo
    pago_realizado = forms.BooleanField(
        required=False,
        label="¿Pago Realizado para Renovación?",
        help_text="Marque si el pago para la renovación de esta licencia ha sido recibido.",
    )

    class Meta:
        model = Licencia
        fields = [
            "version_sistema",
            "observaciones",
            "estado",  # Permitir cambiar el estado (ej. a ACTIVA)
            "fecha_inicio_vigencia",  # Permitir cambiar la fecha de inicio
        ]
        widgets = {
            "version_sistema": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "fecha_inicio_vigencia": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }
        labels = {
            "version_sistema": "Versión del Sistema",
            "observaciones": "Observaciones Adicionales",
            "estado": "Estado de la Licencia",
            "fecha_inicio_vigencia": "Fecha de Inicio de Vigencia",
        }
