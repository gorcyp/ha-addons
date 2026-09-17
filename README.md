# Dodatki gorcyp

## Zasoby HA

Prosty panel RAM i CPU aplikacji oraz systemowej pamięci wymiany (swap), dopasowany do ciemnego motywu Home Assistant.

[Dodaj repozytorium do Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fgorcyp%2Fha-addons)

Po dodaniu repozytorium wybierz Zasoby HA w sklepie aplikacji, zainstaluj i uruchom. Przeznaczone dla Home Assistant OS; sam Home Assistant Container nie obsługuje sklepu aplikacji.

- [Instrukcja i opis pomiarów](ha-resource-monitor/DOCS.md)
- [Historia zmian](ha-resource-monitor/CHANGELOG.md)
- [Zgłoś problem](https://github.com/gorcyp/ha-addons/issues)

## Rozwój

Testy: `python3 -m unittest discover -s ha-resource-monitor -p 'test_*.py'`

Przed wydaniem sprawdź kod JavaScript, testy, budowanie obrazu i działanie w HAOS. Zwiększ wersję w config.yaml i opisz zmiany w CHANGELOG.md. Test jednostkowy nie zastępuje próby na rzeczywistym urządzeniu.
