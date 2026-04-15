# Dashboard Agent

## Tek Sorumluluk
`ui/dashboard.py` ekranını üretmek: streak, haftalık görünüm, hedefler, geçmiş check-in, tetiklenme logları.

## Kullanılacak PyQt6 Bileşenleri
- `QWidget`, `QTabWidget`, `QCalendarWidget` veya custom week strip
- `QListWidget`, `QTableWidget`, `QLabel`, `QScrollArea`, `QVBoxLayout`, `QHBoxLayout`

## Core Interface Kullanımı
- `core.get_streak()`
- `core.get_goals()`
- `core.get_checkin_history()`
- `core.get_trigger_log()`

## Kesinlikle Yazılmayacaklar
- `detection/`, `privacy/`, `dns_proxy/`, `system/` import/değişiklik YASAK.
- Log manipülasyonu ya da DB'ye direkt erişim YASAK.

## Görsel Davranış Kuralları
- Ana pencere, koyu minimal tema.
- Streak öne çıkarılır, haftalık görünüm okunur olmalı.
- Check-in geçmişinde zaman bağlamı ("3 hafta önce" vb.) gösterilmeli.
- Trigger logları saat/yoğunluk perspektifiyle okunmalı.

## Başarı Kriteri
- Tüm paneller `core` verisiyle doluyor.
- Boş veri durumlarında ekran kırılmıyor, anlamlı boş durum metni gösteriyor.
- Kullanıcı geçmişini hızlı tarayabiliyor.