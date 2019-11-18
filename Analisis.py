from re import search
from requests import Session
from requests.exceptions import ConnectionError
from os.path import isfile
from urllib.parse import urlparse
from json import loads
from time import sleep

class Analisis:
    def __init__(self, url_sitio, cms_json = None, user_ag = None):
        self.root = None
        self.cms = None
        self.count_plugins = 20
        self.count_themes = 20
        self.user_agent = user_ag if user_ag != None else 'Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/60.0'
        
        if not cms_json:
            raise ValueError("Es necesario especificar la ruta del archivo de datos sobre CMS")
        else:
            self.cms_dir = cms_json

        self.sitio = url_sitio
        if not url_sitio:
            raise ValueError("Es necesario especificar la URL del sitio")
        if not self.verify_url(self.sitio):
            raise ValueError("No es una URL valida")

    def verify_url(self, url):
        '''
        Funcion que verifica los argumentos minimos para poder ejecutar el programa
        '''
        http_re=r"http://.*(:[0-9]{0,4})?(/.*)?/?$"
        https_re=r"https://.*(:[0-9]{0,4})?(/.*)?/?$"
        if not search(https_re, url):
            if not search(http_re, url):
                return False

        return True

    def get_enabled_methods(self):

        s=Session()
        headers={}
        headers['User-agent']=self.user_agent

        salida = []
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

        print ("Metodos habilitados")
        print(salida)
        return salida

    def make_requests(self, full_url, files2search, sleep_time=0):

        cont=0
        #try:
        for fl in files2search:
            url_file = ""
            if full_url[-1] != '/':
                url_file = full_url + '/' + fl
            else:
                url_file = full_url + fl
            s=Session()
            headers={}
            headers['User-agent']=self.user_agent
            response=s.head(url_file,headers=headers)
            if ((response.status_code >= 200 and response.status_code < 400) or response.status_code == 403):
                #if "content-length" in  response.headers:
                #    message='\t%s : File found    (CODE:%d|SIZE:%d)' %(url_file,response.status_code,response.headers['content-length'])
                #else:
                message='\t%s : File found    (CODE:%d)' %(url_file,response.status_code)
                print(message)
                cont+=1
            #else:
            #    message='\t%s : File not found    (CODE:%s)' %(url_file,str(response.status_code))

            sleep(sleep_time)

        #except ConnectionError:
        #    print("Error de conexion")

        #finally:
        return cont
    
    def get_root(self, files_dict):
        """
            Funcion que nos devuelve la raiz del sitio dado
            a partir de aqui se buscan todos los recursos
        """
        files_v = list(files_dict.values())
        recursos=urlparse(self.sitio).path.split("/")[1:]
        urls = ['/'+'/'.join(recursos[:x+1]) for x in range(len(recursos))]
        if '/' not in urls:
            urls.insert(0,'/')
        base_url= urlparse(self.sitio).scheme+'://'+urlparse(self.sitio).netloc

        for u in urls:
            full_url = base_url+u
            cont = self.make_requests(full_url, files_v)
            if cont > 0:
                self.root = full_url + "/"
                return (full_url + "/", cont)

        return (None, 0)

    def find_cms(self):
        with open(self.cms_dir, "r") as cmsJSON:
            cms_json = loads(cmsJSON.read())

        max_cont = 0
        probably = None
        root = ""
        for cms in cms_json.keys():
            root2, cont = self.get_root(cms_json[cms]["check_root"])
            if cont > max_cont:
                probably = cms_json[cms]['cms']
                max_cont = cont
                root = root2

        if probably:
            print("Raiz del CMS encontrada")
            self.cms = probably
            print (self.cms)
            print (root)
    
    def search_version(self, version_dirs):
        """
            Funcion que busca la version del cms a partir de los recursos
            y los patrones de busqueda dados en el json.
            Devuelve True si encuentra la version, False en caso contrario
        """

        #Iteramos si se dan varias tuplas de busqueda
        for  gv in version_dirs:
            #El formato en el json es recurso;patron_de_busqueda
            resource, patron = gv.split(';')
            #buscamos el patron en el codigo fuente del recurso, obteniendo 20 caracteres inmediatos
            #anteriores y 30 inmediatos posteriores
            s = Session()
            patron_founded = search('(.{0,20}' + patron + '.{1,30})', s.get(self.root + resource).text)
            if patron_founded:
                #Dentro de este string buscamos el numero de version nn.nn.nn
                version = search(patron + '.*([1-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2})', patron_founded.group(1))
                version2 = search(patron + '.*([1-9]{1,2}\.?[0-9]{0,2}\.?[0-9]{0,2})', patron_founded.group(1))
                if version:
                    print('Version encontrada!!!!')
                    print("----------> Version: " + version.group(1)  + " <----------")
                    return version.group(1)

                elif version2:
                    print('Version encontrada!!!!')
                    print("----------> Version: " + version2.group(1)  + " <----------")
                    return version2.group(1)

        return False

    def check_version(self):
        with open(self.cms_dir, "r") as cms_data:
            data = loads(cms_data.read())
        if self.cms:
            try: 
                vers = list(data[self.cms]["check_version"].values())
                version = self.search_version(vers)
                if version:
                    print(version)

            except KeyError:
                pass

    def get_plugins(self):
        with open(self.cms_dir, "r") as cmsJSON:
            cms_json = loads(cmsJSON.read())

        plugins_dir = cms_json[self.cms]['plugins_dir']
        plugins_txt = cms_json[self.cms]['plugins']
        
        #Lista donde se almacenan los plugins instalados
        installed_plugins = []
        cont = 0
        try:
            with open(plugins_txt, "r") as plugins_file:
                for plugin in plugins_file:
                    cont += 1
                    plugin = plugin[:-1]
                    url2plugin = self.root + plugins_dir + plugin
                    s=Session()
                    headers={}
                    headers['User-agent']=self.user_agent
                    response=s.head(url2plugin, headers=headers)

                    if ((response.status_code >= 200 and response.status_code<400) or response.status_code == 403):
                        installed_plugins.append(plugin)
                    if cont == self.count_plugins:
                        break

                print ("plugins instalados")
                print (installed_plugins)
                return installed_plugins

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
            with open(themes_txt, "r") as themes_list:
                for theme in themes_list:
                    cont += 1
                    theme = theme[:-1]
                    url2theme = self.root + directory + theme
                    s=Session()
                    headers={}
                    headers['User-agent']=self.user_agent
                    response=s.head(url2theme, headers=headers)
                    #Si se obtiene respuesta 200 o 403, es que este recurso existe
                    if ((response.status_code >= 200 and response.status_code < 400) or response.status_code == 403):
                        themes_l.append(theme)
                    if cont >= self.count_themes:
                        break

        print ("temas instalados")
        print(themes_l)
        return themes_l

    def get_files(self):
        with open(self.cms_dir, "r") as cmsJSON:
            cms_json = loads(cmsJSON.read())

        check_files = list(cms_json[self.cms]["check_files"].values())
        file_list = []
        for f_file in check_files:
            url2file = self.root + f_file
            s=Session()
            headers={}
            headers['User-agent']=self.user_agent
            response=s.head(url2file, headers=headers)
            if ((response.status_code >= 200 and response.status_code < 400) or response.status_code == 403):
                file_list.append((f_file, response.status_code))

        print ("Se encontraron los archivo con el codigo de respuesta:")
        print (file_list)

        return file_list


an = Analisis("http://conexiones.dgire.unam.mx/", "/home/proy/Documents/cms.json")
an.get_enabled_methods()
an.find_cms()
an.check_version()
an.get_plugins()
an.get_themes()
an.get_files()