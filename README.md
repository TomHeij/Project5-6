# Project5-6

## Project informatie

Een repository voor project 5/6: Lokaliseren van Drones.

Door Tom Heijmans, Fabio Wolthuis, Dennis Zejnilović, Ali Haimed.

---

# Product Backlog

| Nr. | Status | Requirement | User Story | Taken | Acceptatieciteria | Story points |
| :-: | :----: | :---- | :---- | :---- | :---- | :----: |
| 1  | [ ] | **RQ01: Objectdetectie** | Als opdrachtgever wil ik dat de camera's een object (bewegend of niet) kan detecteren | <ul> <li> [ ] Een onderzoeksverslag voor welke camera’s we gaan gebruiken. </li> <li> [ ] Onderzoek naar wat voor soort detectie het beste gebruikt kan worden. </li> <li> [ ] Implementeren van de detectiesysteem. </li> </ul> | Een object wordt correct gedetecteerd. | **8** |
| 2 | [ ] | **RQ02: Gebruikersinterface** | Als opdrachtgever wil ik dat de uitvoer van het programma en het inlezen van de data makkelijk in te zien is, zodat ik een overzicht kan hebben van het gehele programma. | <ul> <li> [ ] Een onderzoeksverslag voor welke software we gaan gebruiken. </li> <li> [ ] Een GUI aanmaken.  </li> </ul> | Een grafische gebruikersinterface is beschikbaar. | **8** |
| 3 | [ ] | **RQ03: Afstandsmeting** | Als gebruiker wil ik de afstand kunnen zien tussen de camera en de drone, zodat ik kan weten hoe ver de drone is van de camera. | <ul> <li> [ ] Onderzoek doen naar wat de meest precieze manier is van afstand bepalen met gebruik van camera's. </li><li> [ ] Het Implementeren van de afstandmethode. </li><li> [ ] Het weergeven van de afstand in de GUI </li></ul> | De afstand van de camera tot de drone wordt correct weergegeven. | **8** |
| 4 | [ ] | **RQ04: Locatie-weergave in 2D** | Als gebruiker wil ik dat ik de locatie van de drone in 2 dimensies kan zien, zodat ik de locatie van de drone duidelijk kan zien. | <ul> <li> [ ] Een grafiek aanmaken van de locatie van de drone in 2 dimensies, x en y. </li> <li> [ ] De grafiek implementeren in de GUI. </li> </ul> | Een 2D interface van de locatie van de drone is beschikbaar. | **6** |
| 5 | [ ] | **RQ05: Live-camera overzicht** | Als gebruiker wil ik dat ik op een scherm in realtime kan zien waar een object zich bevindt in het opgenomen beeld, zodat ik een duidelijk overzicht kan hebben van wat het programma doet. | <ul> <li> [ ] In de GUI wordt een live beeld weergeven van de feed van 1 camera. </li>  <li> [ ] De detectiekader over de objecten toevoegen aan de live feeds. </li> </ul> | Camera-overzicht met detectie is beschikbaar. | **6** |
| 6 | [ ] | **RQ06: Robuuste behuizing** | Als opdrachtgever wil ik dat het eindproduct een robuuste behuizing heeft, zodat de microcontrollers en camera's goed beschermd zijn. | <ul> <li> [ ] Mechatronisch ontwerp. </li> <li> [ ] Onderdelen worden 3D geprint. </li><li> [ ] Elektrisch schema. </li> </ul> | Er is een behuizing op correcte afmetingen. | **8** |
| 7 | [ ] | **RQ07: Locatie-weergave in 3D** | Als opdrachtgever wil ik dat ik de locatie van de drone in 3 dimensies kan zien, zodat ik kan weten wat de exacte locatie is van de drone. | <ul> <li> [ ] Een grafiek aanmaken van de locatie van de drone in 3 dimensies, x/y/z. </li> <li> [ ] Het grafiek implementeren in de GUI. </li> </ul> | AEen 3D interface van de locatie van de drone. | **2** |
| 8 | [ ] | **RQ08: 24/7 zicht** | Als opdrachtgever wil ik dat de camera’s 24/7 werken, zodat ik drones in de dag en in de nacht gedetecteerd kunnen worden. | <ul> <li> [ ] Onderzoek hoe je nachtzicht kan toevoegen </li> <li> [ ] Integratie van nachtzicht camera’s. </li> </ul> | Een 24/7 feed van de drones. | **2** |
| 9 | [ ] | **RQ09: Akoestische waarneming** | Als opdrachtgever wil ik dat ik naast het gebruiken van camera’s, ook gebruik kan maken van microfoons om een object kan detecteren, zodat ik op meerdere manieren de drone kan detecteren. | <ul> <li> [ ] Onderzoeken van al gegeven werk van de opdrachtgever. </li> <li> [ ] Implementatie van software (microfoon) in het systeem. </li> <li> [ ] Implementatie van hardware (microfoon) in het systeem. </li></ul> | Akoestische waarneming is beschikbaar. | **4** |

## Sprint planning 1
---

**Startdatum:** 16-09-2025  
**Einddatum:** 30-09-2025  
**Doel:** Onderzoekingen uitvoeren voor elke component in het project en uitwerken hoe het programma eruit gaat zien.

| Status | Prioriteit | Benodigde tijd (uren) | Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :---- | :----: |
| Klaar | Hoog | 2 | Camera onderzoeksverslag.  | Dennis | 6 |
| Klaar | Hoog | 2 | (Micro-)controller onderzoek. | Tom | - |
| Klaar | Hoog | 2 | Software onderzoek. | Ali | 2 |
| Klaar | Hoog | 8 | Onderzoek motion-detectie | Fabio | 6 |

## Sprint planning 2
---

**Startdatum:** 30-09-2025  
**Einddatum:** 14-10-2025  
**Doel:** Onderdelen aanschaffen en het uit testen daarvan.

| Status | Prioriteit | Benodigde tijd (uren) | Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :---- | :----: |
| [ ] | Hoog | 3 | Budget bepalen/pitchen  | Dennis, Ali | - |
| [ ] | Hoog | 12 | Testen van onderdelen | Tom, Fabio | 5 |
| [ ] | Hoog | 6 | Mechatronisch ontwerp, Architectuur ontwerp, flow chart |  | - |



## Sprint planning 3
---

**Startdatum:** 14-10-2025  
**Einddatum:** 18-11-2025  
**Doel:** Ontwerpfase afronden en het implementeren de detectie functinaliteit.

| Status | Prioriteit | Benodigde tijd (uren) | Taken | Wie? | User story |
| :----: | :---- | :---- | :---- | :---- | :----: |
| [ ] | leeg | 3 | literatuur onderzoek | Dennis, Ali | - |
| [ ] | Hoog | 8 | Mechatronisch ontwerp uitbreiden | Fabio | 3 |
| [ ] | Hoog | 5 | Eerste versie van de GUI maken |alle  | 3 |
| [ ] | Hoog | 6 | Detectie functionaliteit implementeren | Fabio, Tom | 8 |


### Changelog

| Versie | Wat/Wie | Datum |
| :----: | :---- | :----: |
| 1.0 | Product Backlog aangemaakt – Dennis | 16-09-2025 |
| 1.1 | Product Backlog uitgebreid – Allen | 19-09-2025 |
| 1.2 | Product Backlog in Github toegevoegd in markdown – Fabio | 19-09-2025 |
| 1.3 | Sprint planning 1 aangemaakt – Dennis | 21-09-2025 |
| 2.0 | Sprint planning 2 aangemaakt – Dennis | 30-09-2025 |
| 2.1 | Product backlog sprint planning 2 aangepast – Dennis | 3-10-2025 |

