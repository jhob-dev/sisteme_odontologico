from django.urls import path
from . import views

urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pacientes/', views.lista_pacientes, name='lista_pacientes'),
    path('pacientes/crear/', views.crear_paciente, name='crear_paciente'),
    path('pacientes/<int:paciente_id>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:paciente_id>/reporte/', views.reporte_paciente, name='reporte_paciente'),
    path('pacientes/<int:paciente_id>/historia/', views.historia_clinica, name='historia_clinica'),
    path('pacientes/<int:paciente_id>/tratamiento/agregar/', views.agregar_tratamiento, name='agregar_tratamiento'),
    path('citas/', views.lista_citas, name='lista_citas'),
    path('citas/crear/', views.crear_cita, name='crear_cita'),
    path('citas/<int:cita_id>/editar/', views.editar_cita, name='editar_cita'),
    path('pagos/', views.lista_pagos, name='lista_pagos'),
    path('pagos/registrar/', views.registrar_pago, name='registrar_pago'),
    path('horario/', views.horario_semanal, name='horario_semanal'),
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/pacientes/', views.reporte_pacientes, name='reporte_pacientes'),
    path('reportes/citas/', views.reporte_citas, name='reporte_citas'),
    path('reportes/pagos/', views.reporte_pagos, name='reporte_pagos'),
    path('reportes/general/', views.reporte_general, name='reporte_general'),
]
