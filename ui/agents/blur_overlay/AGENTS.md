# Blur Overlay Agent

## Tek Sorumluluk
`ui/blur_overlay.py` ekranını üretmek: tetikleme anında tam ekran, sakin görünümlü blur/friction overlay ve süre bitiminde seçim ekranı.

## Kullanılacak PyQt6 Bileşenleri
- `QWidget`, `QMainWindow` veya `QDialog` (fullscreen overlay)
- `QGraphicsBlurEffect` veya painter tabanlı blur katmanı
- `QPropertyAnimation`, `QTimer`, `QEasingCurve`
- `QPushButton`, `QLabel`, `QFrame`, `QVBoxLayout`, `QHBoxLayout`, `QGridLayout`
- SVG halka için `QSvgRenderer` (opsiyonel) veya `QPainter` ile custom progress ring

## Core Interface Kullanımı
- Bu ekran backend verisine bağımlı olmak zorunda değil.
- Gerekirse sadece izinli interface'ler:
  - `core.get_goals()`
  - `core.update_settings(key, value)`
- Başka hiçbir modüle dokunma.

## Kesinlikle Yazılmayacaklar
- `detection/`, `privacy/`, `dns_proxy/`, `system/` altında import/değişiklik YASAK.
- Ağ çağrısı, telemetry, dışarı veri gönderimi YASAK.

## Görsel Davranış Kuralları
- Tema: koyu ve sakin (`#0a0a0a` taban), yargılayıcı olmayan dil.
- 15 saniyelik halka geri sayım animasyonu akıcı çalışmalı.
- Süre dolunca tek seferde seçim ekranına geçiş:
  - `Siteyi kapat` birincil aksiyon
  - 3 alternatif eylem kartı
- Alternatif seçilince 2 dakikalık aktivite timer'ı başlat, bitince overlay kapanır.
- `Esc`, `Alt+F4`, minimize devre dışı.

## Başarı Kriteri
- Ekran tam ekranda açılıyor, kapanış kısıtları çalışıyor.
- Geri sayım 15 saniye doğru ilerliyor.
- Süre sonunda seçim ekranı doğru geçiyor.
- Alternatif seçince 2 dakikalık ekran gösteriliyor ve bitince kapanıyor.