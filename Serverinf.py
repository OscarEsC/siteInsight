#!/usr/bin/python3

from re import search
from requests import Session
from requests.exceptions import ConnectionError
from requests.adapters import HTTPAdapter
from json import loads

class Serverinf:
    def __init__(self, url_site=None, user_agent=None, verbose=False):
        self.site = url_site
        self.verbose = verbose
        self.user_agent = user_agent if user_agent != None else 'Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/60.0'

        if not url_site:
            raise ValueError("Es necesario especificar la URL del sitio")
        if not self.verify_url(self.site):
            raise ValueError("No es una URL valida")
        

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

    def passive_find_server_header(self):
        """
            Metodo que realiza una peticion al sitio y busca en las cabeceras
            la cabecera 'Server' para identificar el servidor y su version en caso
            de ser posible
        """
        ### patron = (servidor)(/(ve.rs.ion) (otros datos))
        ### grupo1 = servidor
        ### grupo3 = version or None
        ### grupo4 == otros datos or None
        info_pattern = "(\w*)(/(\d{1,2}.?\d{0,2}.?\d{0,2}) ?(.*)?)?"



        s=Session()
        headers={}
        headers['User-agent']=self.user_agent
        s.mount(self.site, HTTPAdapter(max_retries=2))

        response=s.head(self.site, headers=headers)
        pattern = search(info_pattern, response.headers['Server'])


        print(pattern.groups())
        print(pattern.group(1))
        print(pattern.group(3))
        print(pattern.group(4))


        #######################
        ## Para las comparaciones de los headers>
        ## siempre aparecen en letra capital o es mejor hacer un lower para comparar cadenas?
        ############################

if __name__ == "__main__":
    #si = Serverinf("https://dl6698.com/main.html") #nginx
    #si = Serverinf("http://localhost:81/") #nginx
    si = Serverinf("http://200.23.34.40/ecofronteras/index.php/eco") # apache
    #si = Serverinf("http://189.237.34.140:8012/")
    #si = Serverinf("http://23.245.97.28:999/") # IIS

    si.passive_find_server_header()