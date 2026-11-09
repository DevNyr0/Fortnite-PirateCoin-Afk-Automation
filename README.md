# Nyr0 Pirate Coin Automation

Fortnite Pirate Pass ve ada maçları için geliştirilmiş modüler, otomatik maç döngüsü ve Pirate Shop Access takip programı. Maç bittiğinde veya elenildiğinde otomatik olarak **Play Again** (veya lobiye düşerse **Play**) butonuna tıklar, AFK kalmamak için karakteri hareket ettirir ve bulunan Pirate Shop Access sayısını canlı olarak ekranda gösterir.

## Proje Yapısı

```
piratecoinmacro/
├── assets/
│   ├── templates/            Buton ve bildirim şablon görselleri
│   └── icons/                Uygulama simgesi ve logo dosyaları
├── core/
│   ├── config.py             Yapılandırma, koordinat ve zamanlama ayarları
│   ├── vision.py             Ekran yakalama, hızlı ROI ve şablon tarama
│   ├── input_handler.py      Doğrudan giriş simülasyonu ve Fortnite pencere odağı
│   ├── state.py              Makro durum takibi ve canlı olay yayını
│   └── snip.py               Etkileşimli ekran kırpma aracı
├── web/
│   ├── index.html            Modern kontrol paneli arayüzü
│   ├── style.css             Fortnite temalı özel stil dosyası
│   └── app.js                Ön yüz olayları ve gerçek zamanlı sayaçlar
├── main.py                   Ana uygulama ve Eel motoru başlatıcısı
├── engine.py                 Geriye dönük uyumluluk köprüsü
├── Start.bat                 Tek tıkla başlatma betiği
├── Install_Requirements.bat  Gerekli kütüphaneleri yükleme betiği
└── Build_EXE.bat             Tek parça taşınabilir EXE derleme betiği
```

## Özellikler

- **Kesintisiz Maç Döngüsü:** Takım elendiğinde sonuç ekranındaki Play Again butonunu, lobiye düşerse lobi Play butonunu otomatik algılar ve tıklar.
- **W + Space Modu:** Açıldığında bağımsız bir iş parçacığında her 3 saniyede bir ileri zıplama hareketi yapar. Ekran taramasından bağımsız çalıştığı için düşük sistemli laptoplarda da aksamadan tam vaktinde işler.
- **Pirate Shop Access Takibi:** Ekranda beliren "You Found Pirate Shop Access" bildirimlerini sayar ve arayüzde canlı sayaç olarak gösterir.
- **Bölgesel Tarama (Düşük CPU):** Ekranın tamamını taramak yerine sadece butonların çıktığı alanlara odaklanır; düşük sistemli laptoplarda dahi işlemciyi yormaz.
- **Raporlama Koruması:** Maç sonu ekranlarında yanlışlıkla "Report Player" butonuna tıklamayı engeller, açılırsa otomatik kapatır.
- **Ekran Kırpma Aracı (Snip Tool):** Farklı bir ekran çözünürlüğü veya oyun dili kullanıyorsanız arayüzdeki kırpma aracıyla ekrandaki Play Again butonunu seçip kaydedebilirsiniz.

## Kurulum

1. Bilgisayarınızda **Python 3.10 veya üzeri** kurulu olduğundan emin olun.
2. Gerekli paketleri yüklemek için `Install_Requirements.bat` dosyasını çalıştırın.
   *(Manuel yüklemek isterseniz: `pip install -r requirements.txt`)*

## Kullanım

1. `Start.bat` dosyasına çift tıklayarak programı başlatın.
2. Açılan modern arayüzden tercihlerinizi (W + Space vb.) kontrol edin.
3. Fortnite'a geçin, ilk maça girin ve klavyeden **F8** tuşuna basarak (veya arayüzdeki büyük sarı butondan) otomasyonu başlatın.
4. Durdurmak istediğinizde yine **F8** tuşuna basmanız yeterlidir.

## İpuçları

- **Görüntü Modu:** Fortnite'ı **Pencereli Tam Ekran (Windowed Fullscreen)** modunda oynamanız görüntü algılamanın en kararlı şekilde çalışmasını sağlar.
- **Buton Algılanmazsa:** Çözünürlüğünüz veya oyun içi ölçeğiniz farklıysa arayüzdeki **Snip Button** butonuna basın ve ekrandaki Play Again butonunun etrafını seçip bırakın; program yeni görseli anında hafızaya alacaktır.
- **Tek Parça EXE Yapma:** Python kurulu olmayan bir cihaza taşımak veya tek dosya haline getirmek isterseniz `Build_EXE.bat` dosyasını çalıştırabilirsiniz.
