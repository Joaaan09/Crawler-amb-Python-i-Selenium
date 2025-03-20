import csv
import time
import argparse
import requests
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from requests.exceptions import RequestException

class WebCrawler:
    def __init__(self, base_url, output_file="errors_4xx.csv"):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.queue = [base_url]
        self.errors_4xx = []
        self.output_file = output_file
        self.referrer_map = {}  # Mapeja URL -> referrer
        
        # Configuració del navegador
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Configurar un temps d'espera raonable
        self.driver.set_page_load_timeout(15)
        
        # Configuració de les capçaleres HTTP per a requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        # Sessió de requests per mantenir cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def is_same_domain(self, url):
        """Comprova si la URL pertany al mateix domini."""
        if not url:
            return False
        try:
            return urlparse(url).netloc == self.domain
        except:
            return False
    
    def normalize_url(self, url):
        """Normalitza la URL per evitar duplicats."""
        url = url.strip()
        # Elimina el fragment (#) de la URL
        if '#' in url:
            url = url.split('#')[0]
        # Elimina els paràmetres trailing slash si és necessari
        if url.endswith('/'):
            url = url[:-1]
        return url
    
    def extract_links(self):
        """Extreu tots els enllaços de la pàgina actual."""
        links = []
        try:
            # Obté enllaços des de les etiquetes <a>
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            for element in elements:
                href = element.get_attribute("href")
                if href and href.startswith("http") and self.is_same_domain(href):
                    links.append(self.normalize_url(href))
            
            # També obtenim enllaços des d'altres elements comuns
            for tag in ['img', 'script', 'link', 'iframe']:
                elements = self.driver.find_elements(By.TAG_NAME, tag)
                for element in elements:
                    src = element.get_attribute('src') or element.get_attribute('href')
                    if src and src.startswith("http") and self.is_same_domain(src):
                        links.append(self.normalize_url(src))
        except Exception as e:
            print(f"Error al extreure enllaços: {e}")
        
        return list(set(links))  # Elimina duplicats
    
    def check_status_code(self, url):
        """Comprova el codi d'estat HTTP de la URL utilitzant requests."""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10)
            return response.status_code
        except RequestException:
            # Si hi ha un error amb HEAD, intentem amb GET
            try:
                response = self.session.get(url, timeout=10)
                return response.status_code
            except RequestException as e:
                print(f"Error al comprovar {url}: {e}")
                # Intentem determinar si és un error 4XX o 5XX
                error_msg = str(e).lower()
                if "404" in error_msg:
                    return 404
                elif "403" in error_msg:
                    return 403
                elif "401" in error_msg:
                    return 401
                else:
                    return 500
    
    def crawl(self):
        """Inici del procés de crawling."""
        try:
            processed_count = 0
            self.referrer_map[self.base_url] = "Pàgina inicial"
            
            while self.queue:
                current_url = self.queue.pop(0)
                if current_url in self.visited_urls:
                    continue
                
                processed_count += 1
                print(f"[{processed_count}] Explorant: {current_url}")
                self.visited_urls.add(current_url)
                
                # Comprovar el codi d'estat
                status_code = self.check_status_code(current_url)
                
                # Si és un error 4XX, el registrem
                if 400 <= status_code < 500:
                    referrer = self.referrer_map.get(current_url, "Desconegut")
                    self.errors_4xx.append({
                        "url": current_url,
                        "status_code": status_code,
                        "referrer": referrer
                    })
                    print(f"Error {status_code} trobat: {current_url}")
                
                # Si no és un error 4XX o 5XX, carreguem la pàgina amb Selenium per extreure enllaços
                if status_code < 400:
                    try:
                        self.driver.get(current_url)
                        links = self.extract_links()
                        
                        for link in links:
                            if link not in self.visited_urls and link not in self.queue:
                                self.queue.append(link)
                                # Registrem el referrer
                                self.referrer_map[link] = current_url
                    except (TimeoutException, WebDriverException) as e:
                        print(f"Error al navegar a {current_url}: {e}")
                
                # Pausa breu per evitar sobrecarregar el servidor
                time.sleep(1)
                
                # Desarem els errors cada 10 URLs visitades
                if processed_count % 10 == 0:
                    self.save_errors()
                    print(f"Progrés: {processed_count} URLs processades, {len(self.queue)} pendents, {len(self.errors_4xx)} errors trobats")
                    
        except KeyboardInterrupt:
            print("Procés interromput per l'usuari.")
        finally:
            self.driver.quit()
            self.save_errors()
            self.generate_report()
    
    def save_errors(self):
        """Desa els errors trobats en un fitxer CSV."""
        with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'status_code', 'referrer']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for error in self.errors_4xx:
                writer.writerow(error)
                
        print(f"Informe d'errors desat a {self.output_file}")
        
    def generate_report(self):
        """Mostra un resum dels errors trobats."""
        if not self.errors_4xx:
            print("No s'han trobat errors 4XX.")
            return
        
        print("\n===== RESUM D'ERRORS 4XX =====")
        print(f"Total d'errors trobats: {len(self.errors_4xx)}")
        
        # Agrupem els errors per codi
        errors_by_code = {}
        for error in self.errors_4xx:
            code = error['status_code']
            if code not in errors_by_code:
                errors_by_code[code] = 0
            errors_by_code[code] += 1
        
        # Mostrem el resum per codi
        for code, count in sorted(errors_by_code.items()):
            print(f"Errors {code}: {count}")
        
        print(f"\nLes URLs amb errors s'han desat a: {self.output_file}")
        print("URLs amb errors:")
        for i, error in enumerate(self.errors_4xx[:min(10, len(self.errors_4xx))], 1):
            print(f"{i}. {error['url']} - {error['status_code']}")
        
        if len(self.errors_4xx) > 10:
            print(f"... i {len(self.errors_4xx) - 10} més")

def main():
    parser = argparse.ArgumentParser(description="Crawler per detectar errors 4XX en un domini")
    parser.add_argument("url", help="URL base per iniciar el crawling")
    parser.add_argument("-o", "--output", default="errors_4xx.csv", help="Fitxer de sortida (CSV)")
    parser.add_argument("-d", "--depth", type=int, default=None, help="Profunditat màxima d'exploració (opcional)")
    args = parser.parse_args()
    
    crawler = WebCrawler(args.url, args.output)
    print(f"Iniciant crawling de {args.url}")
    crawler.crawl()

if __name__ == "__main__":
    main()