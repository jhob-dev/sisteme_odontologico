import re
from datetime import time
from decimal import Decimal

from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils import timezone

from .models import Cita, Paciente, Pago, Tratamiento


TELEFONO_REGEX = re.compile(r'^[0-9]{7,12}$')
TELEFONO_ERROR = 'El teléfono debe contener solo números, entre 7 y 12 dígitos.'
TEXTO_NOMBRE_REGEX = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]+$")
TEXTO_NOMBRE_ERROR = 'Solo se permiten letras y espacios.'
EMAIL_REGEX = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
DIRECCION_PROHIBIDOS_REGEX = re.compile(r'[<>{};]')
DIRECCION_ERROR = 'La dirección no puede contener los caracteres < > { } ;'


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'cedula', 'nombre', 'apellido', 'telefono', 'email', 'direccion',
            'nombre_familiar', 'telefono_familiar', 'parentesco_familiar',
        ]
        labels = {
            'cedula': 'Cédula de Identidad',
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'telefono': 'Teléfono',
            'email': 'Correo Electrónico',
            'direccion': 'Dirección de Domicilio',
            'nombre_familiar': 'Nombre del Familiar',
            'telefono_familiar': 'Teléfono del Familiar',
            'parentesco_familiar': 'Parentesco',
        }
        widgets = {
            'cedula': forms.TextInput(attrs={
                'inputmode': 'numeric',
                'pattern': '[0-9]+',
                'title': 'La cédula debe contener solo números',
                'placeholder': 'Solo números, ej: 12345678',
                'data-numeric-only': '',
                'maxlength': '10',
                'autocomplete': 'off',
            }),
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre del paciente',
                'maxlength': '50',
            }),
            'apellido': forms.TextInput(attrs={
                'placeholder': 'Apellido del paciente',
                'maxlength': '50',
            }),
            'telefono': forms.TextInput(attrs={
                'type': 'tel',
                'inputmode': 'numeric',
                'pattern': '[0-9]{7,12}',
                'title': TELEFONO_ERROR,
                'placeholder': 'Solo números, ej: 04141234567',
                'data-phone-input': '',
                'maxlength': '12',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'ejemplo@correo.com',
            }),
            'direccion': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Dirección completa...',
                'maxlength': '200',
            }),
            'nombre_familiar': forms.TextInput(attrs={
                'placeholder': 'Nombre completo',
                'maxlength': '50',
            }),
            'telefono_familiar': forms.TextInput(attrs={
                'type': 'tel',
                'inputmode': 'numeric',
                'pattern': '[0-9]{7,12}',
                'title': TELEFONO_ERROR,
                'placeholder': 'Solo números, ej: 04149998877',
                'data-phone-input': '',
                'maxlength': '12',
            }),
            'parentesco_familiar': forms.TextInput(attrs={
                'placeholder': 'Ej: Esposo, Padre, Madre, Hijo, etc.',
                'maxlength': '50',
            }),
        }

    CAMPOS_OPCIONALES = [
        'email', 'direccion', 'nombre_familiar', 'telefono_familiar', 'parentesco_familiar',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in self.CAMPOS_OPCIONALES:
            self.fields[nombre].initial = ''
            if self.initial.get(nombre) == 'Ninguno':
                self.initial[nombre] = ''

    def clean_cedula(self):
        cedula = (self.cleaned_data.get('cedula') or '').strip()
        if cedula and not re.fullmatch(r'[0-9]+', cedula):
            raise ValidationError('La cédula debe contener solo números.')
        if cedula and not 7 <= len(cedula) <= 10:
            raise ValidationError('La cédula debe tener entre 7 y 10 dígitos.')
        return cedula

    def _clean_texto_nombre(self, value, etiqueta):
        texto = (value or '').strip()
        if texto and not TEXTO_NOMBRE_REGEX.fullmatch(texto):
            raise ValidationError(f'El campo {etiqueta} {TEXTO_NOMBRE_ERROR.lower()}')
        if len(texto) > 50:
            raise ValidationError(f'El campo {etiqueta} no puede exceder 50 caracteres.')
        return texto

    def clean_nombre(self):
        return self._clean_texto_nombre(self.cleaned_data.get('nombre'), 'nombre')

    def clean_apellido(self):
        return self._clean_texto_nombre(self.cleaned_data.get('apellido'), 'apellido')

    def clean_nombre_familiar(self):
        return self._clean_texto_nombre(self.cleaned_data.get('nombre_familiar'), 'nombre del familiar')

    def clean_parentesco_familiar(self):
        return self._clean_texto_nombre(self.cleaned_data.get('parentesco_familiar'), 'parentesco')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if email and not EMAIL_REGEX.fullmatch(email):
            raise ValidationError('Ingrese un correo electrónico válido (usuario@dominio.com).')
        return email

    def clean_direccion(self):
        direccion = (self.cleaned_data.get('direccion') or '').strip()
        if len(direccion) > 200:
            raise ValidationError('La dirección no puede exceder 200 caracteres.')
        if direccion and DIRECCION_PROHIBIDOS_REGEX.search(direccion):
            raise ValidationError(DIRECCION_ERROR)
        return direccion

    def _clean_telefono(self, value):
        telefono = (value or '').strip()
        if telefono and not TELEFONO_REGEX.fullmatch(telefono):
            raise ValidationError(TELEFONO_ERROR)
        return telefono

    def clean_telefono(self):
        return self._clean_telefono(self.cleaned_data.get('telefono'))

    def clean_telefono_familiar(self):
        return self._clean_telefono(self.cleaned_data.get('telefono_familiar'))


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['paciente', 'fecha', 'hora', 'hora_fin', 'observaciones']
        labels = {
            'paciente': 'Paciente',
            'fecha': 'Fecha',
            'hora': 'Hora de Inicio',
            'hora_fin': 'Hora de Fin',
            'observaciones': 'Observaciones',
        }
        widgets = {
            'paciente': forms.Select(attrs={'required': True}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'required': True}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'required': True}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'required': True}),
            'observaciones': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Detalles adicionales de la cita...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paciente'].queryset = Paciente.objects.filter(activo=True).order_by('apellido', 'nombre')
        self.fields['paciente'].empty_label = 'Seleccione un paciente'
        self.fields['observaciones'].initial = ''
        self.fields['observaciones'].required = True
        self.fields['observaciones'].validators.append(MaxLengthValidator(200))
        if self.initial.get('observaciones') == 'Ninguno':
            self.initial['observaciones'] = ''

    def clean_paciente(self):
        paciente = self.cleaned_data['paciente']
        if not paciente.activo:
            raise ValidationError('Solo puede agendar citas para pacientes activos.')
        return paciente

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha < timezone.now().date():
            raise ValidationError('La fecha no puede ser anterior a hoy.')
        return fecha

    def clean_hora(self):
        hora = self.cleaned_data.get('hora')
        if hora and not (time(7, 0) <= hora <= time(16, 0)):
            raise ValidationError('La hora debe estar entre las 07:00 a. m. y las 04:00 p. m.')
        return hora

    def clean_hora_fin(self):
        hora_fin = self.cleaned_data.get('hora_fin')
        hora = self.cleaned_data.get('hora')
        if hora_fin and hora and hora_fin <= hora:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        return hora_fin

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        hora_fin = cleaned_data.get('hora_fin')
        if not (fecha and hora and hora_fin):
            return cleaned_data

        citas_conflictivas = Cita.objects.filter(
            fecha=fecha,
        ).exclude(
            estado='cancelada',
        ).exclude(
            pk=self.instance.pk if self.instance else None,
        ).filter(
            hora__lt=hora_fin,
            hora_fin__gt=hora,
        ).exclude(
            hora_fin__lte=models.F('hora'),
        ).select_related('paciente')

        if citas_conflictivas.exists():
            conflicto_paciente = citas_conflictivas.filter(
                paciente=cleaned_data.get('paciente')
            ).exists() if cleaned_data.get('paciente') else False
            if conflicto_paciente:
                raise ValidationError(
                    'Ese paciente ya tiene una cita agendada en ese horario.'
                )
            raise ValidationError(
                'Ya existe una cita agendada en ese horario. No se puede agendar '
                'otra cita que se solape con ella.'
            )
        return cleaned_data


class CitaEstadoForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['estado', 'observaciones']
        labels = {
            'estado': 'Estado',
            'observaciones': 'Observaciones',
        }
        widgets = {
            'estado': forms.Select(attrs={'required': True}),
            'observaciones': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['observaciones'].initial = ''
        if self.initial.get('observaciones') == 'Ninguno':
            self.initial['observaciones'] = ''


class TratamientoForm(forms.ModelForm):
    costo = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0'),
        initial=0,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0',
            'inputmode': 'decimal',
            'pattern': '[0-9]+([.][0-9]{1,2})?',
            'title': 'El costo debe ser un número mayor o igual a 0',
            'placeholder': 'Ej: 25.50',
            'data-decimal-only': '',
        }),
    )

    class Meta:
        model = Tratamiento
        fields = ['cita', 'descripcion', 'diente', 'costo', 'completado']
        labels = {
            'cita': 'Cita Asociada',
            'descripcion': 'Descripción del Tratamiento',
            'diente': 'Número de Diente',
            'costo': 'Costo',
            'completado': 'Tratamiento Completado',
        }
        widgets = {
            'cita': forms.Select(attrs={'required': False}),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'required': True,
                'placeholder': 'Describe el tratamiento realizado...',
            }),
            'diente': forms.TextInput(attrs={
                'inputmode': 'numeric',
                'pattern': '[0-9]+',
                'title': 'El diente debe contener solo números',
                'placeholder': 'Ej: 14, 23, etc.',
                'data-numeric-only': '',
                'maxlength': '10',
            }),
            'completado': forms.CheckboxInput(attrs={'required': False}),
        }

    def __init__(self, *args, **kwargs):
        citas = kwargs.pop('citas', Cita.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['cita'].queryset = citas
        self.fields['cita'].required = False
        self.fields['cita'].empty_label = 'Sin cita asociada'
        self.fields['diente'].initial = ''
        if self.initial.get('diente') == 'Ninguno':
            self.initial['diente'] = ''

    def clean_diente(self):
        diente = (self.cleaned_data.get('diente') or '').strip()
        if diente and not re.fullmatch(r'[0-9]+', diente):
            raise ValidationError('El número de diente debe contener solo números.')
        return diente

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()
        if len(descripcion) < 3:
            raise ValidationError('La descripción debe tener al menos 3 caracteres.')
        return descripcion


class PagoForm(forms.ModelForm):
    monto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('10000'),
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0.01',
            'max': '10000',
            'inputmode': 'decimal',
            'pattern': '[0-9]+([.][0-9]{1,2})?',
            'title': 'El monto debe ser un número mayor que 0',
            'placeholder': 'Ej: 25.50',
            'data-decimal-only': '',
            'required': True,
        }),
    )

    class Meta:
        model = Pago
        fields = ['paciente', 'cita', 'monto', 'metodo', 'tipo', 'estado', 'observaciones']
        labels = {
            'paciente': 'Paciente',
            'cita': 'Cita Asociada',
            'monto': 'Monto',
            'metodo': 'Método de Pago',
            'tipo': 'Tipo de Pago',
            'estado': 'Estado',
            'observaciones': 'Observaciones',
        }
        widgets = {
            'paciente': forms.Select(attrs={'required': True}),
            'cita': forms.Select(attrs={'required': False}),
            'metodo': forms.Select(attrs={'required': True}),
            'tipo': forms.Select(attrs={'required': True}),
            'estado': forms.Select(attrs={'required': True}),
            'observaciones': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Detalles adicionales del pago...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paciente'].queryset = Paciente.objects.filter(activo=True).order_by('apellido', 'nombre')
        self.fields['paciente'].empty_label = 'Seleccione un paciente'
        self.fields['cita'].queryset = Cita.objects.filter(estado='completada').select_related('paciente').order_by('-fecha', '-hora')
        self.fields['cita'].required = False
        self.fields['cita'].empty_label = 'Sin cita asociada'
        self.fields['observaciones'].initial = ''
        self.fields['observaciones'].validators.append(MaxLengthValidator(255))
        if self.initial.get('observaciones') == 'Ninguno':
            self.initial['observaciones'] = ''

    def clean_cita(self):
        cita = self.cleaned_data.get('cita')
        paciente = self.cleaned_data.get('paciente')
        if cita and paciente and cita.paciente_id != paciente.id:
            raise ValidationError('La cita seleccionada no pertenece al paciente indicado.')
        return cita
