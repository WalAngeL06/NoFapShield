# Onboarding Agent

## Tek Sorumluluk
`ui/onboarding.py` ekranını üretmek: ilk kurulum sihirbazı (3 adım) ve ayarların `core` ile kaydı.

## Kullanılacak PyQt6 Bileşenleri
- `QStackedWidget` veya wizard benzeri adım yapısı
- `QLabel`, `QLineEdit`, `QTextEdit`, `QPushButton`, `QListWidget`
- Adım göstergesi ve basic geçiş animasyonları

## Core Interface Kullanımı
- `core.update_settings(key: str, value)`

## Kesinlikle Yazılmayacaklar
- `detection/`, `privacy/`, `dns_proxy/`, `system/` import/değişiklik YASAK.
- Parola hashleme backend dışında yapılmayacak; değer `core` üzerinden aktarılacak.

## Görsel Davranış Kuralları
- 3 adım:
  1. Hedefini yaz
  2. Alternatif eylemleri seç/yaz
  3. Şifre ve opsiyonel partner e-posta
- Karanlık, sade, destekleyici dil.
- Gerekli alanlar dolmadan tamamlanamaz.
- `Esc`, `Alt+F4`, minimize devre dışı.

## Başarı Kriteri
- 3 adım eksiksiz ilerliyor.
- Ayarlar doğru anahtarlarla `core.update_settings` üzerinden yazılıyor.
- Onboarding tamamlandığında ekran temiz şekilde kapanıyor.