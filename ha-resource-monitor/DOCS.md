# Zasoby HA

## Instalacja i aktualizacje

Dodaj https://github.com/gorcyp/ha-addons do repozytoriów sklepu aplikacji Home Assistant OS. Zainstaluj Zasoby HA, uruchom aplikację i włącz pokazywanie na pasku bocznym. Nie potrzeba tokenu użytkownika, otwierania portów ani wyłączania ochrony.

Nowe wersje instaluj przyciskiem Aktualizuj. Nie odinstalowuj aplikacji przed aktualizacją. Historia zmian jest dostępna w CHANGELOG.md.

## RAM, CPU i sieć

RAM w podsumowaniu jest sumą widocznych komponentów, nie użyciem całego hosta. Integracje w Core nie są mierzone osobno. RAM % pochodzi z Supervisor API i odnosi się do limitu kontenera. CPU jest sumą wskazań komponentów; nie jest pomiarem całego hosta. Liczniki sieci to ilości danych, nie szybkość transmisji.

## Pamięć wymiany (swap)

Źródło to SwapTotal i SwapFree z /proc/meminfo. Użycie = SwapTotal − SwapFree; jednostki kB jądra przeliczane są jako 1024 bajty. Na HAOS liczniki dotyczą jądra hosta, nie pojedynczego kontenera. Przy niestandardowej wirtualizacji /proc może być wirtualizowany — wynik dotyczy wtedy widoku udostępnionego aplikacji.

Panel pokazuje zajęte, całkowite, wolne i procent użycia. „Wyłączony” oznacza poprawny odczyt o zerowej pojemności. „Niedostępne” oznacza brak lub niepoprawny odczyt; nie jest zamieniane na 0.

Swap może obejmować zram. Wartości nie określają fizycznego miejsca zajętego na dysku ani stopnia kompresji. Zajęty swap sam w sobie nie dowodzi spowolnienia; panel nie mierzy tempa swap-in/swap-out. Nie dodawaj tej liczby do RAM jako całkowitego fizycznego użycia pamięci.

## Uprawnienia i prywatność

Rola manager pozwala odczytywać statystyki i zatrzymywać aplikacje. Kod używa GET do odczytu i POST wyłącznie do zatrzymania zweryfikowanej aplikacji. Token Supervisora pozostaje w backendzie. Swap odczytywany jest bez uprawnień administratora i bez zmiany swappiness lub rozmiaru swapu. Brak zewnętrznej telemetrii, bazy danych i zapisywania historii.

## Zatrzymywanie aplikacji

Przycisk Zatrzymaj wywołuje standardowe zatrzymanie przez Supervisor po potwierdzeniu nazwy aplikacji. Nie jest to surowy SIGKILL dowolnego procesu. Core, Supervisor i monitor są chronione. Zatrzymanie np. Mosquitto lub Zigbee2MQTT przerwie zależne funkcje domu. Ponowne uruchomienie jest dostępne w ustawieniach aplikacji HA. Ustawienia autostartu i watchdog nie są zmieniane.

Operacje wymagają wejścia przez Ingress oraz tokenu CSRF. Dostęp do panelu powinien być przyznawany tylko użytkownikom uprawnionym do zatrzymywania aplikacji; nie ma dodatkowego systemu ról wewnątrz panelu.

## Oszczędzanie zasobów

Pomiary pobierane są na żądanie. Ukryta karta nie odpytuje serwera. Otwarta domyślnie odświeża co 10 sekund (można ustawić 30 lub 60). Kilka kart współdzieli jeden ostatni pomiar przez 5 sekund. Liczba równoległych odczytów dodatków została ograniczona do dwóch. Brak historii i zależności backendu poza standardową biblioteką Pythona.

Są to ograniczenia wykonywanej pracy i liczby wątków, a nie gwarancja konkretnego zużycia RAM. Porównaj pamięć aplikacji przed i po aktualizacji w podobnym obciążeniu.

## Diagnostyka

- 403: sprawdź rolę manager w konfiguracji aplikacji.
- Brak statystyk jednej usługi: panel oznacza niepełne dane.
- Swap niedostępny: sprawdź logi i dostęp do /proc/meminfo w środowisku aplikacji.
- Po aktualizacji otwórz panel ponownie, by pobrać nowe pliki interfejsu.

Dokumentacja źródłowa: https://docs.kernel.org/filesystems/proc.html
