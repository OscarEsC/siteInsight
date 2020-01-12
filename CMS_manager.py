#!/usr/bin/python3


from Analizer import Analizer
from IOC import IOC
from threading import Thread, Lock, active_count
import threading
from requests import head
from requests.exceptions import ConnectionError
from re import search


class CMS_manager:
    def __init__(self, url_site=None, verbose=False):
        # Estructura del diccionario -> {"raiz_cms": [Objeto_Analizer (, url_donde_se_encontro_websh)]}
        self.cms_dict = {}
        self.current_site = url_site
        self.lock = Lock()
        self.verbose = verbose
        self.ioc = IOC(verbose = verbose)

    def set_current_site(self, url_site):
        self.lock.acquire()
        self.current_site = url_site
        print("Sitio actual -> " + self.current_site) if self.verbose else None
        self.lock.release()

    def is_in_dict(self):
        self.lock.acquire()
        flag = False
        print("Buscando en el diccionario -> " + self.current_site) if self.verbose else None
        for root_cms in self.cms_dict.keys():
            print("\t" + root_cms) if self.verbose else None
            flag = root_cms in self.current_site
            if flag:
                self.lock.release()
                return True

        # Si no se ha encontrado un CMS en la URL del sitio dado
        self.lock.release()
        return False

    def analize_thread(self):
        temp = Analizer(self.current_site, "/home/proy/Documents/cms.json", verbose=self.verbose)
        try:
            temp.search_cms()
            if temp.cms:
                self.lock.acquire()
                self.cms_dict[temp.root] = temp
                self.lock.release()
        
        except ConnectionError:
            pass

        finally:
            del temp

    def analize_it(self):
        """
            Metodo que inicia dos hilos para analizar la url recibida por
            el crawler en busca de CMS o de indicadores de compromiso (webshell y sw de minado)
        """
        if not self.is_in_dict():
            Thread(target=self.analize_thread, args=(), daemon=True).start()
            Thread(target=self.ioc.new_site, args=(self.current_site,), daemon=True).start()
        else:
            print(self.current_site + " analized before") if self.verbose else None

    def new_url(self, crawl_url):
        self.set_current_site(crawl_url)
        self.analize_it()
    

    # Funcion para hacer el resto del analisis por cada elemento de cms_dict
    def traverse_dict(self):
        print("Esperando que todos los hilos concluyan") if self.verbose else None
        while(active_count() > 1):
            pass

        for value in list(self.cms_dict.values()):
            Thread(target=value.get_last_info(), args=(), daemon=True).start()          

if __name__ == "__main__":
    ll = ["http://localhost/drupal", "http://localhost/wordpress", "http://localhost/joomla", "https://www.malware.unam.mx"]  
    #ll2 = ["http://localhost/drupal", "http://localhost/wordpress", "http://localhost/joomla", "http://localhost/wordpress/index.php/2019/11/04/hello-world/"]

    aa = CMS_manager(verbose=True)
    for ur in ll:
        aa.set_current_site(ur)
        aa.analize_it()

    aa.traverse_dict()

    while(active_count() > 1):
            pass


    for key in aa.cms_dict.keys():
        print("################")
        print(aa.cms_dict[key].root)
        print(aa.cms_dict[key].cms)
        print(aa.cms_dict[key].version)
        print(aa.cms_dict[key].installed_plugins)
        print(aa.cms_dict[key].installed_themes)

    #aa.set_current_site("http://localhost/wordpress/index.php/2019/11/04/hello-world/")
    #aa.analize_it()