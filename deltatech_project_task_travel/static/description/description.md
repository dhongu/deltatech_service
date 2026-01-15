### Project Task Travel Management

Acest modul extinde funcționalitatea task-urilor din proiecte pentru a permite monitorizarea și facturarea deplasărilor efectuate de tehnicieni.

#### Caracteristici principale:

*   **Monitorizarea Automată a Deplasării:** Atunci când se folosește cronometrul task-ului, sistemul capturează automat coordonatele GPS și calculează distanța și durata deplasării.
*   **Control Manual:** Butoane dedicate pentru "Start Travel" și "Stop Travel" permit înregistrarea deplasării independent de timpul lucrat propriu-zis.
*   **Integrare Google Maps:** Calcularea distanței se face folosind Google Maps Distance Matrix API pentru precizie maximă (pe drum), cu fallback la formula Haversine (în linie dreaptă).
*   **Sincronizare cu Comanda de Vânzare:** Distanța și timpul de deplasare sunt adăugate automat ca linii în Comanda de Vânzare (Sale Order) asociată task-ului, facilitând facturarea rapidă către client.
*   **Configurare Flexibilă:** Produsele folosite pentru facturarea distanței și a timpului pot fi configurate în setările proiectului.
*   **Vizualizare Detaliată:** Un tab dedicat în formularul de task afișează toate informațiile relevante despre deplasare, inclusiv coordonatele de start și de stop.

#### Configurare:

1. Mergeți la **Project -> Configuration -> Settings**.
2. Configurați produsele pentru **Travel Distance Product** și **Travel Time Product**.
3. Asigurați-vă că aveți o cheie Google API validă în sistem pentru calculul distanței prin Google Maps.
