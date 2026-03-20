# Epson USB Waste Counter Tool

This project reads and resets waste ink counters for Epson USB printers that are compatible with the vendored `reinkpy` database.

It uses:

- `pyusb` for USB access
- a vendored copy of the `reinkpy` logic and model database
- the Epson `EPSON Utility` USB interface (`MI_02`, interface number `2`)

## Quick Start

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

List connected Epson utility devices:

```powershell
py .\epson_waste_counter_tool.py --list
```

List models known by the vendored `reinkpy` database:

```powershell
py .\epson_waste_counter_tool.py --supported-models
```

Read counters from all detected compatible printers:

```powershell
py .\epson_waste_counter_tool.py
```

Read counters from one printer only:

```powershell
py .\epson_waste_counter_tool.py --serial 5844384B3034333527
```

Reset one printer after physical pad cleaning:

```powershell
py .\epson_waste_counter_tool.py --serial 5844384B3034333527 --reset --yes
```

Reset all detected compatible printers:

```powershell
py .\epson_waste_counter_tool.py --all --reset --yes
```

## Files

- `epson_waste_counter_tool.py`: main CLI tool
- `requirements.txt`: Python dependency list
- `CLEANING_GUIDE.md`: generic physical cleaning guide for waste pads
- `vendor/reinkpy/`: vendored Python sources used for the Epson EEPROM workflow
- `vendor/libusb-1.0.dll`: official Windows `libusb` runtime used by `pyusb`

## Safety

This tool only resets the software counters. It does **not** physically clean the waste pads.

Do the physical maintenance first, then run the reset.

When `--reset` is used, the script shows a blocking warning window before writing anything. The reset continues only if the user confirms that the waste pads were physically cleaned or replaced.

Do not assume every Epson printer is supported. The script reads safely by default, but it only resets when the detected model exposes a known waste-counter reset operation in the vendored `reinkpy` database.

## Cleaning Guide

Read the physical maintenance guide before any reset:

- `CLEANING_GUIDE.md`

## Multilingual Summary

### English

This tool reads and resets Epson waste ink counters over USB for models supported by the bundled `reinkpy` database. Reset only after physically cleaning or replacing the waste ink pads.

### Francais

Cet outil lit et remet a zero les compteurs d'encre usagee Epson via USB pour les modeles supportes par la base `reinkpy` embarquee. Ne faites la remise a zero qu'apres avoir reellement nettoye ou remplace les tampons d'encre usagee.

### Espanol

Esta herramienta lee y reinicia los contadores de tinta residual Epson por USB para los modelos compatibles con la base `reinkpy` incluida. Realice el reinicio solo despues de limpiar o reemplazar fisicamente las almohadillas de tinta residual.

### Portugues

Esta ferramenta le e redefine os contadores de tinta residual Epson por USB para os modelos compativeis com a base `reinkpy` incluida. So faca o reset depois de limpar ou substituir fisicamente as almofadas de tinta residual.

### Deutsch

Dieses Werkzeug liest und setzt Epson-Tintenauffangzaehler ueber USB fuer Modelle zurueck, die von der mitgelieferten `reinkpy`-Datenbank unterstuetzt werden. Fuehren Sie das Zuruecksetzen nur durch, nachdem die Tintenschwamm- oder Auffangpads physisch gereinigt oder ersetzt wurden.

### Italiano

Questo strumento legge e azzera i contatori dell'inchiostro di scarto Epson tramite USB per i modelli supportati dal database `reinkpy` incluso. Eseguire l'azzeramento solo dopo aver pulito o sostituito fisicamente i tamponi di inchiostro di scarto.

### العربية

تقوم هذه الأداة بقراءة وإعادة ضبط عدادات حبر النفايات لطابعات Epson عبر USB للطرازات المدعومة في قاعدة بيانات `reinkpy` المضمنة. لا تقم بإعادة الضبط إلا بعد تنظيف وسادات حبر النفايات أو استبدالها فعلياً.

### 中文

此工具可通过 USB 读取并重置 Epson 打印机的废墨计数器，适用于内置 `reinkpy` 数据库支持的机型。只有在真实清洁或更换废墨垫之后，才应执行计数器清零。

### हिन्दी

यह टूल USB के माध्यम से Epson प्रिंटर के waste ink counter को पढ़ता और reset करता है, लेकिन केवल उन्हीं मॉडलों पर जिनका समर्थन bundled `reinkpy` database में मौजूद है। reset केवल तभी करें जब waste ink pads को वास्तव में साफ या बदला जा चुका हो।

### Русский

Этот инструмент считывает и сбрасывает счетчики отработанных чернил Epson по USB для моделей, поддерживаемых встроенной базой `reinkpy`. Выполняйте сброс только после фактической очистки или замены впитывающих прокладок.
