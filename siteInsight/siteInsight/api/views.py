from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render_to_response
#from django.template import RequestContext

def index(request):
    """
        Response con el archivo index.html
    """
    return render_to_response('index.html')

def update_config(request):
    # Se necesita de una cookie para la cabecera de CSRF
    #context = RequestContext(request)

    """Cuando recibe la peticion post con el archivo de configuracion
        redirecciona a la funcion que actualizara los valores leidos del
        archivo
    """
    if request.method == 'POST' and request.FILES['fileToUpload']:
        print("yes")
        handle_update_file(request.FILES['fileToUpload'])
        return render(request, 'index.html', {
            'uploaded_file': True
        })
    else:
        print("no")
        return render(request, 'index.html')

def handle_update_file(f):
    """
        Funcion para actualizar los valores leidos del archivo de configuracion
        de la herramienta
    """
    print("work!")
