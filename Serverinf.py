#!/usr/bin/python3

from re import search
from requests import Session
from requests.exceptions import ConnectionError
from requests.adapters import HTTPAdapter
from json import loads
from random import choice
from string import ascii_letters, digits

class Serverinf:
    def __init__(self, url_site=None, srv_json=None, user_agent=None, verbose=False):
        self.site = url_site
        self.server = None
        self.version = None
        self.other_data = None

        self.verbose = verbose
        self.user_agent = user_agent if user_agent != None else 'Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/60.0'

        if not url_site:
            raise ValueError("Es necesario especificar la URL del sitio")
        if not self.verify_url(self.site):
            raise ValueError("No es una URL valida")

        if not srv_json:
            raise ValueError("Es necesario especificar la ruta del archivo de datos sobre el servidor")
        else:
            self.srv_dir = srv_json
        

    def verify_url(self, url):
        '''
            Funcion que verifica que la URL dada al constructor sea valida.
        '''
        http_re=r"http://.*(:[0-9]{0,4})?(/.*)?/?$"
        https_re=r"https://.*(:[0-9]{0,4})?(/.*)?/?$"

        # Busca ambas expresiones regulares en la cadena
        if not search(https_re, url):
            if not search(http_re, url):
                return False

        return True

    def update_site(self, url_site):
        self.site = url_site

        if not self.verify_url(self.site):
            raise ValueError("No es una URL valida")

    def passive_search_server_header(self):
        """
            Metodo que realiza una peticion al sitio y busca en las cabeceras
            la cabecera 'Server' para identificar el servidor y su version en caso
            de ser posible
        """
        ### patron = (servidor)(/(ve.rs.ion) (otros datos))
        ### grupo1 = servidor
        ### grupo3 = version or None
        ### grupo4 == otros datos or None
        info_pattern = "([\w-]*)(/(\d{1,2}.?\d{0,2}.?\d{0,2}) ?(.*)?)?"


        s=Session()
        headers={}
        headers['User-agent']=self.user_agent
        s.mount(self.site, HTTPAdapter(max_retries=2))

        response=s.head(self.site, headers=headers)

        # Si no existe la cabecera 'Server' se retorna falso
        # para utilizar otro metodo
        if not response.headers['Server']:
            return False

        pattern = search(info_pattern, response.headers['Server'])

        self.server = pattern.group(1)
        self.version = pattern.group(3)
        self.other_data = pattern.group(4)

        print("##############") if self.verbose else None
        print(si.site) if self.verbose else None
        print(self.server) if self.verbose else None
        print(self.version) if self.verbose else None
        print(self.other_data) if self.verbose else None

        return True

    def passive_search_order_headers(self):
        """
            Metodo que realiza una peticion al sitio e intenta inferir el
            servidor por el orden en que aparecen los encabezados de la respuesta
            del servidor. Util cuando la cabecera 'Server' ha sido omitida en la respuesta
        """

        with open(self.srv_dir, "r") as sjson:
            srv_json = loads(sjson.read())
        
        s=Session()
        headers={}
        headers['User-agent']=self.user_agent
        s.mount(self.site, HTTPAdapter(max_retries=2))

        response=s.head(self.site, headers=headers)

        probably_server = self.infer_server(srv_json, [x for x in response.headers])

        if probably_server:
            self.server = probably_server

        print("se infirio el servidor")
        print(self.server)

    def infer_server(self, srv_json, headers_list):
        """
            Metodo para inferir el servidor buscando en el JSON la
            llave 'in_order'
        """
        probably_server = None

        for server_name in list(srv_json.keys()):

            in_order = srv_json[server_name]['in_order']
            print("Buscando similitud con", server_name) if self.verbose else None
            tmp, occurencies = 0, 0

            for h in in_order:
                j = 0
                while( tmp + j  < len(headers_list)):
                    print("\tComparando ", h, headers_list[tmp + j])  if self.verbose else None
                    if h == headers_list[tmp + j]:
                        occurencies += 1
                        tmp += j + 1
                        break
                    
                    j += 1

            # Si existen mas de 3 coincidencias en el orden, se supone que se ha
            # encontrado el servidor
            if occurencies >= 3:
                probably_server = server_name
                break

        return probably_server

    def passive_search_in_content(self):
        """
            Metodo para buscar informacion del servidor en el contenido
            buscando despues de la etiqueta (HTML) <hr> el nombre de uno de
            los servidores en el archivo de configuracion
        """

        with open(self.srv_dir, "r") as sjson:
            srv_json = loads(sjson.read())

        # Generamos un eror 404 donde normalmente se muestra la version del servidor
        e404 = ''.join([choice(ascii_letters + digits) for n in range(8)])
        if self.site[-1] == '/':
            e404 = self.site + e404
        else:
            e404 = self.site + '/' + e404

        s=Session()
        headers={}
        headers['User-agent']=self.user_agent
        s.mount(self.site, HTTPAdapter(max_retries=2))

        response=s.get(self.site, headers=headers)

        # Buscamos cada servidor en el archivo de configuracion en los
        # ultimos 100 caracteres del contenido del sitio
        for server_name in list(srv_json.keys()):
            pattern = search("(" + server_name + ".{1,10})", response.text[-100:])
            if pattern:
                info_pattern = "([\w-]*)/?(\d{0,2}.?\d{0,2}.?\d{0,2})"
                patternn = search(info_pattern, pattern.group(1))
                print("servidor " + patternn.group(1))  if self.verbose else None
                print("version " + patternn.group(2)) if self.verbose else None

    def passive_search(self):

        if not self.passive_search_server_header():
            self.passive_search_order_headers()
    
if __name__ == "__main__":
    ll = ["https://dl6698.com/main.html", "http://200.23.34.40/ecofronteras/index.php/eco", "http://23.245.97.28:999/", "https://www.malware.unam.mx"]
    #si = Serverinf("https://dl6698.com/main.html") #nginx
    #si = Serverinf("http://localhost:81/") #nginx
    #si = Serverinf("http://200.23.34.40/ecofronteras/index.php/eco") # apache
    #si = Serverinf("http://189.237.34.140:8012/")
    #si = Serverinf("http://23.245.97.28:999/") # IIS

    si = Serverinf("http://download.dominiosistemas.com.br/atualizacao/contabil/", "/home/proy/Documents/server.json", verbose=True)
    si.passive_search()
    
    """
    for ind in ll:
        si.update_site(ind)
        si.passive_search_server_header()

    """
    
