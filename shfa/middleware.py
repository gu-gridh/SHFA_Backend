import sys


class FixAdminOriginMiddleware:
    """Fix CSRF origin checking for admin - origin is null on some browsers/redirects"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Always log full headers for admin POSTs to see why check fails
        if request.method == 'POST' and '/admin/' in request.path:
            origin = request.META.get('HTTP_ORIGIN')
            sys.stderr.write(f"\n[CSRF DEBUG] POST to {request.path}\n")
            sys.stderr.write(f"[CSRF DEBUG] Origin: '{origin}' (type: {type(origin)})\n")
            
            # Host header
            host = request.get_host()
            sys.stderr.write(f"[CSRF DEBUG] Host: {host}\n")
            
            # Force set origin if missing/null
            if not origin or origin == 'null':
                new_origin = f"https://{host}"
                request.META['HTTP_ORIGIN'] = new_origin
                sys.stderr.write(f"[CSRF FIX] FORCED Origin to: {new_origin}\n")
            
            sys.stderr.flush()
        
        return self.get_response(request)
