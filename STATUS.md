# Project Status — NoFapShield
_Last updated: 2026-04-15_

---

## 1. Tamamlananlar

### Backend — `src/shield/` (131 test, tümü geçiyor)

| Modül | Sınıf / Servis | Testler |
|---|---|---|
| `core/` | `Config`, `Orchestrator` | 8 + 8 = 16 |
| `db/` | `DBService`, streak logic | 16 + 6 + 2 = 24 |
| `detection/` | `ScreenshotCapture`, `NSFWClassifier`, `HybridScorer` | 3 + 7 + 10 = 20 |
| `dns_proxy/` | `BlocklistManager`, `DNSProxyService` | 12 + 11 = 23 |
| `privacy/` | `AccountabilityService` | 22 |
| `system/` | `NSSMService`, `UninstallProtection`, `SystemService` | 12 + 14 = 26 |

```
131 passed, 100 warnings in ~7s
```

Backend importları temiz:
```
python -c "from shield.core import Orchestrator, Config; print('import OK')"
# → import OK
```

### UI — `ui/` + `main.py`

Dosyalar yazıldı (~3 600 satır):

| Dosya | İçerik |
|---|---|
| `ui/blur_overlay.py` | Tam ekran NSFW blur overlay |
| `ui/dashboard.py` | İstatistik paneli |
| `ui/morning_checkin.py` | Günlük check-in ekranı |
| `ui/onboarding.py` | İlk kurulum akışı |
| `ui/settings.py` | Ayarlar ekranı |
| `main.py` | Akış yöneticisi (argparse, otomatik ekran geçişi) |

---

## 2. Eksik / Çalışmıyor

### Kritik

**PyQt6 kurulu değil ve `pyproject.toml`'a eklenmemiş.**  
Tüm UI importları `ModuleNotFoundError` veriyor:
```
python -c "from ui.blur_overlay import BlurOverlayWindow"
# → ModuleNotFoundError: No module named 'PyQt6'
```

**UI ↔ Backend entegrasyonu yok.**  
`main.py` `shield.core.Orchestrator`'a bağlanmıyor. `import core` deniyor, başarısız olursa `_CoreFallback` stub'ı devreye giriyor. Bu stub `get_goals()` ve `get_checkin_history()` döndürüyor, başka hiçbir şey yok.  
Somut eksikler:
- `Orchestrator.register_friction_callback()` hiçbir yerde çağrılmıyor → blur overlay asla tetiklenmiyor
- `DBService` dashboard'a bağlı değil → streak/istatistik verisi görünmüyor
- `Config` settings ekranına bağlı değil → ayar değişiklikleri kaydedilmiyor

**UI testleri yok.**  
`tests/test_ui/` dizini mevcut değil.

### Minör

- `datetime.utcnow()` 7 farklı yerde kullanılıyor (`orchestrator.py`, `scorer.py`, `screenshot.py`, `db/__init__.py`). Python 3.12'de deprecated, gelecek sürümde kaldırılacak. 100 uyarı bundan geliyor.
- DNS proxy ve NSSM servisi **admin yetkisi gerektirir**. Bu durum dokümanlarda belirtilmemiş.
- Windows system tray ikonu yok — uygulama kapatıldığında arka planda çalışmaya devam etmiyor.

---

## 3. Kurulum (Şu An Çalıştırmak İçin)

```bash
# 1. Bağımlılıkları kur
pip install -e ".[dev]"
pip install PyQt6  # henüz pyproject.toml'da yok

# 2. Backend testlerini çalıştır (PyQt6 gerekmez)
python -m pytest tests/ --tb=short

# 3. UI'ı doğrudan başlat (backend entegrasyonu yok, stub ile çalışır)
python main.py --screen dashboard
python main.py --screen overlay
python main.py --screen onboarding
```

DNS proxy ve NSSM için **yönetici olarak çalıştır** gerekli.

---

## 4. Bilinen Buglar ve TODO'lar

| # | Durum | Açıklama |
|---|---|---|
| 1 | BUG | `main.py` hiçbir zaman gerçek `Orchestrator`'ı başlatmıyor |
| 2 | BUG | Blur overlay, `friction_callback` almadığı için asla görünmüyor |
| 3 | BUG | Dashboard streak/istatistik verisi göstermiyor (DBService bağlı değil) |
| 4 | BUG | Settings kaydetmiyor (Config bağlı değil) |
| 5 | TODO | `PyQt6` bağımlılığını `pyproject.toml`'a ekle |
| 6 | TODO | `datetime.utcnow()` → `datetime.now(datetime.UTC)` (7 konum) |
| 7 | TODO | System tray ikonu — arka planda çalışma |
| 8 | TODO | Admin yetki kontrolü ve kullanıcıya açıklama |
| 9 | TODO | UI smoke testleri (en azından import + instantiation) |
| 10 | TODO | NSSM kurulum scripti veya Makefile |

---

## 5. Sıradaki Milestone

**`feat/shield-integration` — UI ↔ Backend bağlantısı**

Öncelik sırasıyla:

1. `PyQt6`'yı `pyproject.toml`'a ekle
2. `main.py`'yi `shield.core` paketine bağla:
   - `Orchestrator` ve `DBService` oluştur
   - `register_friction_callback()` → `BlurOverlayWindow`'u tetikle
   - `DBService` → `DashboardWindow`'a streak/olay verisi aktar
   - `Config` → `SettingsWindow`'a bağla (okuma + yazma)
3. `datetime.utcnow()` uyarılarını gider
4. `Orchestrator.start()` sonrası sistem tepsisi ikonu ekle
5. Temel UI smoke testleri ekle

Bu milestone tamamlandığında uygulama uçtan uca çalışır hale gelir.
