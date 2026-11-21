from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import CitaForm, PacienteForm, PagoForm, TratamientoForm
from .models import Cita, HistoriaClinica, Paciente, Pago, Tratamiento


User = get_user_model()


class ConsultorioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin123')
        self.client.force_login(self.user)
        self.paciente = Paciente.objects.create(
            cedula='12345678',
            nombre='Ana',
            apellido='Pérez',
            telefono='04141234567',
            email='ana@example.com',
            direccion='Calle 1',
        )

    def datos_paciente(self, **kwargs):
        data = {
            'cedula': '87654321',
            'nombre': 'Luis',
            'apellido': 'Gómez',
            'telefono': '04149998877',
            'email': '',
            'direccion': '',
            'nombre_familiar': '',
            'telefono_familiar': '',
            'parentesco_familiar': '',
        }
        data.update(kwargs)
        return data

    def test_formularios_opcionales_no_usan_sentinela(self):
        self.assertEqual(PacienteForm().fields['telefono_familiar'].initial, '')
        self.assertEqual(PacienteForm().fields['direccion'].initial, '')
        self.assertEqual(CitaForm().fields['observaciones'].initial, '')
        self.assertEqual(TratamientoForm(citas=Cita.objects.none()).fields['diente'].initial, '')
        self.assertEqual(PagoForm().fields['observaciones'].initial, '')

    def test_pantallas_principales_renderizan(self):
        urls = [
            reverse('dashboard'),
            reverse('lista_pacientes'),
            reverse('crear_paciente'),
            reverse('editar_paciente', args=[self.paciente.id]),
            reverse('detalle_paciente', args=[self.paciente.id]),
            reverse('historia_clinica', args=[self.paciente.id]),
            reverse('agregar_tratamiento', args=[self.paciente.id]),
            reverse('lista_citas'),
            reverse('crear_cita'),
            reverse('lista_pagos'),
            reverse('registrar_pago'),
            reverse('horario_semanal'),
            reverse('reportes'),
            reverse('reporte_pacientes'),
            reverse('reporte_citas'),
            reverse('reporte_pagos'),
            reverse('reporte_general'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_registrar_paciente_rechaza_campos_numericos_invalidos(self):
        response = self.client.post(reverse('crear_paciente'), data=self.datos_paciente(
            cedula='12a456',
            telefono='abc',
            telefono_familiar='123abc',
        ))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Paciente.objects.filter(cedula='12a456').exists())
        self.assertContains(response, 'La cédula debe contener solo números')
        self.assertContains(response, 'El teléfono solo puede contener números')

    def test_registrar_paciente_valido_crea_historia_clinica(self):
        response = self.client.post(reverse('crear_paciente'), data=self.datos_paciente(
            direccion='Avenida Principal',
            nombre_familiar='María Gómez',
            telefono_familiar='04148887766',
            parentesco_familiar='Esposa',
        ))

        self.assertRedirects(response, reverse('lista_pacientes'))
        paciente = Paciente.objects.get(cedula='87654321')
        self.assertEqual(paciente.direccion, 'Avenida Principal')
        self.assertTrue(hasattr(paciente, 'historia_clinica'))
        self.assertIsInstance(paciente.historia_clinica, HistoriaClinica)

    def test_editar_paciente_actualiza_datos(self):
        response = self.client.post(reverse('editar_paciente', args=[self.paciente.id]), data=self.datos_paciente(
            cedula=self.paciente.cedula,
            nombre='Ana María',
            apellido='Pérez Ruiz',
            telefono='04140001122',
            email='ana.nueva@example.com',
            direccion='Nueva dirección 123',
        ))

        self.assertRedirects(response, reverse('detalle_paciente', args=[self.paciente.id]))
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.nombre, 'Ana María')
        self.assertEqual(self.paciente.apellido, 'Pérez Ruiz')
        self.assertEqual(self.paciente.telefono, '04140001122')
        self.assertEqual(self.paciente.email, 'ana.nueva@example.com')
        self.assertEqual(self.paciente.direccion, 'Nueva dirección 123')

    def test_crear_cita_rechaza_fecha_invalida_y_horario_duplicado(self):
        response = self.client.post(reverse('crear_cita'), data={
            'paciente': self.paciente.id,
            'fecha': 'fecha-invalida',
            'hora': '09:00',
            'observaciones': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Cita.objects.count(), 0)

        Cita.objects.create(
            paciente=self.paciente,
            fecha=date(2026, 11, 10),
            hora=time(9, 0),
            estado='pendiente',
        )
        response = self.client.post(reverse('crear_cita'), data={
            'paciente': self.paciente.id,
            'fecha': '2026-11-10',
            'hora': '09:00',
            'observaciones': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Cita.objects.count(), 1)

    def test_agregar_tratamiento_rechaza_diente_con_letras(self):
        response = self.client.post(reverse('agregar_tratamiento', args=[self.paciente.id]), data={
            'cita': '',
            'descripcion': 'Limpieza dental',
            'diente': 'abc',
            'costo': '25.50',
            'completado': 'on',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tratamiento.objects.exists())
        self.assertContains(response, 'El número de diente debe contener solo números')

    def test_registrar_pago_rechaza_cita_de_otro_paciente(self):
        otro = Paciente.objects.create(
            cedula='99999999',
            nombre='Otro',
            apellido='Paciente',
            telefono='04241112233',
        )
        cita = Cita.objects.create(
            paciente=otro,
            fecha=date(2026, 11, 11),
            hora=time(10, 0),
            estado='completada',
        )

        response = self.client.post(reverse('registrar_pago'), data={
            'paciente': self.paciente.id,
            'cita': cita.id,
            'monto': '50.00',
            'metodo': 'efectivo',
            'tipo': 'completo',
            'estado': 'completado',
            'observaciones': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Pago.objects.exists())
        self.assertContains(response, 'La cita seleccionada no pertenece al paciente indicado')

    def test_registrar_pago_valido(self):
        response = self.client.post(reverse('registrar_pago'), data={
            'paciente': self.paciente.id,
            'cita': '',
            'monto': '75.25',
            'metodo': 'transferencia',
            'tipo': 'cuota',
            'estado': 'completado',
            'observaciones': 'Pago de prueba',
        })

        self.assertRedirects(response, reverse('lista_pagos'))
        pago = Pago.objects.get()
        self.assertEqual(str(pago.monto), '75.25')
        self.assertEqual(pago.metodo, 'transferencia')
        self.assertEqual(pago.tipo, 'cuota')

    def test_historia_clinica_guarda_antecedentes_y_habitos(self):
        response = self.client.post(reverse('historia_clinica', args=[self.paciente.id]), data={
            'antecedentes_personales': ['Diabetes', 'Asma', 'Fumador'],
            'habitos_parafuncionales': ['Bruxismo', 'Onicofagia'],
            'observaciones_paciente': 'Paciente ansioso',
        })

        self.assertRedirects(response, reverse('historia_clinica', args=[self.paciente.id]))
        historia = HistoriaClinica.objects.get(paciente=self.paciente)
        self.assertEqual(historia.antecedentes_personales, ['Diabetes', 'Asma', 'Fumador'])
        self.assertEqual(historia.habitos_parafuncionales, ['Bruxismo', 'Onicofagia'])
        self.assertEqual(historia.observaciones_paciente, 'Paciente ansioso')

    def test_historia_clinica_permite_secciones_vacias(self):
        response = self.client.post(reverse('historia_clinica', args=[self.paciente.id]), data={
            'observaciones_paciente': '',
        })

        self.assertRedirects(response, reverse('historia_clinica', args=[self.paciente.id]))
        historia = HistoriaClinica.objects.get(paciente=self.paciente)
        self.assertEqual(historia.antecedentes_personales, [])
        self.assertEqual(historia.habitos_parafuncionales, [])
        self.assertEqual(historia.observaciones_paciente, '')
