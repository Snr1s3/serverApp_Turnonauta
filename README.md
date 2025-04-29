# SERVER APP TURNONAUTA

> **Altres Repositoris del Projecte**
>- [API](https://github.com/Snr1s3/TurnoNauta_FastAPI.git)
>- [MOBIL](https://github.com/Snr1s3/Turnonauta.git)
>- [WEB](https://github.com/EdwindanielTIC/web_TurnoNauta.git)


Estructura de Directoris:     
└── snr1s3-serverapp_turnonauta/           
    ├── README.md     
    ├── requirements.txt        
    └── src/      
        ├── api_connections.py      
        ├── client.py      
        ├── server.py        
        └── models/       
            ├── Jugador.py     
            └── Torneig.py  


## requeriments.txt

### Llista de Dependències
- **`aiohappyeyeballs==2.6.1`**: Millora la resolució DNS i la fiabilitat de les connexions en aplicacions asíncrones.
- **`aiohttp==3.11.16`**: Un potent framework HTTP asíncron per gestionar peticions i respostes HTTP.
- **`aiosignal==1.3.2`**: Gestiona senyals asíncrones, utilitzat internament per `aiohttp`.
- **`asyncio==3.4.3`**: Una llibreria per escriure codi asíncron utilitzant la sintaxi `async` i `await` de Python.
- **`attrs==25.3.0`**: Simplifica la creació de classes amb menys codi redundant.
- **`frozenlist==1.5.0`**: Proporciona llistes immutables, utilitzades internament per `aiohttp`.
- **`idna==3.10`**: Gestiona noms de domini internacionalitzats (IDN), utilitzat per al parsing d'URLs.
- **`multidict==6.4.2`**: Implementa estructures de multidict, utilitzades per `aiohttp` per gestionar capçaleres HTTP i paràmetres de consulta.
- **`propcache==0.3.1`**: Una llibreria per a la memòria cau de propietats en objectes Python.
- **`yarl==1.19.0`**: Una llibreria per al parsing i la manipulació d'URLs, utilitzada internament per `aiohttp`.

```bash
# instal·lar requeriments.txt
pip install -r requirements.txt
```