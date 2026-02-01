# Project5-6

## Project informatie

Een repository voor project 5/6: Lokaliseren van Drones.

Door Tom Heijmans, Fabio Wolthuis, Dennis Zejnilović, Ali Haimed.

## Scope

In de beginfase van het project lag de focus op het detecteren en lokaliseren van drones in de Coolhaven in Rotterdam voor de opdrachtgever Tidalis, het doel was om een systeem te ontwikkelen dat in een open buitenomgeving drones kan herkennen en volgen met behulp van camerabeelden en stereovisie geometrie. Echter is in het project verandering gekomen. Het doel werd om de technische haalbaarheid in te zien van het detecteren van objecten en lokaliseren van deze objecten op een optische manier. Dit systeem zal Tidalis dan toepassen in een ingang van de haven en zouden er schepen gemonitord worden, hierbij was de scope dus verandert naar: Het detecteren en lokaliseren van schepen. De nadruk ligt dus op de technische haalbaarheid van de kernfuncties maar zal uiteindelijk neergezet worden in de ingang van een haven. Door deze verandering van scope zullen er verslagen zijn in dit opleverset met een versie van de oude scope en een versie voor de nieuwe scope. Dit is te zien met de naam van het document met erachter het woord “drone”, voor documenten die tijdens de eerste scope gemaakt zijn, en “schip”, voor documenten die voor de nieuwe scope gemaakt zijn.


---

# Product Backlog

| Nr. | Status | Requirement | User Story | Taken | Acceptatieciteria | Story points |
| :-: | :----: | :---- | :---- | :---- | :---- | :----: |
| 1  | [ ] | **RQ01: Objectdetectie** | Als opdrachtgever wil ik dat de camera's een object (bewegend of niet) kan detecteren | <ul> <li> [ ] Een onderzoeksverslag voor welke camera’s we gaan gebruiken. </li><li> [ ] Een onderzoeksverslag voor welke microcontroller we gaan gebruiken. </li><li> [ ] Een onderzoeksverslag voor hoe het systeem geoptimalisserd kan worden. </li> <li> [ ] Onderzoek naar wat voor soort detectie het beste gebruikt kan worden. </li> <li> [ ] Implementeren van de detectiesysteem. </li> <li> [ ] Testen of het detectiesysteem correct werkt. </li></ul> | Een object wordt correct gedetecteerd. | **8** |
| 2 | [ ] | **RQ02: Gebruikersinterface** | Als opdrachtgever wil ik dat de uitvoer van het programma en het inlezen van de data makkelijk in te zien is, zodat ik een overzicht kan hebben van het gehele programma. | <ul> <li> [ ] Een onderzoeksverslag voor welke software we gaan gebruiken. </li> <li> [ ] Een GUI aanmaken.  </li> <li> [ ] Testen of data vanuit de microcontroller te zien is op de GUI </li></ul> | Een grafische gebruikersinterface met data is beschikbaar. | **8** |
| 3 | [ ] | **RQ03: Afstandsmeting** | Als gebruiker wil ik de afstand kunnen zien tussen de camera en een object, zodat ik kan weten hoe ver een object is van de camera. | <ul> <li> [ ] Onderzoek doen naar wat de meest precieze manier is van afstand bepalen met gebruik van camera's. </li><li> [ ] Het Implementeren van de afstandmethode. </li><li> [ ] Het testen van de afstandmethode. </li><li> [ ] Het weergeven van de afstand in de GUI </li></ul> | De afstand van de camera tot een object wordt correct weergegeven. | **8** |
| 4 | [ ] | **RQ04: Locatie-weergave in 2D** | Als gebruiker wil ik dat ik de locatie van een object in 2 dimensies kan zien, zodat ik de locatie van een object duidelijk kan zien. | <ul> <li> [ ] Een grafiek aanmaken van de locatie van een object in 2 dimensies, x en y. </li><li> [ ] Testen of de grafiek correct werkt. </li> <li> [ ] De grafiek implementeren in de GUI. </li> </ul> | Een 2D interface van de locatie van een object is beschikbaar. | **6** |
| 5 | [ ] | **RQ05: Live-camera overzicht** | Als gebruiker wil ik dat ik op een scherm in realtime kan zien waar een object zich bevindt in het opgenomen beeld, zodat ik een duidelijk overzicht kan hebben van wat het programma doet. | <ul> <li> [ ] In de GUI wordt een live beeld weergeven van de feed van 1 camera. </li>  <li> [ ] De detectiekader over de objecten toevoegen aan de live feeds. </li><li> [ ] Testen of de detectie correct werkt in de GUI. </li> </ul> | Camera-overzicht met detectie is beschikbaar. | **6** |
| 6 | [ ] | **RQ06: Robuuste behuizing** | Als opdrachtgever wil ik dat het eindproduct een robuuste behuizing heeft, zodat de microcontrollers en camera's goed beschermd zijn. | <ul> <li> [ ] Mechatronisch ontwerp. </li> <li> [ ] Onderdelen worden 3D geprint. </li><li> [ ] Testen of de behuizing robuust genoeg is. </li> </ul> | Er is een behuizing op correcte afmetingen. | **8** |
| 7 | [ ] | **RQ07: Ontwerp functionaliteit** | Als opdrachtgever wil ik dat kan inzien wat het ontwerp is van de functionaliteit van het gehele programma is, zodat ik een duidelijk beeld heb over wat het structuur is van de programma doet. | <ul> <li> [ ] Architectuurontwerp maken. </li><li> [ ] Flowchart maken. </li> <li> [ ] UML van de main code maken. </li><li> [ ] Elektrisch schema maken. </li> </ul> | Structuur van het programma is duidelijk. | **2** |
| 8 | [ ] | **RQ08: Locatie-weergave in 3D** | Als opdrachtgever wil ik dat ik de locatie van een object in 3 dimensies kan zien, zodat ik kan weten wat de exacte locatie is van een object. | <ul> <li> [ ] Een grafiek aanmaken van de locatie van een object in 3 dimensies, x/y/z. </li><li> [ ] Testen of de grafiek correct werkt. </li> <li> [ ] Het grafiek implementeren in de GUI. </li> </ul> | Een 3D interface van de locatie van een object. | **2** |
| 9 | [ ] | **RQ09: 24/7 zicht** | Als opdrachtgever wil ik dat de camera’s 24/7 werken, zodat ik drones in de dag en in de nacht gedetecteerd kunnen worden. | <ul> <li> [ ] Onderzoek hoe je nachtzicht kan toevoegen </li> <li> [ ] Integratie van nachtzicht camera’s. </li><li> [ ] Camera's testen. </li> </ul> | Een 24/7 feed van een object. | **2** |
| 10 | [ ] | **RQ10: Akoestische waarneming** | Als opdrachtgever wil ik dat ik naast het gebruiken van camera’s, ook gebruik kan maken van microfoons om een object kan detecteren, zodat ik op meerdere manieren een object kan detecteren. | <ul> <li> [ ] Onderzoeken van al gegeven werk van de opdrachtgever. </li> <li> [ ] Implementatie van software (microfoon) in het systeem. </li> <li> [ ] Implementatie van hardware (microfoon) in het systeem. </li><li> [ ] Microfoons testen. </li></ul> | Akoestische waarneming is beschikbaar. | **4** |

## Sprint planning 1
---

**Startdatum:** 16-09-2025  
**Einddatum:** 30-09-2025  
**Doel:** Onderzoekingen uitvoeren voor elke component in het project en uitwerken hoe het programma eruit gaat zien.

| Status | Prioriteit |  Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :----: |
| Klaar | Hoog | Camera onderzoeksverslag  | Dennis | 1 |
| Klaar | Hoog | Microcontroller onderzoeksverslag | Tom | 1 |
| Klaar | Hoog | Software onderzoeksverslag | Ali | 2 |
| Klaar | Hoog | Onderzoek motion-detectie | Fabio | 1 |

## Sprint planning 2
---

**Startdatum:** 30-09-2025  
**Einddatum:** 14-10-2025  
**Doel:** Onderdelen aanschaffen en het uit testen daarvan.

| Status | Prioriteit |  Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :----: |
| Klaar | Hoog |  Probleemomschrijving maken  | Tom | - |
| Klaar | Midden |  Budget bepalen/pitchen  | Dennis, Ali | - |
| Klaar | Hoog |  Testen van onderdelen | Tom, Fabio | 5 |
| Klaar | Hoog |  Raspberry Pi OS configureren | Fabio | 5 |
| Klaar | Hoog |  Onderdelen voor rondom de Raspberry Pi en camera's printen | Fabio | 6 |
| Klaar | Hoog |  Begin requirementsanalyse | Dennis | - |
| Klaar | Hoog |  Mechatronisch ontwerp, Architectuur ontwerp, flow chart | Ali, Tom | 6, 7 |



## Sprint planning 3
---

**Startdatum:** 14-10-2025  
**Einddatum:** 14-11-2025  
**Doel:** Ontwerpfase afronden en het implementeren de detectie functinaliteit.

| Status | Prioriteit |  Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :----: |
| Klaar | Midden |  Requirements analyse afronden | Dennis | - |
| Klaar | Hoog |  Detectie-model (YOLO) toevoegen aan camera-feed en optimaliseren  | Dennis, Fabio | 1, 3 |
| Bezig | Hoog |  Afstandsmethode onderzoeken, implementeren en testen | Fabio, Tom  | 3 |
| Bezig | Hoog |  Onderzoeken en beginnen met een punt te krijgen van de camera beelden in een 2D grafiek | Ali | 4 |
| Klaar | Midden |  UML maken van de main code | Ali | 4 |
| Klaar | Hoog |  Begin Test-rapport | Tom | - |



## Sprint planning 4
---

**Startdatum:** 18-11-2025  
**Einddatum:** 02-12-2025  
**Doel:** Functionaliteit compleet maken en meer documentatie af hebben.

| Status | Prioriteit |  Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :----: |
| [ ] | Hoog | Raspberry Pi AI HAT+ toevoegen voor optimalisatie | Fabio | 1 |
| [ ] | Hoog | Verder kalibreren, implementeren en testen van de afstandsmethode | Dennis, Tom | 3 |
| [ ] | Hoog |  Punt van een object inzien in een 2D grafiek | Ali, Fabio | 4 |
| [ ] | Midden |  Literatuuronderzoek maken | Dennis | - |
| [ ] | Midden |  Gebruikersonderzoek maken | Tom | - |
| [ ] | Hoog |  Verder Test-rapport | Tom | - |
| [ ] | Hoog |  Elektrisch schema maken | Ali | 7 |


## Sprint planning 5
---

**Startdatum:** 2-12-2025  
**Einddatum:** 16-12-2025  
**Doel:** Verder met functionaliteit compleet maken en meer documentatie af hebben.

| Status | Prioriteit |  Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :----: |
| [ ] | Hoog | Raspberry Pi AI HAT+ toevoegen voor optimalisatie | Fabio, Tom | 1 |
| [ ] | Hoog | Verder kalibreren, implementeren en testen van de afstandsmethode | Dennis, Tom | 3 |
| [ ] | Hoog |  Punt van een object inzien in een 2D grafiek | Ali, Fabio | 4 |
| [ ] | Midden |  stereo-visie onderzoeksverslag | Dennis | 3 |
| [ ] | Midden |  optimalisatie onderzoeksverslag | Ali | 1 |
| [ ] | Midden |  Literatuuronderzoek toevoegen aan onderzoeksverslagen | Dennis | 1,3 |
| [ ] | Hoog |  Detectie en afstands testen toevoegen aan het test-rapport| Tom | 1,2 |


## Sprint planning 6
---

**Startdatum:** 16-12-2025  
**Einddatum:** 13-1-2026  
**Doel:** Veel aandacht geven aan het correct kunnen te bepalen van de afstand.

| Status | Prioriteit |  Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :----: |
| [ ] | Laag | Raspberry Pi AI HAT+ toevoegen voor optimalisatie | Dennis, Tom | 1 |
| [ ] | Hoog |  kalibreren, implementeren en testen van de afstandsmethode | Dennis, Tom | 3 |
| [ ] | Hoog |  Verder punt van een object inzien in een 2D grafiek | Ali, Fabio | 4 |
| [ ] | Midden |  optimalisatie onderzoeksverslag | Ali | 1 |
| [ ] | Midden |  Camera houder opnieuw ontwerpen| Fabio | 2 |


## Sprint planning 7
---

**Startdatum:** 13-1-2025  
**Einddatum:** 27-1-2026  
**Doel:** Functionaliteit afmaken en documentatie afronden.

| Status | Prioriteit |  Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :----: |
| [ ] | Laag | Raspberry Pi AI HAT+ toevoegen voor optimalisatie | Fabio, Dennis | 1 |
| [ ] | Hoog |  kalibreren, implementeren en testen van de afstandsmethode | Fabio, Tom | 3 |
| [ ] | Hoog |  Verder punt van een object inzien in een 2D grafiek | Ali, Tom, Fabio | 4 |
| [ ] | Midden | Aanpassingen/ toevoegingen documentatie na mate scope | Dennis, Ali | 1,2 |

### Changelog

| Versie | Wat | Datum |
| :----: | :---- | :----: |
| 1.0 | Product Backlog aangemaakt | 16-09-2025 |
| 1.1 | Product Backlog uitgebreid | 19-09-2025 |
| 1.2 | Product Backlog in Github toegevoegd in markdown | 19-09-2025 |
| 1.3 | Sprint planning 1 aangemaakt | 21-09-2025 |
| 2.0 | Sprint planning 2 aangemaakt | 30-09-2025 |
| 3.0 | Sprint planning 3 aangemaakt | 13-10-2025 |
| 4.0 | Sprint planning 4 aangemaakt  | 18-11-2025 |
| 5.0 | Sprint planning 5 aangemaakt  | 2-12-2025 |
| 6.0 | Sprint planning 6 aangemaakt  | 16-12-2025 |
| 6.0 | Sprint planning 7 aangemaakt  | 13-1-2026 |