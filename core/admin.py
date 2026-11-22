from django.contrib import admin
from .models import Paciente, Cita, HistoriaClinica, Tratamiento, Pago


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'nombre', 'apellido', 'telefono', 'email', 'activo']
    list_filter = ['activo', 'fecha_registro']
    search_fields = ['cedula', 'nombre', 'apellido', 'telefono', 'email']
    ordering = ['apellido', 'nombre']


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'fecha', 'hora', 'hora_fin', 'estado', 'esta_pagada']
    list_filter = ['estado', 'fecha']
    search_fields = ['paciente__nombre', 'paciente__apellido', 'paciente__cedula']
    date_hierarchy = 'fecha'
    ordering = ['fecha', 'hora']


@admin.register(HistoriaClinica)
class HistoriaClinicaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'fecha_creacion', 'fecha_actualizacion']
    search_fields = ['paciente__nombre', 'paciente__apellido', 'paciente__cedula']
    ordering = ['-fecha_actualizacion']


@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'diente', 'fecha', 'costo', 'completado']
    list_filter = ['completado', 'fecha']
    search_fields = ['descripcion', 'diente']
    ordering = ['-fecha']


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'monto', 'metodo', 'tipo', 'estado', 'fecha_pago']
    list_filter = ['metodo', 'tipo', 'estado', 'fecha_pago']
    search_fields = ['paciente__nombre', 'paciente__apellido', 'paciente__cedula']
    date_hierarchy = 'fecha_pago'
    ordering = ['-fecha_pago']
