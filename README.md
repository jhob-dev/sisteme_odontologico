# Consultorio Odontológico - Sistema de Gestión

Sistema de gestión odontológica desarrollado en Django con base de datos SQLite, diseñado para ser portable y fácil de utilizar.

## Características

- **Gestión de Pacientes**: Registro completo de pacientes con información personal (nombre, apellido, cédula, teléfono, email, dirección)
- **Familiar de Contacto**: Registro opcional de familiar de contacto con nombre, teléfono y parentesco
- **Gestión de Citas**: Agendamiento de citas médicas con fecha, hora y estados (pendiente, confirmada, completada, cancelada)
- **Historias Clínicas**: Registro de antecedentes personales, hábitos parafuncionales, observaciones y tratamientos realizados
- **Control de Pagos**: Registro de pagos con diferentes métodos (efectivo, tarjeta, transferencia, cheque) y tipos (completo, adelantado, cuotas)
- **Vista de Pacientes**: Lista de pacientes con estado de citas pendientes y pagos realizados
- **Horario Semanal**: Vista visual de todas las citas de la semana organizadas por día
- **Sistema de Login**: Autenticación de usuarios para acceso seguro al sistema
- **Dashboard**: Panel principal con estadísticas y accesos directos
- **Sistema de Reportes**: Reportes detallados y generales con filtros y opciones de impresión
- **Alertas Toast**: Notificaciones visuales (verde para éxito, rojo para errores)

## Requisitos

- Python 3.10 o superior (probado con Python 3.13)
- pip (gestor de paquetes de Python, se instala junto con Python)

## Instalación y Puesta en Marcha

Sigue estos pasos la primera vez que uses el sistema, o al copiarlo a un equipo nuevo.

### 1. Obtener el proyecto

Clona el repositorio o copia la carpeta del proyecto a tu equipo.

```powershell
cd C:\workspace\odontologia   # ajusta a la ruta donde copiaste el proyecto
```

### 2. Crear el entorno virtual

El proyecto usa un entorno virtual para aislar sus dependencias. Créalo dentro de la carpeta del proyecto:

```powershell
python -m venv venv
```

> **Nota:** el entorno virtual no se copia entre equipos; se crea en cada máquina con este comando.

### 3. Activar el entorno virtual

**Windows (PowerShell o CMD):**
```powershell
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

Verás `(venv)` al inicio del prompt cuando esté activo.

> **PowerShell:** si aparece un error de política de ejecución, ejecuta una sola vez:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> Alternativamente, no actives el entorno y usa `venv\Scripts\python.exe` en lugar de `python` en los comandos siguientes.

### 4. Instalar las dependencias

Con el entorno virtual activado, instala las dependencias desde `requirements.txt`:

```powershell
pip install -r requirements.txt
```

### 5. Preparar la base de datos

Ejecuta las migraciones para crear las tablas en SQLite:

```powershell
python manage.py migrate
```

### 6. Crear un usuario administrador (solo si es la primera instalación)

Este usuario te permitirá iniciar sesión en el sistema:

```powershell
python manage.py createsuperuser
```

Sigue las instrucciones para crear usuario y contraseña. Si la base de datos ya tiene datos copiados (`db.sqlite3`), este paso se puede omitir si ya existe un usuario.

### 7. Iniciar el servidor

```powershell
python manage.py runserver
```

El servidor queda disponible en http://127.0.0.1:8000/

Para detenerlo, presiona `Ctrl + C` en la terminal.

### 8. Acceder a la aplicación

- Página de bienvenida: http://127.0.0.1:8000/
- Login: http://127.0.0.1:8000/login/
- Dashboard (después del login): http://127.0.0.1:8000/dashboard/
- Panel de administración: http://127.0.0.1:8000/admin/

> **Resumen rápido para uso diario:** abre una terminal en la carpeta del proyecto, ejecuta `venv\Scripts\activate` (Windows) y luego `python manage.py runserver`.

## Copiar el sistema a otro equipo

1. Copia la carpeta del proyecto **incluyendo `db.sqlite3`** si quieres conservar los datos (la carpeta `venv` no hace falta copiarla).
2. En el equipo nuevo, instala Python 3.10+.
3. Sigue los pasos 2 a 5 de la instalación (crear venv, activarlo, instalar dependencias, migrar).
4. Si copiaste `db.sqlite3`, el paso 6 (createsuperuser) no es necesario; los usuarios existentes seguirán funcionando.

## Uso

### Flujo de la Aplicación

1. **Página de Bienvenida**: Al acceder a http://127.0.0.1:8000/, verás una página de bienvenida con información del sistema.
2. **Login**: Haz clic en "Iniciar Sesión" para acceder al sistema. Usa el superusuario creado durante la instalación.
3. **Dashboard**: Después del login, serás redirigido al dashboard donde verás estadísticas y accesos directos.
4. **Navegación**: Desde el dashboard puedes acceder a todas las funcionalidades del sistema.

### Dashboard
El dashboard muestra estadísticas rápidas:
- Citas para hoy
- Total de pacientes registrados
- Citas pendientes
- Pagos del mes actual

También proporciona accesos directos a las acciones más comunes y secciones del sistema.

### Gestión de Pacientes

**Registrar un nuevo paciente:**
1. Ve a "Pacientes" → "Registrar Nuevo Paciente"
2. Completa los campos obligatorios (cedula, nombre, apellido, teléfono)
3. Los campos email y dirección son opcionales
4. Al crear el paciente, se genera automáticamente su historia clínica vacía

**Ver lista de pacientes:**
- Muestra todos los pacientes con su información básica
- Indica citas pendientes y total pagado
- Estado visual: "Al día" (sin citas pendientes) o "Pendiente"

**Detalle del paciente:**
- Información personal completa
- Resumen de citas y pagos
- Lista de todas las citas del paciente
- Lista de todos los pagos realizados
- Botón **Imprimir Reporte**: abre un modal para elegir qué secciones incluir (datos del paciente, historia clínica, tratamientos, citas y pagos) y genera un documento con formato de plantilla lista para imprimir

### Gestión de Citas

**Agendar una cita:**
1. Ve a "Citas" → "Agendar Nueva Cita"
2. Selecciona un paciente de la lista
3. Define la fecha y hora
4. Agrega observaciones opcionales
5. La cita se crea con estado "pendiente" por defecto

**Editar una cita:**
- Cambiar el estado (pendiente → confirmada → completada → cancelada)
- Actualizar observaciones

**Filtrar citas:**
- Puedes filtrar por estado desde la lista de citas

### Historias Clínicas

**Actualizar historia clínica:**
1. Desde el detalle del paciente, haz clic en "Historia"
2. Registra:
   - Condiciones médicas preexistentes
   - Alergias conocidas
   - Medicamentos actuales
   - Antecedentes familiares
   - Observaciones generales

**Agregar tratamientos:**
1. Desde la historia clínica, haz clic en "Agregar Tratamiento"
2. Asocia una cita (opcional)
3. Describe el tratamiento realizado
4. Indica el diente si aplica
5. Registra el costo
6. Marca si está completado

### Control de Pagos

**Registrar un pago:**
1. Ve a "Pagos" → "Registrar Nuevo Pago"
2. Selecciona el paciente
3. Ingresa el monto
4. Selecciona el método de pago (efectivo, tarjeta, transferencia, cheque)
5. Selecciona el tipo (completo, adelantado, cuota)
6. Agrega observaciones opcionales

**Ver lista de pagos:**
- Todos los pagos registrados
- Filtrable por paciente
- Muestra fecha, paciente, monto, método, tipo y estado

### Horario Semanal

**Ver horario:**
- Ve a "Horario Semanal"
- Muestra una vista de 7 días (lunes a domingo)
- Cada día muestra las citas agendadas con hora y paciente
- Los estados de las citas se muestran con colores

### Sistema de Reportes

El sistema incluye un módulo completo de reportes accesible desde el menú "Reportes":

**Reporte General:**
- Estadísticas totales del sistema
- Estadísticas del mes actual
- Vista general de pacientes, citas, pagos y tratamientos
- Opción de imprimir

**Reporte de Pacientes:**
- Listado completo de pacientes
- Citas totales y pendientes por paciente
- Total pagado por paciente
- Opción de imprimir

**Reporte de Citas:**
- Listado de todas las citas
- Filtros por rango de fechas
- Estadísticas por estado (completadas, pendientes, canceladas)
- Opción de imprimir

**Reporte de Pagos:**
- Listado de todos los pagos
- Filtros por rango de fechas
- Análisis por método de pago (efectivo, tarjeta, transferencia)
- Monto total y estadísticas
- Opción de imprimir

Todos los reportes incluyen botón de impresión para generar versiones en papel o PDF.

## Panel de Administración

El panel de administración de Django (http://127.0.0.1:8000/admin/) permite:

- Gestión completa de todos los modelos
- Búsqueda avanzada
- Filtros personalizados
- Exportación de datos
- Gestión de usuarios

Para acceder, usa el superusuario creado durante la instalación.

## Estructura de la Base de Datos

### Paciente
- cédula (única)
- nombre
- apellido
- teléfono
- email (opcional)
- dirección (opcional)
- nombre_familiar (opcional)
- telefono_familiar (opcional)
- parentesco_familiar (opcional)
- fecha_registro
- activo

### Cita
- paciente (FK)
- fecha
- hora
- estado (pendiente, confirmada, completada, cancelada)
- observaciones
- fecha_creación
- fecha_actualización

### HistoriaClínica
- paciente (FK, OneToOne)
- antecedentes_personales
- habitos_parafuncionales
- observaciones_paciente
- fecha_creación
- fecha_actualización

### Tratamiento
- historia_clínica (FK)
- cita (FK, opcional)
- descripción
- diente (opcional)
- fecha
- costo
- completado

### Pago
- paciente (FK)
- cita (FK, opcional)
- monto
- método (efectivo, tarjeta, transferencia, cheque)
- tipo (completo, adelantado, cuota)
- estado (pendiente, completado, anulado)
- fecha_pago
- observaciones

## Configuración

### Zona Horaria
La aplicación está configurada para la zona horaria "America/Caracas". Puedes cambiarla en `consultorio_odontologico/settings.py`:

```python
TIME_ZONE = 'America/Caracas'  # Cambia a tu zona horaria
```

### Idioma
La aplicación está en español. Puedes cambiarlo en `consultorio_odontologico/settings.py`:

```python
LANGUAGE_CODE = 'es'  # Cambia a 'en' para inglés, etc.
```

### Base de Datos
Por defecto usa SQLite (archivo `db.sqlite3`). Es portable y no requiere configuración adicional.

## Portabilidad

La aplicación es completamente portable:
- La base de datos SQLite es un solo archivo (`db.sqlite3`)
- No requiere instalación de servidor de base de datos
- Las dependencias están fijadas en `requirements.txt`
- Funciona en Windows, Linux y macOS con Python 3.10+
- Puedes copiar toda la carpeta del proyecto (excepto `venv`) y ejecutarla en otra máquina siguiendo los pasos de "Copiar el sistema a otro equipo"

## Backup

Para hacer backup de la aplicación:
1. Copia toda la carpeta del proyecto
2. El archivo `db.sqlite3` contiene todos los datos
3. No hay configuraciones externas necesarias

## Troubleshooting

**Error: "No module named 'django'"**
```powershell
# Asegúrate de tener el entorno virtual activado y luego:
pip install -r requirements.txt
```

**Error: "python no se reconoce" o el venv no funciona**
```powershell
# Verifica que Python esté instalado: python --version
# Si cambiaste de equipo o de versión de Python, recrea el entorno:
python -m venv venv --clear
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

**Error al activar el entorno en PowerShell**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Error: "No migrations to apply"**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Error: "Table already exists"**
```bash
# Elimina el archivo db.sqlite3 y ejecuta:
python manage.py migrate
```

## Desarrollo

Para añadir nuevas funcionalidades:
1. Modifica los modelos en `core/models.py`
2. Ejecuta `python manage.py makemigrations`
3. Ejecuta `python manage.py migrate`
4. Añade las vistas en `core/views.py`
5. Crea los templates en `core/templates/core/`
6. Añade las URLs en `core/urls.py`

## Licencia

Este proyecto es de uso personal para la gestión de un consultorio odontológico.
