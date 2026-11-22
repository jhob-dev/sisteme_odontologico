from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count, F
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Paciente, Cita, HistoriaClinica, Tratamiento, Pago
from .forms import CitaEstadoForm, CitaForm, PacienteForm, PagoForm, TratamientoForm


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%H:%M').time()
    except (TypeError, ValueError):
        return None


def _pacientes_con_estadisticas(pacientes):
    ids = [p.id for p in pacientes]
    citas_stats = {}
    for row in (Cita.objects.filter(paciente_id__in=ids)
                .values('paciente_id')
                .annotate(
                    pendientes=Count('id', filter=Q(estado='pendiente')),
                    total=Count('id'),
                )):
        citas_stats[row['paciente_id']] = row
    pagos_stats = {}
    for row in (Pago.objects.filter(paciente_id__in=ids, estado='pagado')
                .values('paciente_id')
                .annotate(total=Sum('monto'))):
        pagos_stats[row['paciente_id']] = row['total'] or 0
    for paciente in pacientes:
        citas = citas_stats.get(paciente.id, {})
        paciente.citas_pendientes = citas.get('pendientes', 0)
        paciente.citas_totales = citas.get('total', 0)
        paciente.total_pagado = pagos_stats.get(paciente.id, 0)
        paciente.al_dia = paciente.citas_pendientes == 0
    return pacientes


def _aplicar_busqueda(qs, q, criterio='todos', prefijo=''):
    q = (q or '').strip()
    if not q:
        return qs
    lookups = {
        'nombre': f'{prefijo}nombre__icontains',
        'apellido': f'{prefijo}apellido__icontains',
        'cedula': f'{prefijo}cedula__icontains',
    }
    if criterio in lookups:
        return qs.filter(**{lookups[criterio]: q})
    return qs.filter(
        Q(**{f'{prefijo}nombre__icontains': q})
        | Q(**{f'{prefijo}apellido__icontains': q})
        | Q(**{f'{prefijo}cedula__icontains': q})
    )


def _contexto_busqueda(request):
    return {
        'q': request.GET.get('q', '').strip(),
        'criterio': request.GET.get('criterio', 'todos'),
    }


def _validar_rango_fechas(request, fecha_inicio, fecha_fin):
    if fecha_inicio and fecha_fin:
        if fecha_inicio > fecha_fin:
            messages.error(request, 'La fecha de inicio no puede ser mayor que la fecha final.')
            return False
        if (fecha_fin - fecha_inicio).days > 365:
            messages.error(request, 'El rango de consulta no puede ser superior a 365 días.')
            return False
    return True


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente')
    return redirect('login')


def bienvenida(request):
    return render(request, 'core/bienvenida.html')


@login_required
def dashboard(request):
    citas_hoy = Cita.objects.filter(fecha=timezone.now().date(), estado='pendiente').count()
    pacientes_total = Paciente.objects.filter(activo=True).count()
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    pagos_mes = Pago.objects.filter(
        fecha_pago__month=timezone.now().month,
        fecha_pago__year=timezone.now().year,
        estado='pagado'
    ).aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'citas_hoy': citas_hoy,
        'pacientes_total': pacientes_total,
        'citas_pendientes': citas_pendientes,
        'pagos_mes': pagos_mes,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def home(request):
    citas_hoy = Cita.objects.filter(fecha=timezone.now().date(), estado='pendiente').count()
    pacientes_total = Paciente.objects.filter(activo=True).count()
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()

    context = {
        'citas_hoy': citas_hoy,
        'pacientes_total': pacientes_total,
        'citas_pendientes': citas_pendientes,
    }
    return render(request, 'core/home.html', context)


@login_required
def lista_pacientes(request):
    pacientes = Paciente.objects.filter(activo=True)
    busqueda = _contexto_busqueda(request)
    pacientes = _aplicar_busqueda(
        pacientes, busqueda['q'], busqueda['criterio']
    ).order_by('apellido', 'nombre')
    pacientes = _pacientes_con_estadisticas(list(pacientes))

    context = {
        'pacientes': pacientes,
        **busqueda,
    }
    return render(request, 'core/lista_pacientes.html', context)


@login_required
def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            try:
                paciente = form.save()
                HistoriaClinica.objects.create(paciente=paciente)
                messages.success(request, f'Paciente {paciente.nombre_completo} creado exitosamente.')
                return redirect('lista_pacientes')
            except Exception as e:
                messages.error(request, f'Error al crear paciente: {str(e)}')
        else:
            messages.error(request, 'Revisa los campos marcados antes de continuar.')
    else:
        form = PacienteForm()

    return render(request, 'core/crear_paciente.html', {'form': form})


@login_required
def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Paciente {paciente.nombre_completo} actualizado exitosamente.')
                return redirect('detalle_paciente', paciente_id=paciente.id)
            except Exception as e:
                messages.error(request, f'Error al actualizar paciente: {str(e)}')
        else:
            messages.error(request, 'Revisa los campos marcados antes de continuar.')
    else:
        form = PacienteForm(instance=paciente)

    return render(request, 'core/editar_paciente.html', {
        'form': form,
        'paciente': paciente,
    })


@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historia, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)
    citas = paciente.citas.all()
    pagos = paciente.pagos.all()
    tratamientos = historia.tratamientos.all()

    total_pagado = pagos.filter(estado='pagado').aggregate(total=Sum('monto'))['total'] or 0
    citas_pendientes = citas.filter(estado='pendiente').count()

    context = {
        'paciente': paciente,
        'historia': historia,
        'tratamientos': tratamientos,
        'citas': citas,
        'pagos': pagos,
        'total_pagado': total_pagado,
        'citas_pendientes': citas_pendientes,
    }
    return render(request, 'core/detalle_paciente.html', context)


@login_required
def reporte_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historia, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)

    secciones_validas = {'paciente', 'historia', 'tratamientos', 'citas', 'pagos'}
    secciones = [s for s in request.GET.getlist('seccion') if s in secciones_validas]
    if not secciones:
        secciones = ['paciente']

    citas = paciente.citas.all().order_by('-fecha', '-hora')
    pagos = paciente.pagos.all()
    tratamientos = historia.tratamientos.all()

    total_pagado = pagos.filter(estado='pagado').aggregate(total=Sum('monto'))['total'] or 0
    citas_pendientes = citas.filter(estado='pendiente').count()

    secciones_labels = {
        'paciente': 'Datos del Paciente',
        'historia': 'Historia Clínica',
        'tratamientos': 'Tratamientos',
        'citas': 'Citas',
        'pagos': 'Pagos',
    }
    contenido = [secciones_labels[s] for s in secciones]

    context = {
        'paciente': paciente,
        'historia': historia,
        'tratamientos': tratamientos,
        'citas': citas,
        'pagos': pagos,
        'total_pagado': total_pagado,
        'citas_pendientes': citas_pendientes,
        'secciones': secciones,
        'contenido': contenido,
    }
    return render(request, 'core/reporte_paciente.html', context)


@login_required
def crear_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            try:
                cita = form.save()
                messages.success(request, f'Cita creada exitosamente para {cita.paciente.nombre_completo}.')
                return redirect('lista_citas')
            except Exception as e:
                messages.error(request, f'Error al crear cita: {str(e)}')
        else:
            messages.error(request, 'Revisa los campos marcados antes de continuar.')
    else:
        form = CitaForm()

    context = {
        'form': form,
        'tiene_pacientes': Paciente.objects.filter(activo=True).exists(),
    }
    return render(request, 'core/crear_cita.html', context)


@login_required
def lista_citas(request):
    citas = Cita.objects.all().select_related('paciente')
    estado_filter = request.GET.get('estado')
    estados_validos = {estado for estado, _ in Cita.ESTADO_CHOICES}

    if estado_filter in estados_validos:
        citas = citas.filter(estado=estado_filter)
    else:
        estado_filter = None

    busqueda = _contexto_busqueda(request)
    citas = _aplicar_busqueda(citas, busqueda['q'], busqueda['criterio'], prefijo='paciente__')

    context = {
        'citas': citas,
        'estado_filter': estado_filter,
        **busqueda,
    }
    return render(request, 'core/lista_citas.html', context)


@login_required
def cita_disponibilidad(request):
    paciente_id = request.GET.get('paciente')
    fecha = _parse_date(request.GET.get('fecha'))
    hora = _parse_time(request.GET.get('hora'))
    hora_fin = _parse_time(request.GET.get('hora_fin'))

    if not (paciente_id and fecha and hora and hora_fin):
        return JsonResponse({'disponible': True})

    if hora_fin <= hora:
        return JsonResponse({
            'disponible': False,
            'mensaje': 'La hora de fin debe ser posterior a la hora de inicio.',
        })

    conflictos = (Cita.objects
                  .filter(fecha=fecha)
                  .exclude(estado='cancelada')
                  .filter(hora__lt=hora_fin, hora_fin__gt=hora)
                  .exclude(hora_fin__lte=F('hora')))

    paciente_conflicto = conflictos.filter(paciente_id=paciente_id).exists()
    slot_conflicto = conflictos.exclude(paciente_id=paciente_id).exists()

    if paciente_conflicto:
        return JsonResponse({
            'disponible': False,
            'paciente_conflicto': True,
            'mensaje': 'Ese paciente ya tiene una cita agendada en ese horario.',
        })
    if slot_conflicto:
        return JsonResponse({
            'disponible': False,
            'slot_conflicto': True,
            'mensaje': 'Ya existe una cita agendada en ese horario. No se puede agendar otra cita que se solape con ella.',
        })
    return JsonResponse({'disponible': True})


@login_required
def editar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)

    if request.method == 'POST':
        form = CitaEstadoForm(request.POST, instance=cita)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Cita actualizada exitosamente.')
                return redirect('lista_citas')
            except Exception as e:
                messages.error(request, f'Error al actualizar cita: {str(e)}')
        else:
            messages.error(request, 'Revisa los campos marcados antes de continuar.')
    else:
        form = CitaEstadoForm(instance=cita)

    context = {
        'cita': cita,
        'form': form,
    }
    return render(request, 'core/editar_cita.html', context)


@login_required
def historia_clinica(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historia, created = HistoriaClinica.objects.get_or_create(paciente=paciente)
    if historia.antecedentes_personales is None:
        historia.antecedentes_personales = []
    if historia.habitos_parafuncionales is None:
        historia.habitos_parafuncionales = []
    tratamientos = historia.tratamientos.all()

    if request.method == 'POST':
        try:
            historia.antecedentes_personales = request.POST.getlist('antecedentes_personales')
            historia.habitos_parafuncionales = request.POST.getlist('habitos_parafuncionales')
            historia.observaciones_paciente = request.POST.get('observaciones_paciente', '').strip()[:255]
            historia.save()
            messages.success(request, 'Historia clínica actualizada exitosamente.')
            return redirect('historia_clinica', paciente_id=paciente.id)
        except Exception as e:
            messages.error(request, f'Error al actualizar historia clínica: {str(e)}')

    context = {
        'paciente': paciente,
        'historia': historia,
        'tratamientos': tratamientos,
        'antecedentes_opciones': HistoriaClinica.ANTECEDENTES_PERSONALES_OPCIONES,
        'habitos_opciones': HistoriaClinica.HABITOS_PARAFUNCIONALES_OPCIONES,
    }
    return render(request, 'core/historia_clinica.html', context)


@login_required
def agregar_tratamiento(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historia, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)
    citas = paciente.citas.filter(estado='completada').order_by('-fecha', '-hora')

    if request.method == 'POST':
        form = TratamientoForm(request.POST, citas=citas)
        if form.is_valid():
            try:
                tratamiento = form.save(commit=False)
                tratamiento.historia_clinica = historia
                tratamiento.save()
                messages.success(request, 'Tratamiento agregado exitosamente.')
                return redirect('historia_clinica', paciente_id=paciente.id)
            except Exception as e:
                messages.error(request, f'Error al agregar tratamiento: {str(e)}')
        else:
            messages.error(request, 'Revisa los campos marcados antes de continuar.')
    else:
        form = TratamientoForm(citas=citas)

    context = {
        'paciente': paciente,
        'historia': historia,
        'citas': citas,
        'form': form,
    }
    return render(request, 'core/agregar_tratamiento.html', context)


@login_required
def registrar_pago(request):
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Pago registrado exitosamente.')
                return redirect('lista_pagos')
            except Exception as e:
                messages.error(request, f'Error al registrar pago: {str(e)}')
        else:
            messages.error(request, 'Revisa los campos marcados antes de continuar.')
    else:
        form = PagoForm()

    return render(request, 'core/registrar_pago.html', {'form': form})


@login_required
def lista_pagos(request):
    pagos = Pago.objects.all().select_related('paciente', 'cita')
    pacientes = Paciente.objects.filter(activo=True)
    paciente_filter = request.GET.get('paciente')

    if paciente_filter and paciente_filter.isdigit():
        pagos = pagos.filter(paciente_id=paciente_filter)
    else:
        paciente_filter = None

    busqueda = _contexto_busqueda(request)
    pagos = _aplicar_busqueda(pagos, busqueda['q'], busqueda['criterio'], prefijo='paciente__')

    context = {
        'pagos': pagos,
        'pacientes': pacientes,
        'paciente_filter': paciente_filter,
        **busqueda,
    }
    return render(request, 'core/lista_pagos.html', context)


@login_required
def horario_semanal(request):
    DIAS_ES = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo',
    }
    MESES_ES = {
        'January': 'Enero',
        'February': 'Febrero',
        'March': 'Marzo',
        'April': 'Abril',
        'May': 'Mayo',
        'June': 'Junio',
        'July': 'Julio',
        'August': 'Agosto',
        'September': 'Septiembre',
        'October': 'Octubre',
        'November': 'Noviembre',
        'December': 'Diciembre',
    }

    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    citas_semana = Cita.objects.filter(
        fecha__range=[inicio_semana, fin_semana]
    ).select_related('paciente').order_by('fecha', 'hora')

    busqueda = _contexto_busqueda(request)
    citas_semana = _aplicar_busqueda(
        citas_semana, busqueda['q'], busqueda['criterio'], prefijo='paciente__'
    )

    dias_semana = []
    for i in range(7):
        dia = inicio_semana + timedelta(days=i)
        citas_dia = citas_semana.filter(fecha=dia)

        nombre_dia_en = dia.strftime('%A')
        nombre_dia_es = DIAS_ES.get(nombre_dia_en, nombre_dia_en)

        fecha_formateada = f"{dia.day:02d}/{dia.month:02d}"

        nombre_mes_en = dia.strftime('%B')
        nombre_mes_es = MESES_ES.get(nombre_mes_en, nombre_mes_en)

        dias_semana.append({
            'fecha': dia,
            'nombre_dia': nombre_dia_es,
            'nombre_mes': nombre_mes_es,
            'fecha_formateada': fecha_formateada,
            'citas': citas_dia,
        })

    inicio_formateado = f"{inicio_semana.day:02d}/{inicio_semana.month:02d}/{inicio_semana.year}"
    fin_formateado = f"{fin_semana.day:02d}/{fin_semana.month:02d}/{fin_semana.year}"

    context = {
        'inicio_semana': inicio_semana,
        'fin_semana': fin_semana,
        'inicio_formateado': inicio_formateado,
        'fin_formateado': fin_formateado,
        'dias_semana': dias_semana,
        **busqueda,
    }
    return render(request, 'core/horario_semanal.html', context)


@login_required
def reportes(request):
    return render(request, 'core/reportes.html')


@login_required
def reporte_pacientes(request):
    pacientes = list(Paciente.objects.filter(activo=True).order_by('apellido', 'nombre'))
    pacientes = _pacientes_con_estadisticas(pacientes)

    context = {
        'pacientes': pacientes,
        'total_pacientes': len(pacientes),
    }
    return render(request, 'core/reporte_pacientes.html', context)


@login_required
def reporte_citas(request):
    citas = Cita.objects.all().select_related('paciente')
    fecha_inicio_input = request.GET.get('fecha_inicio', '')
    fecha_fin_input = request.GET.get('fecha_fin', '')
    fecha_inicio = _parse_date(fecha_inicio_input)
    fecha_fin = _parse_date(fecha_fin_input)

    if fecha_inicio_input and fecha_inicio is None:
        messages.warning(request, 'La fecha de inicio no es válida; se ignoró el filtro.')
    if fecha_fin_input and fecha_fin is None:
        messages.warning(request, 'La fecha final no es válida; se ignoró el filtro.')

    if not _validar_rango_fechas(request, fecha_inicio, fecha_fin):
        citas = Cita.objects.none()
    else:
        if fecha_inicio:
            citas = citas.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            citas = citas.filter(fecha__lte=fecha_fin)

    total_citas = citas.count()
    citas_completadas = citas.filter(estado='completada').count()
    citas_pendientes = citas.filter(estado='pendiente').count()
    citas_canceladas = citas.filter(estado='cancelada').count()

    context = {
        'citas': citas,
        'total_citas': total_citas,
        'citas_completadas': citas_completadas,
        'citas_pendientes': citas_pendientes,
        'citas_canceladas': citas_canceladas,
        'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else '',
        'fecha_fin': fecha_fin.isoformat() if fecha_fin else '',
    }
    return render(request, 'core/reporte_citas.html', context)


@login_required
def reporte_pagos(request):
    pagos = Pago.objects.all().select_related('paciente', 'cita')
    fecha_inicio_input = request.GET.get('fecha_inicio', '')
    fecha_fin_input = request.GET.get('fecha_fin', '')
    fecha_inicio = _parse_date(fecha_inicio_input)
    fecha_fin = _parse_date(fecha_fin_input)

    if fecha_inicio_input and fecha_inicio is None:
        messages.warning(request, 'La fecha de inicio no es válida; se ignoró el filtro.')
    if fecha_fin_input and fecha_fin is None:
        messages.warning(request, 'La fecha final no es válida; se ignoró el filtro.')

    if not _validar_rango_fechas(request, fecha_inicio, fecha_fin):
        pagos = Pago.objects.none()
    else:
        if fecha_inicio:
            pagos = pagos.filter(fecha_pago__date__gte=fecha_inicio)
        if fecha_fin:
            pagos = pagos.filter(fecha_pago__date__lte=fecha_fin)

    total_pagos = pagos.count()
    total_monto = pagos.filter(estado='pagado').aggregate(total=Sum('monto'))['total'] or 0
    pagos_efectivo = pagos.filter(metodo='efectivo').count()
    pagos_tarjeta = pagos.filter(metodo='tarjeta').count()
    pagos_transferencia = pagos.filter(metodo='transferencia').count()

    context = {
        'pagos': pagos,
        'total_pagos': total_pagos,
        'total_monto': total_monto,
        'pagos_efectivo': pagos_efectivo,
        'pagos_tarjeta': pagos_tarjeta,
        'pagos_transferencia': pagos_transferencia,
        'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else '',
        'fecha_fin': fecha_fin.isoformat() if fecha_fin else '',
    }
    return render(request, 'core/reporte_pagos.html', context)


@login_required
def reporte_general(request):
    pacientes_total = Paciente.objects.filter(activo=True).count()
    citas_total = Cita.objects.count()
    citas_completadas = Cita.objects.filter(estado='completada').count()
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    pagos_total = Pago.objects.filter(estado='pagado').aggregate(total=Sum('monto'))['total'] or 0
    tratamientos_total = Tratamiento.objects.count()

    citas_mes = Cita.objects.filter(
        fecha__month=timezone.now().month,
        fecha__year=timezone.now().year
    ).count()

    pagos_mes = Pago.objects.filter(
        fecha_pago__month=timezone.now().month,
        fecha_pago__year=timezone.now().year,
        estado='pagado'
    ).aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'pacientes_total': pacientes_total,
        'citas_total': citas_total,
        'citas_completadas': citas_completadas,
        'citas_pendientes': citas_pendientes,
        'pagos_total': pagos_total,
        'tratamientos_total': tratamientos_total,
        'citas_mes': citas_mes,
        'pagos_mes': pagos_mes,
    }
    return render(request, 'core/reporte_general.html', context)