# PDF Catalog Order Manager

Desktop aplikacija koja ucitava PDF katalog proizvoda, automatski pronalazi proizvode i omogucava selektovanje, unos kolicine i export porudzbine (Excel / PDF).

## Tech stack

- Python
- PySide6 (GUI)
- PyMuPDF (PDF processing)
- Pillow (image processing)
- openpyxl (Excel export)
- reportlab (PDF export)
- PyInstaller (packaging)

## Struktura

```
catalog-order-manager/
├── app/
│   ├── main.py
│   ├── models/     (product.py, order.py)
│   ├── pdf/        (parser.py, text_extractor.py, image_extractor.py)
│   ├── ui/         (main_window.py, product_card.py, product_list.py, widgets.py)
│   ├── export/     (excel_exporter.py, pdf_exporter.py)
│   ├── services/   (catalog_service.py, order_service.py)
│   └── utils/      (code_parser.py, image_utils.py)
├── tests/
│   ├── test_parser.py
│   ├── test_code_parser.py
│   └── test_export.py
├── requirements.txt
└── main.py
```

## Instalacija

```
pip install -r requirements.txt
```

## Pokretanje

```
python main.py
```

## Build za Windows (.exe)

Pakovanje radi sa PyInstaller-om i sprema aplikaciju tako da na Windows
masini NIJE potreban Python niti bilo koja instalirana biblioteka.

Opcija A - gradjenje na Windows masini (najjednostavnije):

1. Skini i instaliraj Python sa https://www.python.org/downloads/
   (obavezno oznaciti "Add Python to PATH").
2. Dvostrukim klikom pokreni `build_windows.bat`.
3. Rezultat je `dist\InteractiveCatalog\InteractiveCatalog.exe` - pokreni ga
   direktno. Cela `InteractiveCatalog` folder mora ostati zajedno.

Opcija B - gradjenje bez Python-a, preko GitHub Actions:

1. Push-uj projekat na GitHub i pokreni workflow "Build Windows .exe"
   (Actions tab; podrzano i na push-u tagova `v*`).
2. Skinuti artifact `InteractiveCatalog-windows` (zip) sa Actions strane.

Napomene:

- Prvi put kada se .exe pokrene, Windows moze prikazati SmartScreen
  upozorenje jer .exe nije potpisan - klikni "More info", pa "Run anyway".
- Sample katalog (`samples_pdfs/`) se ne pakuje u .exe - PDF katalog se
  bira u aplikaciji preko Open dijaloga.

## Faze razvoja

1. Analiza PDF-a (inspect_pdf.py)
2. Product model
3. Parser (bez GUI-ja)
4. CLI test (parse_catalog.py)
5. GUI
6. Excel export
7. PDF export
8. Validacija i error handling
9. Testovi
10. PyInstaller packaging