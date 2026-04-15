# Morning Check-in Agent

## Tek Sorumluluk
`ui/morning_checkin.py` ekranını üretmek: günün ilk açılışında zorunlu check-in, 40+ karakter cevap, streak görünümü.

## Kullanılacak PyQt6 Bileşenleri
- Tam ekran pencere (`QWidget` / `QMainWindow`)
- `QLabel`, `QTextEdit`, `QPushButton`, `QVBoxLayout`, `QHBoxLayout`
- `QPropertyAnimation` (yetersiz girişte buton titreme)
- `QTimer` (gerekirse küçük UI efektleri)

## Core Interface Kullanımı
- `core.get_streak()`
- `core.save_checkin(text: str)`

## Kesinlikle Yazılmayacaklar
- `detection/`, `privacy/`, `dns_proxy/`, `system/` import/değişiklik YASAK.
- Doğrudan sqlite bağlantısı açma; sadece `core.save_checkin` kullan.

## Görsel Davranış Kuralları
- Tam ekran, sakin koyu tema.
- Soru listesi her gün tek soruya rotasyonla düşmeli.
- Minimum 40 karakter olmadan pencere kapanmamalı.
- Sayaç: eksikken `X karakter daha`, yeterliyse `✓`.
- Eksik karakterde buton titreme animasyonu.
- Sağ üstte streak görünmeli.
- `Esc`, `Alt+F4`, minimize devre dışı.

## Başarı Kriteri
- Günlük soru doğru seçiliyor.
- 40 karakter altı kaydetme engelleniyor ve titreme çalışıyor.
- 40+ karakterde kayıt yapılıyor ve ekran kapanıyor.