# Changelog

## 1.3.0

- Zatrzymywanie uruchomionych aplikacji przez Supervisor API, z potwierdzeniem.
- Blokada zatrzymania Core, Supervisora i monitora zasobów.
- Weryfikacja celu na serwerze, dostęp przez Ingress i ochrona żądań przed CSRF.
- Wspólny, pięciosekundowy cache statystyk dla otwartych paneli.
- Zmniejszenie liczby równoległych odczytów z ośmiu do dwóch.
- Domyślne odświeżanie co 10 s i pauza po ukryciu karty.
- Wyłączenie rutynowych logów każdego żądania HTTP.

Nie wykonano jeszcze pomiaru porównawczego RAM na Home Assistant Green.

## 1.2.0

- Dodano systemowe zużycie swapu: zajęte, wolne, całkowite i procent użycia.
- Rozróżniono brak aktywnego swapu i niedostępność pomiaru.
- Dodano wyjaśnienia dotyczące swapu, zram i ograniczeń pomiaru.
- Dodano dokumentację dla zakładki aplikacji oraz testy odczytu swapu.

## 1.1.0

- Uproszczono ciemny interfejs i zmieniono nazwę na Zasoby HA.
- Poprawiono opisy RAM, CPU i liczników sieci.
- Dodano sygnalizowanie niepełnych i nieaktualnych pomiarów.
- Uwzględniono rolę manager niezbędną do odczytów Supervisor API.

## 1.0.0

- Pierwsza wersja lokalna: tabela statystyk Core i aplikacji.
