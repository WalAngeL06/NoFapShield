# Settings Agent

## Tek Sorumluluk
`ui/settings.py` ekranını üretmek: hedef, alternatif eylem, şifre, hassasiyet, partner e-posta ayarlarının düzenlenmesi.

## Kullanılacak PyQt6 Bileşenleri
- `QWidget`, `QFormLayout`, `QSlider`, `QLineEdit`, `QTextEdit`, `QPushButton`, `QListWidget`
- Geri bildirim için `QLabel`/inline status mesajları

## Core Interface Kullanımı
- `core.update_settings(key: str, value)`
- `core.verify_password(pw: str) -> bool` (şifre değişim akışı için)
- `core.get_goals()` (mevcut hedefleri prefill etmek için)

## Kesinlikle Yazılmayacaklar
- `detection/`, `privacy/`, `dns_proxy/`, `system/` import/değişiklik YASAK.
- bcrypt işi UI tarafında yapılmaz; sadece core çağrılır.

## Görsel Davranış Kuralları
- Sakin koyu tema, form odaklı net düzen.
- Şifre değişiminde mevcut şifre doğrulama + yeni şifre kaydı.
- Hassasiyet slider değeri anlık görünmeli.

## Başarı Kriteri
- Her ayar güncellemesi doğru `core.update_settings` anahtarıyla kaydoluyor.
- Hatalı mevcut şifrede değişim engelleniyor.
- Form akışı kullanıcıyı kırmadan net geri bildirim veriyor.