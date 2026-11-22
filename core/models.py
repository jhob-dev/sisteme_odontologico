from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Paciente(models.Model):
    cedula = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^\d+$', 'La cédula debe contener solo números')]
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    nombre_familiar = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Nombre del familiar de contacto"
    )
    telefono_familiar = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Teléfono del familiar de contacto"
    )
    parentesco_familiar = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Parentesco (ej: esposo/a, padre/madre, etc.)"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['apellido', 'nombre']
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - {self.cedula}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    fecha = models.DateField()
    hora = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha', 'hora']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        unique_together = ['fecha', 'hora']

    def __str__(self):
        return f"{self.paciente.nombre_completo} - {self.fecha} {self.hora}"

    @property
    def horario(self):
        return f"{self.hora.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')}"

    @property
    def esta_pagada(self):
        pagos = self.pagos.aggregate(total=models.Sum('monto'))['total'] or 0
        return pagos >= self.costo_estimado

    @property
    def costo_estimado(self):
        return 100


class HistoriaClinica(models.Model):
    ANTECEDENTES_PERSONALES_OPCIONES = [
        'Diabetes', 'Alergias', 'Drogas', 'Cardiopatías', 'ETS',
        'Anticonceptivos', 'Asma', 'Digestivas', 'COVID-19',
        'Eruptivas', 'Quirúrgicos', 'Fumador', 'T.E.',
    ]
    HABITOS_PARAFUNCIONALES_OPCIONES = [
        'Onicofagia', 'Quielofagia', 'Succión digital', 'Bruxismo',
        'Desviación ATM',
    ]

    paciente = models.OneToOneField(Paciente, on_delete=models.CASCADE, related_name='historia_clinica')
    antecedentes_personales = models.JSONField(
        default=list, blank=True,
        help_text="Antecedentes personales seleccionados"
    )
    habitos_parafuncionales = models.JSONField(
        default=list, blank=True,
        help_text="Hábitos parafuncionales seleccionados"
    )
    observaciones_paciente = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Observaciones del paciente"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'

    def __str__(self):
        return f"Historia clínica - {self.paciente.nombre_completo}"


class Tratamiento(models.Model):
    historia_clinica = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE, related_name='tratamientos')
    cita = models.ForeignKey(Cita, on_delete=models.SET_NULL, null=True, blank=True, related_name='tratamientos')
    descripcion = models.TextField()
    diente = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="Número de diente si aplica"
    )
    fecha = models.DateField(default=timezone.now)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    completado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Tratamiento'
        verbose_name_plural = 'Tratamientos'

    def __str__(self):
        return f"{self.descripcion} - {self.fecha}"


class Pago(models.Model):
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('cheque', 'Cheque'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('no_pagado', 'No Pagado'),
    ]

    TIPO_CHOICES = [
        ('adelantado', 'Pago Adelantado'),
        ('cuota', 'Cuota'),
        ('completo', 'Pago Completo'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='pagos')
    cita = models.ForeignKey(Cita, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='completo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pagado')
    fecha_pago = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_pago']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"{self.paciente.nombre_completo} - ${self.monto} ({self.fecha_pago.strftime('%d/%m/%Y')})"