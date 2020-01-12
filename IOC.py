#!/usr/bin/python3

from re import search
from requests import head

class IOC:
    def __init__(self, commons = "commons.txt", verbose = False):
        self.websh_vuln = []
        self.site = None
        self.commons = commons
        self.verbose = verbose

    def new_site(self, nsite):
        self.site = nsite
        self.search_websh()
        self.search_miner()

    def search_websh(self):
        """
            Metodo para buscar webshells comunes existentes en el servidor
            Se buscan solo tomando como base el directorio uploads
        """
        uploads = "(.*/uploads?/)"
        reu = search (uploads, self.site)
        if reu:
            with open(self.commons, "r") as wbf:
                for wb in wbf:
                    print("Request  a " + reu.group(1) + wb[:-1]) if self.verbose else None
                    if head(reu.group(1) + wb[:-1]).status_code == 200:
                        print("Webshell encontrada!!!") if self.verbose else None
                        print(reu.group(1) + wb[:-1]) if self.verbose else None
                        self.websh_vuln.append(reu.group(1) + wb[:-1])
                        break

    def search_miner(self):
        pass