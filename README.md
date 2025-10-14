# Project5-6

## Project informatie

Een repository voor project 5/6: Lokaliseren van Drones.

Door Tom Heijmans, Fabio Wolthuis, Dennis Zejnilović, Ali Haimed.

---

# Product Backlog

| Nr. | Status | Requirement | Userstory | Taken | Acceptatieciteria | Story points |
| :-: | :----: | :---- | :---- | :---- | :---- | :----: |
| 1  | [ ] | **RQ01** | Als opdrachtgever wil ik dat ik op een scherm in realtime kan zien waar een object zich bevindt in het opgenomen beeld, zodat ik een duidelijk overzicht kan hebben van wat het programma doet. | <ul> <li> [ ] In de GUI een 2D grafiek maken waarin de positie van de drone exact wordt weergegeven. </li> <li> [ ] In de GUI de live beelden laten zien van de camera's </li> </ul> | Camera-overzicht beschikbaar. | **8** |
| 2 | [ ] | **RQ02** | Als opdrachtgever wil ik dat de uitvoer van het programma en het inlezen van data makkelijk kan zien, zodat ik een overzicht kan hebben van het programma | <ul> <li> [ ] Een onderzoeksverslag voor welke software we gaan gebruiken voor de interface. </li> <li> [ ] Een GUI aanmaken.  </li> </ul> | Een grafische gebruikersinterface is beschikbaar | **8** |
| 3 | [ ] | **RQ03** | Als opdrachtgever wil ik dat ik de locatie van de drone in 3 dimensies kan zien, zodat ik kan weten wat de exacte locatie is van de drone. | <ul> <li> [ ] De grafiek van de locatie van de drone in 3 dimensies maken, x/y/z </li> </ul> | Een 3D interface van de locatie van de drone | **2** |
| 4 | [ ] | **RQ04** | Als opdrachtgever wil ik dat de camera’s 24/7 werken, zodat ik drones in de dag en in de nacht gedetecteerd kunnen worden | <ul> <li> [ ] Onderzoek hoe je nachtzicht kan toevoegen </li> <li> [ ] Integratie van nachtzicht camera’s </li> </ul> | Een 24/7 feed van de drones | **4** |
| 5 | [ ] | **RQ05** | Als gebruiker wil ik de afstand kunnen zien tussen de camera en de drone, zodat ik kan weten hoe ver de drone is van de camera. | <ul> <li> [ ] Onderzoek doen naar wat de meest efficiënte manier is van afstand detecteren </li> <li> [ ] Het Implementeren van de afstandmethode. </li> <li> [ ] Het weergeven van de afstand in de GUI </li> </ul> | De afstand van de camera tot de drone wordt correct weergegeven. | **6** |
| 6 | [ ] | **RQ06** | Als opdrachtgever wil ik dat de camera's een object (bewegend of niet) kan detecteren | <ul> <li> [ ] Onderzoek voor welke camera’s we gaan gebruiken. </li> <li> [ ] Onderzoek naar wat voor soort detectie het beste gebruikt kan worden </li> </ul> | Een object kunnen detecteren. | **8** |
| 7 | [ ] | **RQ07** | Als opdrachtgever wil ik dat ik naast het gebruiken van camera’s, ook gebruik kan maken van microfoons om een object kan detecteren, zodat ik op meerdere manieren de drone kan detecteren. | <ul> <li> [ ] Onderzoeken van al gegeven werk van de opdrachtgever </li> <li> [ ] Implementatie van software (microfoon) in het systeem </li> <li> [ ] Implementatie van hardware (microfoon) in het systeem </li> </ul> | Akoestische waarneming is beschikbaar | **2** |
| 8 | [ ] | **RQ08** | Als opdrachtgever wil ik dat het eindproduct een robuuste behuizing heeft, zodat de microcontrollers en camera's goed beschermd zijn | <ul> <li> [ ] Mechatronisch ontwerp maken </li> <li> [ ] Behuizing Maken </li> </ul> | Er is een behuizing | **6** |

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

