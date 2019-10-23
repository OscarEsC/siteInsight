from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render_to_response
import json


def index(request):
    """
        Response con el archivo index.html
    """
    return render_to_response('index.html')

# ------------------------------------------------
# funciones para actualizacion de configuracion de
# la herramienta
# ------------------------------------------------

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

# Funcion en potencia modular
def handle_update_file(config_f):
    """
        Funcion para actualizar los valores leidos del archivo de configuracion
        de la herramienta
    """

    # Si se intenta subir un archivo mayor a 2MB se retorna una etiqueta
    # de error y no se actualizara la configuracion
    if config_f.size > 2048:
        return render(request, 'index.html', {
            'exceeded_size': True
        })
    else:
        # decode para casteo de binary a string
        new_configuration = config_f.read().decode('utf8')
        # data es el diccionario JSON
        data = json.loads(new_configuration)
        print(data["google_key"])



def get_public_information(request):
    """
        Response con el archivo public_information.html
    """
    return render_to_response('public_information.html')

# funcion en potencia modular
def load_sites(request):
    if request.method == 'POST' and request.FILES['sites_file']:
        print("work!")