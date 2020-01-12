#!/usr/bin/python3

from re import search
from requests import Session
from requests.exceptions import ConnectionError
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse
from json import loads

class Analizer:
    def __init__(self, url_sitio, cms_json = None, verbose = False, user_ag = None):
        # Atributos
        self.root = None
        self.cms = None
        self.enabled_methods = []
        self.version = None
        self.installed_plugins = []
        self.installed_themes = []

        self.verbose = verbose

        # Atributos auxiliares en los metodos
        self.count_plugins = 20
        self.count_themes = 20
        self.user_agent = user_ag if user_ag != None else 'Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/60.0'
        
        if not cms_json:
            raise ValueError("Es necesario especificar la ruta del archivo de datos sobre CMS")
        else:
            self.cms_dir = cms_json

        # Este atributo es la URL que se va a analizar en busca de CMS
        self.sitio = url_sitio

        if not url_sitio:
            raise ValueError("Es necesario especificar la URL del sitio")
        if not self.verify_url(self.sitio):
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

    ###################################
    ######## ES NECESARIA?  ###########
    ###################################
    def get_enabled_methods(self):

        s=Session()
        headers={}
        headers['User-agent']=self.user_agent

        salida = []
        s.mount(self.sitio, HTTPAdapter(max_retries=2))

        if s.put(self.sitio, headers=headers).status_code == 200:
            salida.append("put")
        if s.get(self.sitio, headers=headers).status_code == 200:
            salida.append("get")
        if s.options(self.sitio, headers=headers).status_code == 200:
            salida.append("options")
        if s.post(self.sitio, headers=headers).status_code == 200:
            salida.append("post")
        if s.delete(self.sitio, headers=headers).status_code == 200:
            salida.append("delete")
        if s.head(self.sitio, headers=headers).status_code == 200:
            salida.append("head")
        if s.patch(self.sitio, headers=headers).status_code == 200:
            salida.append("patch")

        return salida

    def make_requests(self, full_url, files2search):
        """
            Metodo que realiza una peticion HEAD al recurso dado como
            parametro (full_url), si se obtiene un codigo 200 o 403 asumimos
            que tal recurso existe.

            Retorna cuantos recursos existen de la lista dada como segundo
            argumento (files2search).
        """
        cont=0
        try:
            for fl in files2search:
                url_file = ""
                # Concatenacion de URL y recurso a buscar
                # agrega el / si es necesario

                if full_url[-1] != '/':
                    url_file = full_url + '/' + fl
                else:
                    url_file = full_url + fl

                s=Session()
                headers={}
                headers['User-agent']=self.user_agent
                s.mount(url_file, HTTPAdapter(max_retries=2))

                response=s.head(url_file,headers=headers)

                if (response.status_code == 200  or response.status_code == 403):
                    message='\t%s : File found    (CODE:%d)' %(url_file,response.status_code)
                    print(message) if self.verbose else None
                    cont+=1
        
        except ConnectionError:
            pass

        finally:
            return cont
    
    def get_root(self, files_dict):
        """
            Metodo que busca la raiz de un CMS en cada recurso de la URL base.
            Itera por cada recurso y en cada uno busca un CMS.

            Retorna una tupla de la URL donde encontro coincidencias con un CMS
            y cuantas coincidencias de archivos generales (del CMS) encontro.
        """

        # Obtiene los archivos comunes en raiz del CMS en cuestion
        # estructura del diccionario -> {'numero_identificador' : 'recurso_en_raiz'}

        files_v = list(files_dict.values())

        # Particion de la URL en '/'
        recursos=urlparse(self.sitio).path.split("/")[1:]

        # Enlistado de los recursos URL base del sitio
        urls = ['/'+'/'.join(recursos[:x+1]) for x in range(len(recursos))]
        urls = [''] if len(urls) == 0 else urls

        base_url= urlparse(self.sitio).scheme+'://'+urlparse(self.sitio).netloc

        # Se buscan los archivos comunes de un CMS en cada recurso desde la url base
        for u in urls:
            full_url = base_url+u
            founded_files = self.make_requests(full_url, files_v)
            if founded_files > 0:
                return (full_url, founded_files)

        return (None, 0)

    def search_cms(self):
        max_coincidences = 0
        with open(self.cms_dir, "r") as cmsJSON:
            cms_json = loads(cmsJSON.read())

        for cms in cms_json.keys():
            temp_root, temp_coincidences = self.get_root(cms_json[cms]["check_root"])
            if  temp_coincidences > max_coincidences:
                self.cms = cms_json[cms]['cms']
                self.root = temp_root
                max_coincidences = temp_coincidences

        if self.cms:
            print("Raiz del CMS encontrada") if self.verbose else None
            print (self.cms) if self.verbose else None
            print (self.root) if self.verbose else None

                        
    def search_version(self, version_dirs):
        """
            Funcion que busca la version del cms a partir de los recursos
            y los patrones de busqueda dados en el json.
            Devuelve True si encuentra la version, False en caso contrario
        """

        #Iteramos si se dan varias tuplas de busqueda
        for  gv in version_dirs:
            try:
                #El formato en el json es recurso;patron_de_busqueda
                resource, patron = gv.split(';')
                resource = self.root + '/' + resource if self.root[-1] != '/' else self.root + resource

                #buscamos el patron en el codigo fuente del recurso, obteniendo 20 caracteres inmediatos
                #anteriores y 30 inmediatos posteriores
                s = Session()
                s.mount(resource, HTTPAdapter(max_retries=2))
                # fragmento donde viene el patron a buscar para obtener la version
                print("Buscando version en " + resource) if self.verbose else None
                patron_founded = search('(.{0,20}' + patron + '.{1,30})', s.get(resource).text)
                if patron_founded:
                    #Dentro de este string buscamos el numero de version nn.nn.nn
                    # version : nn.nn.nn
                    # version2: nn (sin punto decimal)
                    version = search(patron + '.*([1-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2})', patron_founded.group(1))
                    version2 = search(patron + '.*([1-9]{1,2}\.?[0-9]{0,2}\.?[0-9]{0,2})', patron_founded.group(1))
                    if version:
                        print('Version encontrada!!!!') if self.verbose else None
                        print("----------> Version: " + version.group(1)  + " <----------") if self.verbose else None
                        return version.group(1)

                    elif version2:
                        print('Version encontrada!!!!') if self.verbose else None
                        print("----------> Version: " + version2.group(1)  + " <----------") if self.verbose else None
                        return version2.group(1)
            except ConnectionError:
                pass
        return False

    def check_version(self):
        """
            Metodo para buscar la version del CMS encontrado.
            Obtiene el recurso de donde buscar y que patron buscar del archivo JSON
            de configuracion.
            si se encuentra la version, se actualiza el atributo self.version
        """
        with open(self.cms_dir, "r") as cms_data:
            data = loads(cms_data.read())
        if self.cms:
            try: 
                vers = list(data[self.cms]["check_version"].values())
                version = self.search_version(vers)
                if version:
                    self.version = version

            except KeyError:
                pass

    def get_plugins(self):
        """
            Metodo para buscar plugins habilitados en el CMS.
            Obtiene los directorios donde se encuentran los plugins del
            JSON de configuracion asi como la ruta al archivo de los plugins
            de tal CMS.
        """
        with open(self.cms_dir, "r") as cmsJSON:
            cms_json = loads(cmsJSON.read())

        plugins_dir = cms_json[self.cms]['plugins_dir']
        plugins_txt = cms_json[self.cms]['plugins']

        if self.root[-1] != '/':
            plugins_dir = self.root + '/' + plugins_dir
        else:
            plugins_dir = self.root + plugins_dir
        
        # Lista donde se almacenan los plugins instalados
        installed_plugins = []
        # Contador de plugins que han sido buscados
        cont = 0
        try:
            with open(plugins_txt, "r") as plugins_file:
                # Itera por cada plugin en el archivo para buscarlo
                for plugin in plugins_file:
                    cont += 1
                    # quita el salto de linea
                    plugin = plugin[:-1]
                    url2plugin = plugins_dir + plugin
                    print("Buscando plugin  " + url2plugin) if self.verbose else None
                    s=Session()
                    s.mount(url2plugin, HTTPAdapter(max_retries=2))
                    headers={}
                    headers['User-agent'] = self.user_agent
                    response=s.head(url2plugin, headers=headers)

                    if (response.status_code >= 200 or response.status_code == 403):
                        print("\tPlugin " + plugin + " encontrado!") if self.verbose else None
                        installed_plugins.append(plugin)

                    # Control para detener la busqueda inmensa de plugins
                    if cont == self.count_plugins:
                        break

                self.installed_plugins = installed_plugins

        except IOError:
            print("error al abrir el archivo" + plugins_txt)

    def get_themes(self):
        if self.cms == "Joomla!":
            return None

        with open(self.cms_dir, "r") as cmsJSON:
            cms_json = loads(cmsJSON.read())

        themes_dir = list(cms_json[self.cms]['themes_dir'].values())
        themes_txt = cms_json[self.cms]['themes']

        themes_l = []
        for directory in themes_dir:
            cont = 0
            if self.root[-1] != '/':
                directory = self.root + '/' + directory
            else:
                directory = self.root + directory

            with open(themes_txt, "r") as themes_list:
                for theme in themes_list:
                    cont += 1
                    theme = theme[:-1]
                    url2theme = directory + theme
                    print("Buscando  " + url2theme) if self.verbose else None
                    s=Session()
                    s.mount(url2theme, HTTPAdapter(max_retries=2))
                    headers={}
                    headers['User-agent']=self.user_agent
                    response=s.head(url2theme, headers=headers)
                    #Si se obtiene respuesta 200 o 403, es que este recurso existe
                    if (response.status_code >= 200 or response.status_code == 403):
                        print("\tTema " + theme + " encontrado!!") if self.verbose else None
                        themes_l.append(theme)
                    if cont >= self.count_themes:
                        break

        self.installed_themes = themes_l

    def get_last_info(self):
        """
            Metodo que invoca los metodos adicionales a realizar una vez
            que se ha encontrado la raiz del CMS. Busca informacion adicional
            del sitio
        """

        self.check_version()
        self.get_plugins()
        self.get_themes()


if  __name__ == "__main__":
    an = Analizer("http://localhost/wordpress/", "/home/proy/Documents/cms.json", True)
    an.search_cms()
    an.get_last_info()
    print(an.version)