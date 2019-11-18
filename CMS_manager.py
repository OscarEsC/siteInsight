from Analizer import Analizer
from threading import Thread, Lock
from time import sleep

class CMS_manager:
    def __init__(self, site_url=None):
        self.cms_dict = {}
        self.current_site = site_url
        self.lock = Lock()

    def set_current_site(self, site_url):
        self.lock.acquire()
        self.current_site = site_url
        self.lock.release()

    def is_in_dict(self):
        self.lock.acquire()
        flag = False
        for root_cms in self.cms_dict.keys():
            flag = root_cms in self.current_site
            if flag:
                self.lock.release()
                return True

        # Si no se ha encontrado un CMS en la URL del sitio dado
        self.lock.release()
        return False

    def analize_thread(self):
        temp = Analizer(self.current_site, "/home/proy/Documents/cms.json")
        temp.find_cms()
        if temp.cms:
            self.lock.acquire()
            self.cms_dict[temp.root] = temp
            self.lock.release()

    def analize_it(self):
        if not self.is_in_dict():
            Thread(target=self.analize_thread, args=(), daemon=True).start()
        else:
            print("analized before")

    # Funcion para hacer el resto del analisis por cada elemento de cms_dict



if __name__ == "__main__":
    ll = ["http://localhost/drupal", "http://localhost/wordpress", "http://localhost/joomla"]  
    ll2 = ["http://localhost/drupal", "http://localhost/wordpress", "http://localhost/joomla", "http://localhost/wordpress/index.php/2019/11/04/hello-world/"]

    aa = CMS_manager()
    for ur in ll:
        aa.set_current_site(ur)
        aa.analize_it()

    sleep(10)
    for key in aa.cms_dict.keys():
        print("################")
        print(aa.cms_dict[key].root)
        print(aa.cms_dict[key].cms)

    aa.set_current_site("http://localhost/wordpress/index.php/2019/11/04/hello-world/")
    aa.analize_it()