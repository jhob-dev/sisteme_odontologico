from django.utils import timezone


class PageCacheMiddleware:
    """Permite que el navegador reutilice páginas GET durante un corto periodo.

    Esto reduce el retardo percibido entre cambios de vista: la primera carga
    se hace normalmente y las navegaciones siguientes (o el precargado con
    <link rel="prefetch">) se sirven desde la caché del navegador.

    Cuando una vista muta datos (POST que termina en redirect), se actualiza
    la cookie ``ce`` (cache epoch). Como las páginas cacheadas varían por la
    cabecera Cookie, ese cambio invalida la caché y la siguiente navegación
    trae datos frescos.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method == 'POST' and response.status_code in (301, 302, 303):
            response.set_cookie(
                'ce',
                str(int(timezone.now().timestamp())),
                max_age=60 * 60 * 24 * 365,
                samesite='Lax',
            )

        content_type = response.get('Content-Type', '')
        if (
            request.method == 'GET'
            and getattr(request, 'user', None) is not None
            and request.user.is_authenticated
            and response.status_code == 200
            and content_type.startswith('text/html')
        ):
            response['Cache-Control'] = 'private, max-age=60'
            vary = response.get('Vary', '')
            if 'cookie' not in vary.lower():
                response['Vary'] = (vary + ', Cookie').strip(', ')
        return response
