# Zasoby HA — 1.1.0

Panel RAM i CPU dla Home Assistant Core, Supervisora i uruchomionych aplikacji.
Ciemne, płaskie karty nawiązują do standardowego motywu HA. Bez zewnętrznych fontów, bibliotek i historii pomiarów.

## Aktualizacja

1. Wgraj ha-resource-monitor.zip do /config przez Studio Code Server.
2. Użyj terminala **wewnątrz Studio Code Server**, nie Terminal & SSH.
3. Sprawdź: `mount | grep ' on /addons '`. Jeśli brak wyniku, zatrzymaj się.
4. Zachowaj ewentualne własne zmiany poza /addons, następnie wykonaj:
   `unzip -o /config/ha-resource-monitor.zip -d /addons`
5. Sklep aplikacji → Sprawdź aktualizacje → HA Resource Monitor → Aktualizuj do 1.1.0.
6. Po aktualizacji nazwa aplikacji to Zasoby HA. Otwórz ponownie panel.

Rozpakowanie nadpisuje źródła tej aplikacji. Nie wymaga odinstalowania, wyłączania ochrony ani restartu całego HA.

## Pomiar

Suma RAM obejmuje tylko pozycje tabeli, nie całe urządzenie. Integracje w Core nie są mierzone osobno. RAM % jest wskazaniem API względem limitu kontenera. CPU nie przedstawia obciążenia całego hosta. Liczniki sieci nie są prędkością transferu.
Brak odczytu aplikacji lub Supervisora sygnalizowany jest komunikatem. Po błędzie poprzedni pomiar jest oznaczony jako nieaktualny.

## Uprawnienia

Rola Supervisor API manager jest szersza niż odczyt statystyk; kod wykonuje tylko żądania GET. Token pozostaje w backendzie. Interfejs działa przez Ingress, bez portu wystawionego w LAN.
Odstęp odświeżania wybiera się w panelu.
