class NgrokSkipWarningMiddleware:
    """
    Middleware для автоматического пропуска страницы предупреждения ngrok.
    Добавляет заголовок 'ngrok-skip-browser-warning' ко всем запросам.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Добавляем заголовок для пропуска страницы ngrok
        request.META['HTTP_NGROK_SKIP_BROWSER_WARNING'] = 'true'
        
        response = self.get_response(request)
        
        # Также добавляем заголовок в ответ (для некоторых версий ngrok)
        response['ngrok-skip-browser-warning'] = 'true'
        
        return response
