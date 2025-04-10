#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper de anúncios do Imovelweb via URL de busca.
Detecta cidade e operação automaticamente, coleta todos os anúncios,
e permite colar os cookies manualmente ou passar via argumento.
"""

import json
import os
import time
import argparse
import re
from datetime import datetime, timezone
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup

CITY_IDS = {
    "sao-bernardo-do-campo": "109670",
    "sao-paulo": "109668",
    "campinas": "109673",
}

STATE_FILE = "scraper_state.json"

class ImovelWebScraper:
    def __init__(self, output_file="listings.json", cookies_file="cookies.json"):
        self.output_file = output_file
        self.cookies_file = cookies_file
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
            "Accept": "*/*",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.imovelweb.com.br",
            "Connection": "keep-alive",
        }
        self.url = "https://www.imovelweb.com.br/rplis-api/postings"
        self.params = {"dynamicListingSearch": "true", "enableStepSA": "true"}
        self.payload = {
            "tipoDePropiedad": "2",
            "tipoDeOperacion": "1",
            "preTipoDeOperacion": "1",
            "superficieCubierta": 1,
            "idunidaddemedida": 1,
            "province": "265",
            "sort": "relevance",
        }
        self._load_cookies()
        self.state = self._load_state()

    def _load_cookies(self):
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    for name, value in cookies.items():
                        self.session.cookies.set(name, value)
            except json.JSONDecodeError:
                print("Erro ao carregar cookies. Continuando sem.")

    def _save_cookies(self):
        cookies = {c.name: c.value for c in self.session.cookies}
        with open(self.cookies_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print("Cookies salvos com sucesso.")

    def update_cookies_manualmente(self):
        print("\nCole abaixo TODO o cabeçalho Cookie copiado do DevTools (F12):")
        cookie_str = input("Cookie: ").strip()
        if not cookie_str:
            print("Nenhum cookie colado.")
            return

        cookies = {}
        for item in cookie_str.split(";"):
            if "=" in item:
                name, value = item.strip().split("=", 1)
                cookies[name] = value
        with open(self.cookies_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print("Cookies colados e salvos!")
        self._load_cookies()

    def _save_listings(self, data):
        if os.path.exists(self.output_file):
            with open(self.output_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []

        existing.extend(data)
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"Total de anúncios acumulados: {len(existing)}")

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"last_page": 0, "total_listings": 0, "last_run": None}

    def _save_state(self, page, total):
        self.state = {
            "last_page": page,
            "total_listings": total,
            "last_run": datetime.now(timezone.utc).isoformat()
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def scrape(self, referer_base: str, city_id: str, tipo_operacao: str, start_page: int = 1):
        self.payload["city"] = city_id
        self.payload["tipoDeOperacion"] = "1" if tipo_operacao == "venda" else "2"
        self.payload["preTipoDeOperacion"] = self.payload["tipoDeOperacion"]

        page = start_page
        total_listings = 0

        while True:
            referer = f"{referer_base}-pagina-{page}.html"
            self.headers["Referer"] = referer
            print(f"Requesting page {page}...")

            try:
                response = self.session.post(
                    self.url,
                    params=self.params,
                    headers=self.headers,
                    json=self.payload,
                    timeout=30,
                )

                if response.status_code == 403:
                    print("Erro 403 (acesso negado). Tente atualizar os cookies.")
                    self.update_cookies_manualmente()
                    continue

                if response.status_code != 200:
                    print(f"Erro {response.status_code} ao requisitar a página {page}.")
                    break

                data = response.json()
                postings = data.get("listPostings", [])
                if not postings:
                    print(f"Nenhum anúncio encontrado na página {page}. Encerrando.")
                    break

                print(f"Página {page} OK - {len(postings)} anúncios.")
                self._save_listings(postings)
                total_listings += len(postings)
                self._save_state(page, total_listings)
                page += 1
                time.sleep(2)

            except Exception as e:
                print("Erro ao processar a página:", e)
                break

def extract_city_info_from_url(url: str) -> Dict[str, str]:
    match = re.search(r"imoveis-(aluguel|venda)-([\w\-]+)-sp", url)
    if not match:
        raise ValueError("URL inválida ou fora do padrão.")

    operacao, cidade_slug = match.groups()
    return {
        "operacao": operacao,
        "cidade_slug": cidade_slug,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL de busca do Imovelweb")
    parser.add_argument("--output", default="listings.json")
    parser.add_argument("--cookies", default=None, help="Cookies como string ou nome do arquivo JSON")
    args = parser.parse_args()

    city_info = extract_city_info_from_url(args.url)
    cidade_slug = city_info["cidade_slug"]
    operacao = city_info["operacao"]
    cidade_id = CITY_IDS.get(cidade_slug)

    if not cidade_id:
        raise ValueError(f"ID da cidade '{cidade_slug}' não encontrado. Adicione ao dicionário CITY_IDS.")

    scraper = ImovelWebScraper(output_file=args.output)

    if args.cookies:
        if os.path.isfile(args.cookies):
            scraper.cookies_file = args.cookies
            scraper._load_cookies()
        else:
            cookies_dict = {}
            for pair in args.cookies.split(";"):
                if "=" in pair:
                    name, value = pair.strip().split("=", 1)
                    cookies_dict[name] = value
            with open("cookies.json", "w", encoding="utf-8") as f:
                json.dump(cookies_dict, f, ensure_ascii=False, indent=2)
            scraper.cookies_file = "cookies.json"
            scraper._load_cookies()

    referer_base = args.url.rsplit("-pagina", 1)[0]
    start_page = scraper.state.get("last_page", 0) + 1

    scraper.scrape(
        referer_base=referer_base,
        city_id=cidade_id,
        tipo_operacao=operacao,
        start_page=start_page,
    )
    print("Scraping finalizado.")

if __name__ == "__main__":
    main()
