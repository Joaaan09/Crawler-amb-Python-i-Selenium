# WebCrawler per detectar errors 4XX

Aquest és un crawler web dissenyat per rastrejar llocs web i identificar errors 4XX (com ara 404 Not Found, 403 Forbidden, etc.). L'eina és útil per a administradors web que necessiten identificar enllaços trencats o recursos inaccessibles en els seus llocs web.

## Característiques principals

- Rastreig automàtic de pàgines web dins del mateix domini
- Detecció d'errors 4XX (404, 403, 401, etc.)
- Registre dels referrers (pàgines d'origen) que contenen enllaços als recursos amb errors
- Exportació dels resultats a un fitxer CSV
- Límit configurable de URLs a processar
- Informe de resum dels errors trobats

## Requisits

- Python 3.6 o superior
- Navegador Chrome instal·lat
- Llibreries Python necessàries (vegeu `requirements.txt`)

## Instal·lació

1. Clona aquest repositori:
   ```
   git clone https://github.com/teu-usuari/web-crawler-4xx.git
   cd web-crawler-4xx
   ```

2. Instal·la les dependències:
   ```
   pip install -r requirements.txt
   ```

## Ús

Executa el crawler amb una URL base:

```
python crawler.py https://www.exemple.com
```

### Opcions disponibles

- `-o, --output`: Especifica el nom del fitxer de sortida (per defecte: errors_4xx.csv)
- `-l, --limit`: Estableix un límit màxim d'URLs a processar

Exemples:

```
# Exemple amb fitxer de sortida personalitzat
python crawler.py https://www.exemple.com -o resultats.csv

# Exemple amb límit d'URLs
python crawler.py https://www.exemple.com -l 100
```

## Com funciona

1. El crawler comença des de la URL base proporcionada
2. Utilitza Selenium per carregar cada pàgina i extreure tots els enllaços
3. Comprova el codi d'estat HTTP de cada enllaç
4. Registra els errors 4XX trobats juntament amb les seves URLs referents
5. Genera un informe amb un resum dels errors trobats

## Estructura de fitxers de sortida

El fitxer CSV generat conté les següents columnes:
- `url`: La URL que presenta l'error
- `status_code`: El codi d'estat HTTP (p.ex. 404, 403, etc.)
- `referrer`: La URL de la pàgina que conté l'enllaç a la URL amb error

## Contribucions

Les contribucions són benvingudes! Si voleu millorar aquesta eina, no dubteu a fer un fork del repositori i enviar una pull request.

## Llicència

Aquest projecte està llicenciat sota la llicència MIT. Consulteu el fitxer `LICENSE` per a més detalls.
