# YT60245 Manual Converter 🇸🇪

Automatiskt GitHub-workflow som konverterar den engelska manualen till en svensk PDF.

## 🚀 Användning
1. Ladda upp originalet som `input/original_manual.pdf`.
2. Lägg den svenska texten i `input/svensk_text.txt`.
3. Kör workflowet via **Actions → Convert Manual to Swedish PDF → Run workflow**.
4. När jobbet är klart hittar du `converted-pdf` under *Artifacts* – ladda ner den färdiga PDF:en.

## 🧩 Teknik
- Python 3.11
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [ReportLab](https://www.reportlab.com/dev/docs/)

## 🛠 Utbyggbart
Du kan förbättra skriptet för:
- Exakt textplacering per block
- Rubriker med olika fontstorlek
- Tvåspaltig text eller punktlistor

---
© 2025 – Automatisk konvertering till svenska
