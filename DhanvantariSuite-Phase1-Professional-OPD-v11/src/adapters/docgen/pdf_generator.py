import io
import os
from typing import List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.domain.models.invoice import Invoice
from src.domain.models.consultation import Consultation
from src.domain.models.patient import Patient
from src.domain.ports.doc_gen_port import DocGenPort

# Dictionary of translations for English, Marathi, Hindi, and Arabic
# Extensible structure: additional languages can be added by declaring a new key block
TRANSLATIONS = {
    "en": {
        "invoice_title": "INVOICE / RECEIPT",
        "prescription_title": "MEDICAL PRESCRIPTION",
        "invoice_no": "Invoice No:",
        "date": "Date:",
        "patient_name": "Patient Name:",
        "patient_no": "Patient No:",
        "mobile": "Mobile:",
        "age_sex": "Age / Sex:",
        "visit_type": "Visit Type:",
        "item_desc": "Description",
        "qty": "Qty",
        "price": "Price",
        "tax": "Tax",
        "total": "Total",
        "subtotal": "Subtotal:",
        "discount": "Discount:",
        "grand_total": "Grand Total:",
        "amount_paid": "Amount Paid:",
        "amount_due": "Amount Due:",
        "payment_mode": "Payment Mode:",
        "payment_status": "Status:",
        "rx": "Rx (Prescription Details):",
        "medicine": "Medicine Name",
        "dosage": "Dosage",
        "timing": "Timing (M-A-N)",
        "freq": "Frequency",
        "duration": "Duration",
        "food_relation": "Food Relation",
        "instructions": "Instructions",
        "notes": "Doctor Notes:",
        "advice_notes": "Advice / Doctor Notes:",
        "follow_up_date": "Follow-up Date:",
        "vitals": "Vitals:",
        "symptoms": "Chief Complaints / Symptoms:",
        "diagnosis": "Clinical Diagnosis:",
        "consult_charges": "Consultation Charges:",
        "medicine_charges": "Medicine Charges:",
        "lab_charges": "Lab Charges:",
        "doctor_designation": "Consultant Physician",
        "doctor_signature": "Doctor's Signature & Stamp",
        "footer_disclaimer": "This is an electronically generated prescription via Dhanvantari Clinic ERP. Please keep for your medical records.",
        "food_map": {
            "After Food": "After Food",
            "Before Food": "Before Food",
            "Empty Stomach": "Empty Stomach",
            "Bedtime": "Bedtime",
            "With Food": "With Food",
            "Anytime": "Anytime"
        },
        "duration_map": {
            "2 Days": "2 Days",
            "3 Days": "3 Days",
            "5 Days": "5 Days",
            "7 Days": "7 Days",
            "10 Days": "10 Days",
            "15 Days": "15 Days",
            "1 Month": "1 Month",
            "2 Months": "2 Months"
        }
    },
    "mr": {
        "invoice_title": "देयक / पावती",
        "prescription_title": "वैद्यकीय औषधोपचार पत्रक",
        "invoice_no": "देयक क्रमांक:",
        "date": "दिनांक:",
        "patient_name": "रुग्णाचे नाव:",
        "patient_no": "रुग्ण क्रमांक:",
        "mobile": "मोबाईल:",
        "age_sex": "वय / लिंग:",
        "visit_type": "भेटीचा प्रकार:",
        "item_desc": "तपशील",
        "qty": "प्रमाण",
        "price": "दर",
        "tax": "कर",
        "total": "एकूण",
        "subtotal": "उप-एकूण:",
        "discount": "सवलत:",
        "grand_total": "एकूण रक्कम:",
        "amount_paid": "भरलेली रक्कम:",
        "amount_due": "बाकी रक्कम:",
        "payment_mode": "पैसे भरण्याची पद्धत:",
        "payment_status": "स्थिती:",
        "rx": "औषधोपचार तपशील (Rx):",
        "medicine": "औषधाचे नाव",
        "dosage": "मात्रा",
        "timing": "वेळ (सकाळ-दुपार-रात्र)",
        "freq": "वारंवारता",
        "duration": "कालावधी",
        "food_relation": "जेवणासंबंधी",
        "instructions": "सूचना",
        "notes": "डॉक्टरची नोंद:",
        "advice_notes": "सल्ला व डॉक्टरांची नोंद:",
        "follow_up_date": "पुढील तपासणी दिनांक:",
        "vitals": "शारीरिक तपासणी:",
        "symptoms": "प्रमुख तक्रारी / लक्षणे:",
        "diagnosis": "वैद्यकीय निदान:",
        "consult_charges": "तपासणी शुल्क:",
        "medicine_charges": "औषध शुल्क:",
        "lab_charges": "लॅब चाचणी शुल्क:",
        "doctor_designation": "सल्लागार फिजिशियन",
        "doctor_signature": "डॉक्टरांची स्वाक्षरी व शिक्का",
        "footer_disclaimer": "हे प्रिस्क्रिप्शन धनवंतरी क्लिनिक ईआरपी द्वारे डिजिटल पद्धतीने व्युत्पन्न केले आहे. कृपया आपल्या नोंदीसाठी जपून ठेवा.",
        "food_map": {
            "After Food": "जेवणानंतर",
            "Before Food": "जेवणापूर्वी",
            "Empty Stomach": "उपाशी पोटी",
            "Bedtime": "झोपताना",
            "With Food": "जेवणासोबत",
            "Anytime": "कधीही"
        },
        "duration_map": {
            "2 Days": "२ दिवस",
            "3 Days": "३ दिवस",
            "5 Days": "५ दिवस",
            "7 Days": "७ दिवस",
            "10 Days": "१० दिवस",
            "15 Days": "१५ दिवस",
            "1 Month": "१ महिना",
            "2 Months": "२ महिने"
        }
    },
    "hi": {
        "invoice_title": "चालान / रसीद",
        "prescription_title": "चिकित्सा पर्चा",
        "invoice_no": "पर्ची संख्या:",
        "date": "दिनांक:",
        "patient_name": "मरीज का नाम:",
        "patient_no": "मरीज संख्या:",
        "mobile": "मोबाइल:",
        "age_sex": "आयु / लिंग:",
        "visit_type": "परामर्श प्रकार:",
        "item_desc": "विवरण",
        "qty": "मात्रा",
        "price": "दर",
        "tax": "कर",
        "total": "कुल",
        "subtotal": "उप-योग:",
        "discount": "छूट:",
        "grand_total": "कुल राशि:",
        "amount_paid": "भुगतान की गई राशि:",
        "amount_due": "शेष राशि:",
        "payment_mode": "भुगतान का प्रकार:",
        "payment_status": "स्थिति:",
        "rx": "दवा का विवरण (Rx):",
        "medicine": "दवा का नाम",
        "dosage": "खुराक",
        "timing": "समय (सुबह-दोपहर-रात)",
        "freq": "बारंबारता",
        "duration": "अवधि",
        "food_relation": "भोजन संबंध",
        "instructions": "निर्देश",
        "notes": "डॉक्टर की टिप्पणी:",
        "advice_notes": "सलाह व डॉक्टर की टिप्पणी:",
        "follow_up_date": "अगली मुलाकात दिनांक:",
        "vitals": "शारीरिक माप:",
        "symptoms": "मुख्य लक्षण / समस्याएं:",
        "diagnosis": "चिकित्सीय निदान:",
        "consult_charges": "परामर्श शुल्क:",
        "medicine_charges": "दवा शुल्क:",
        "lab_charges": "जांच शुल्क:",
        "doctor_designation": "परामर्श चिकित्सक",
        "doctor_signature": "डॉक्टर के हस्ताक्षर एवं मुहर",
        "footer_disclaimer": "यह पर्चा धनवंतरी क्लीनिक ईआरपी द्वारा डिजिटल रूप से तैयार किया गया है। कृपया इसे सुरक्षित रखें।",
        "food_map": {
            "After Food": "खाने के बाद",
            "Before Food": "खाने से पहले",
            "Empty Stomach": "खाली पेट",
            "Bedtime": "सोते समय",
            "With Food": "भोजन के साथ",
            "Anytime": "कभी भी"
        },
        "duration_map": {
            "2 Days": "२ दिन",
            "3 Days": "३ दिन",
            "5 Days": "५ दिन",
            "7 Days": "७ दिन",
            "10 Days": "१० दिन",
            "15 Days": "१५ दिन",
            "1 Month": "१ महीना",
            "2 Months": "२ महीने"
        }
    },
    "ar": {
        "invoice_title": "فاتورة / إيصال سداد",
        "prescription_title": "الوصفة الطبية الرسمية",
        "invoice_no": "رقم الفاتورة:",
        "date": "التاريخ:",
        "patient_name": "اسم المريض:",
        "patient_no": "رقم الملف الطبي:",
        "mobile": "رقم الهاتف:",
        "age_sex": "العمر / الجنس:",
        "visit_type": "نوع الزيارة:",
        "item_desc": "الوصف والخدمة",
        "qty": "الكمية",
        "price": "السعر",
        "tax": "الضريبة",
        "total": "المجموع",
        "subtotal": "المجموع الفرعي:",
        "discount": "الخصم:",
        "grand_total": "المبلغ الإجمالي:",
        "amount_paid": "المبلغ المدفوع:",
        "amount_due": "المبلغ المتبقي:",
        "payment_mode": "طريقة الدفع:",
        "payment_status": "حالة الدفع:",
        "rx": "جدول العلاج والدواء (Rx):",
        "medicine": "اسم الدواء",
        "dosage": "الجرعة",
        "timing": "التوقيت (صباحاً-ظهراً-مساءً)",
        "freq": "التكرار",
        "duration": "المدة",
        "food_relation": "العلاقة بالطعام",
        "instructions": "التعليمات",
        "notes": "ملاحظات الطبيب:",
        "advice_notes": "نصائح وإرشادات الطبيب المعالج:",
        "follow_up_date": "موعد المراجعة القادم:",
        "vitals": "المؤشرات الحيوية:",
        "symptoms": "الشكوى والأعراض الرئيسية:",
        "diagnosis": "التشخيص الطبي:",
        "consult_charges": "رسوم الكشف:",
        "medicine_charges": "رسوم الأدوية:",
        "lab_charges": "رسوم الفحوصات:",
        "doctor_designation": "طبيب استشاري باطني",
        "doctor_signature": "توقيع الطبيب وخاتم العيادة",
        "footer_disclaimer": "تم إصدار هذه الوصفة الطبية إلكترونياً من خلال نظام دهنفنتري لإدارة العيادات الطبية.",
        "food_map": {
            "After Food": "بعد الأكل",
            "Before Food": "قبل الأكل",
            "Empty Stomach": "على معدة فارغة",
            "Bedtime": "عند النوم",
            "With Food": "مع الطعام",
            "Anytime": "في أي وقت"
        },
        "duration_map": {
            "2 Days": "يومان",
            "3 Days": "٣ أيام",
            "5 Days": "٥ أيام",
            "7 Days": "٧ أيام",
            "10 Days": "١٠ أيام",
            "15 Days": "١٥ يوماً",
            "1 Month": "شهر واحد",
            "2 Months": "شهران"
        }
    }
}


def reshape_for_pdf(text: str, lang: str) -> str:
    """Format and reshape Arabic text with bidirectional algorithm so it renders properly in PDF."""
    if not text:
        return ""
    if lang == "ar":
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            reshaped = arabic_reshaper.reshape(str(text))
            return get_display(reshaped)
        except Exception:
            return str(text)
    return str(text)


class PDFGeneratorAdapter(DocGenPort):
    def __init__(self):
        self.devanagari_font = None
        self.arabic_font = None
        self.arabic_font_bold = None

        # 1. Register Devanagari font (for Marathi & Hindi)
        devanagari_candidates = [
            ("C:\\Windows\\Fonts\\Nirmala.ttc", 0),
            ("C:\\Windows\\Fonts\\gargi.ttf", None),
            ("C:\\Windows\\Fonts\\mangal.ttf", None),
            ("C:\\Windows\\Fonts\\Kokila.ttf", None),
            ("C:\\Windows\\Fonts\\aparaj.ttf", None)
        ]
        for path, sub_idx in devanagari_candidates:
            if os.path.exists(path):
                try:
                    if sub_idx is not None:
                        pdfmetrics.registerFont(TTFont("Devanagari", path, subfontIndex=sub_idx))
                    else:
                        pdfmetrics.registerFont(TTFont("Devanagari", path))
                    self.devanagari_font = "Devanagari"
                    break
                except Exception:
                    pass

        # 2. Register Arabic/Unicode font (Arial has standard full Arabic glyphs on Windows)
        arabic_candidates = [
            ("C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"),
            ("C:\\Windows\\Fonts\\tahoma.ttf", "C:\\Windows\\Fonts\\tahomabd.ttf"),
            ("C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\segoeuib.ttf")
        ]
        for reg_path, bold_path in arabic_candidates:
            if os.path.exists(reg_path):
                try:
                    pdfmetrics.registerFont(TTFont("ArabicFont", reg_path))
                    self.arabic_font = "ArabicFont"
                    if os.path.exists(bold_path):
                        pdfmetrics.registerFont(TTFont("ArabicFont-Bold", bold_path))
                        self.arabic_font_bold = "ArabicFont-Bold"
                    else:
                        self.arabic_font_bold = "ArabicFont"
                    break
                except Exception:
                    pass

    def _get_styles_for_lang(self, lang: str):
        styles = getSampleStyleSheet()
        is_rtl = (lang == "ar")

        if lang in ["mr", "hi"] and self.devanagari_font:
            base_font = self.devanagari_font
            bold_font = self.devanagari_font
        elif lang == "ar" and self.arabic_font:
            base_font = self.arabic_font
            bold_font = self.arabic_font_bold or self.arabic_font
        else:
            base_font = "Helvetica"
            bold_font = "Helvetica-Bold"

        align_main = 2 if is_rtl else 0
        align_right = 0 if is_rtl else 2

        title_style = ParagraphStyle(
            name=f"Title_{lang}",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F766E"),
            alignment=1,  # Centered
            spaceAfter=12
        )
        header_style = ParagraphStyle(
            name=f"SecHead_{lang}",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0F766E"),
            alignment=align_main,
            spaceBefore=8,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            name=f"Body_{lang}",
            parent=styles["Normal"],
            fontName=base_font,
            fontSize=9.5,
            leading=13,
            alignment=align_main,
            textColor=colors.HexColor("#1E293B")
        )
        bold_style = ParagraphStyle(
            name=f"Bold_{lang}",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9.5,
            leading=13,
            alignment=align_main,
            textColor=colors.HexColor("#0F172A")
        )
        doc_name_style = ParagraphStyle(
            name=f"DocName_{lang}",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=13,
            leading=16,
            alignment=align_main,
            textColor=colors.HexColor("#0F172A")
        )
        doc_sub_style = ParagraphStyle(
            name=f"DocSub_{lang}",
            parent=styles["Normal"],
            fontName=base_font,
            fontSize=8.5,
            leading=11,
            alignment=align_main,
            textColor=colors.HexColor("#475569")
        )
        right_title = ParagraphStyle(
            name=f"RightTitle_{lang}",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=12,
            leading=15,
            alignment=align_right,
            textColor=colors.HexColor("#0D9488")
        )
        right_sub = ParagraphStyle(
            name=f"RightSub_{lang}",
            parent=styles["Normal"],
            fontName=base_font,
            fontSize=8.5,
            leading=11,
            alignment=align_right,
            textColor=colors.HexColor("#475569")
        )
        footer_style = ParagraphStyle(
            name=f"Footer_{lang}",
            parent=styles["Normal"],
            fontName=base_font,
            fontSize=7.5,
            leading=10,
            alignment=1,  # Centered
            textColor=colors.HexColor("#94A3B8")
        )

        return {
            "title": title_style,
            "header": header_style,
            "body": body_style,
            "bold": bold_style,
            "doc_name": doc_name_style,
            "doc_sub": doc_sub_style,
            "right_title": right_title,
            "right_sub": right_sub,
            "footer": footer_style,
            "is_rtl": is_rtl
        }

    def generate_invoice_pdf(self, invoice: Invoice, patient: Patient, language: str = "en") -> bytes:
        lang = language if language in TRANSLATIONS else "en"
        t = TRANSLATIONS[lang]
        st = self._get_styles_for_lang(lang)

        def P(text, style_key="body"):
            return Paragraph(reshape_for_pdf(text, lang), st[style_key])

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        # 1. Title
        story.append(P(f"<b>{t['invoice_title']}</b>", "title"))
        story.append(Spacer(1, 8))

        # 2. Metadata Table
        inv_date = invoice.created_at.strftime('%Y-%m-%d') if hasattr(invoice.created_at, 'strftime') else str(invoice.created_at)[:10]
        metadata = [
            [P(f"<b>{t['invoice_no']}</b> {invoice.invoice_number}"),
             P(f"<b>{t['patient_no']}</b> {patient.patient_number}")],
            [P(f"<b>{t['date']}</b> {inv_date}"),
             P(f"<b>{t['patient_name']}</b> {patient.full_name}")],
            [P(f"<b>{t['payment_mode']}</b> {invoice.payment_mode}"),
             P(f"<b>{t['mobile']}</b> {patient.mobile_normalized}")]
        ]
        meta_table = Table(metadata, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT' if st['is_rtl'] else 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # 3. Invoice Items Table
        table_data = [[
            P(f"<b>{t['item_desc']}</b>", "bold"),
            P(f"<b>{t['qty']}</b>", "bold"),
            P(f"<b>{t['price']}</b>", "bold"),
            P(f"<b>{t['tax']}</b>", "bold"),
            P(f"<b>{t['total']}</b>", "bold")
        ]]
        for item in invoice.items:
            table_data.append([
                P(item.description),
                P(str(item.quantity)),
                P(f"{item.unit_price:.2f}"),
                P(f"{item.tax_amount:.2f} ({item.tax_rate}%)"),
                P(f"{item.total:.2f}")
            ])

        items_table = Table(table_data, colWidths=[220, 50, 80, 110, 80])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F766E")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT' if st['is_rtl'] else 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 14))

        # 4. Totals Calculation Table
        totals_data = [
            [P(""), P(f"<b>{t['consult_charges']}</b>", "bold"), P(f"{invoice.consultation_charges:.2f}")],
            [P(""), P(f"<b>{t['medicine_charges']}</b>", "bold"), P(f"{invoice.medicine_charges:.2f}")],
            [P(""), P(f"<b>{t['lab_charges']}</b>", "bold"), P(f"{invoice.lab_charges:.2f}")],
            [P(""), P(f"<b>{t['subtotal']}</b>", "bold"), P(f"{invoice.subtotal:.2f}")],
            [P(""), P(f"<b>{t['discount']}</b>", "bold"), P(f"{invoice.discount_amount:.2f}")],
            [P(""), P(f"<b>{t['grand_total']}</b>", "bold"), P(f"<b>{invoice.total_amount:.2f}</b>", "bold")],
            [P(""), P(f"<b>{t['amount_paid']}</b>", "bold"), P(f"<b>{invoice.amount_paid:.2f}</b>", "bold")],
            [P(""), P(f"<b>{t['amount_due']}</b>", "bold"), P(f"<b>{invoice.amount_due:.2f}</b>", "bold")],
            [P(""), P(f"<b>{t['payment_status']}</b>", "bold"), P(f"<b>{invoice.payment_status.value}</b>", "bold")],
        ]
        totals_table = Table(totals_data, colWidths=[310, 130, 100])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 3),
            ('LINEABOVE', (1, 5), (-1, 5), 1, colors.HexColor("#0F766E")),
            ('LINEABOVE', (1, 6), (-1, 6), 0.5, colors.HexColor("#A0AEC0")),
        ]))
        story.append(totals_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_prescription_pdf(
        self,
        consultation: Consultation,
        patient: Patient,
        language: str = "en",
        doctor=None,
        clinic_settings=None
    ) -> bytes:
        lang = language if language in TRANSLATIONS else "en"
        t = TRANSLATIONS[lang]
        st = self._get_styles_for_lang(lang)

        def P(text, style_key="body"):
            return Paragraph(reshape_for_pdf(text, lang), st[style_key])

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )

        # Resolve Doctor and Clinic details
        raw_doc_name = getattr(doctor, 'full_name', None) or "Dr. Vivek Singh"
        if not raw_doc_name.lower().startswith("dr.") and not raw_doc_name.lower().startswith("dr "):
            doc_name = f"Dr. {raw_doc_name}"
        else:
            doc_name = raw_doc_name

        doc_designation = f"MBBS, MD - {t.get('doctor_designation', 'Consultant Physician')}"
        clinic_name = getattr(clinic_settings, 'clinic_name', None) or "DHANVANTARI CLINIC & HEALTHCARE"
        clinic_address = getattr(clinic_settings, 'clinic_address', None) or "Main Branch, Local Area"
        clinic_phone = getattr(clinic_settings, 'phone', None) or "+91 98765 43210"
        clinic_email = getattr(clinic_settings, 'email', None) or "contact@dhanvantari.local"

        story = []

        # 1. Header: Doctor (left) & Clinic (right)
        doc_info = [
            P(f"<b>{doc_name}</b>", "doc_name"),
            P(doc_designation, "doc_sub"),
        ]
        if getattr(clinic_settings, 'license_number', None):
            doc_info.append(P(f"Reg/Lic: {clinic_settings.license_number}", "doc_sub"))

        clinic_info = [
            P(f"<b>{clinic_name}</b>", "right_title"),
            P(clinic_address, "right_sub"),
            P(f"Ph: {clinic_phone} | Email: {clinic_email}", "right_sub"),
        ]

        if st["is_rtl"]:
            header_table = Table([[clinic_info, doc_info]], colWidths=[270, 270])
        else:
            header_table = Table([[doc_info, clinic_info]], colWidths=[270, 270])

        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0D9488'), spaceBefore=2, spaceAfter=8))

        # 1b. Prescription Document Title Banner
        story.append(P(f"<b>{t['prescription_title']}</b>", "title"))
        story.append(Spacer(1, 4))

        # 2. Patient details bar
        c_date = consultation.created_at.strftime('%d-%b-%Y %I:%M %p') if hasattr(consultation.created_at, 'strftime') else str(consultation.created_at)[:16]
        p_row1 = [
            P(f"<b>{t['patient_name']}</b> {patient.full_name}"),
            P(f"<b>{t['patient_no']}</b> {patient.patient_number}"),
            P(f"<b>{t['date']}</b> {c_date}")
        ]
        p_row2 = [
            P(f"<b>{t['age_sex']}</b> {patient.age} Yrs / {patient.gender}"),
            P(f"<b>{t['mobile']}</b> {patient.mobile_normalized}"),
            P(f"<b>{t['visit_type']}</b> {consultation.consultation_type or 'General OPD'}")
        ]

        if st["is_rtl"]:
            p_row1.reverse()
            p_row2.reverse()

        patient_table = Table([p_row1, p_row2], colWidths=[200, 170, 170])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 8))

        # 3. Vitals block (if any recorded)
        vitals_list = []
        if consultation.blood_pressure:
            vitals_list.append(f"BP: {consultation.blood_pressure} mmHg")
        if consultation.weight:
            vitals_list.append(f"Wt: {consultation.weight} kg")
        if consultation.height:
            vitals_list.append(f"Ht: {consultation.height} cm")
        if getattr(consultation, 'bmi', None):
            vitals_list.append(f"BMI: {consultation.bmi}")
        if consultation.pulse_rate:
            vitals_list.append(f"Pulse: {consultation.pulse_rate} bpm")
        if consultation.temperature:
            vitals_list.append(f"Temp: {consultation.temperature} °F")
        if getattr(consultation, 'spo2', None):
            vitals_list.append(f"SpO2: {consultation.spo2}%")
        if getattr(consultation, 'respiratory_rate', None):
            vitals_list.append(f"Resp: {consultation.respiratory_rate}/min")

        if vitals_list:
            v_cell = P(" &nbsp; | &nbsp; ".join(vitals_list))
            v_label = P(f"<b>{t['vitals']}</b>", "bold")
            if st["is_rtl"]:
                v_table = Table([[v_cell, v_label]], colWidths=[465, 75])
            else:
                v_table = Table([[v_label, v_cell]], colWidths=[75, 465])
            v_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(v_table)
            story.append(Spacer(1, 8))

        # 4. Complaints, Diagnosis & Notes
        cd_data = []
        if consultation.symptoms:
            sym_text = ", ".join(consultation.symptoms)
            lbl = P(f"<b>{t['symptoms']}</b>", "bold")
            val = P(sym_text, "body")
            cd_data.append([val, lbl] if st["is_rtl"] else [lbl, val])

        if consultation.diagnosis:
            lbl = P(f"<b>{t['diagnosis']}</b>", "bold")
            val = P(f"<b><font color='#0F766E'>{consultation.diagnosis}</font></b>", "body")
            cd_data.append([val, lbl] if st["is_rtl"] else [lbl, val])

        if cd_data:
            col_w = [380, 160] if st["is_rtl"] else [160, 380]
            cd_table = Table(cd_data, colWidths=col_w)
            cd_table.setStyle(TableStyle([
                ('PADDING', (0, 0), (-1, -1), 3),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(cd_table)
            story.append(Spacer(1, 8))

        # 5. Rx Prescription Table
        # CRITICAL USER REQUIREMENT:
        # "Prescrption generated should be in that language except medine names"
        story.append(P(f"<b><font size=13 color='#0D9488'>Rx</font> <font size=10 color='#334155'>{t['rx']}</font></b>", "header"))
        story.append(Spacer(1, 4))

        rx_header = [
            P("<b>#</b>", "bold"),
            P(f"<b>{t['medicine']}</b>", "bold"),
            P(f"<b>{t['timing']}</b>", "bold"),
            P(f"<b>{t['duration']}</b>", "bold"),
            P(f"<b>{t['food_relation']}</b>", "bold"),
            P(f"<b>{t['instructions']}</b>", "bold")
        ]
        if st["is_rtl"]:
            rx_header.reverse()
        rx_data = [rx_header]

        food_map = t.get("food_map", {})
        dur_map = t.get("duration_map", {})

        for idx, item in enumerate(consultation.prescription, start=1):
            # Medicine name stays in Latin / English as explicitly requested!
            med_name_p = Paragraph(f"<b>{item.medicine_name}</b>", st["bold"])

            timing_val = getattr(item, 'dosage', '') or '-'
            dur_val = getattr(item, 'duration', '') or '-'
            dur_translated = dur_map.get(dur_val, dur_val)

            rel_val = getattr(item, 'food_relation', '') or 'After Food'
            rel_translated = food_map.get(rel_val, rel_val)

            inst_val = getattr(item, 'instructions', '') or '-'

            row = [
                P(str(idx)),
                med_name_p,
                P(timing_val),
                P(dur_translated),
                P(rel_translated),
                P(inst_val)
            ]
            if st["is_rtl"]:
                row.reverse()
            rx_data.append(row)

        rx_col_widths = [25, 175, 85, 75, 90, 90]
        if st["is_rtl"]:
            rx_col_widths.reverse()

        rx_table = Table(rx_data, colWidths=rx_col_widths)
        rx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F766E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(rx_table)
        story.append(Spacer(1, 10))

        # 6. Advice / Notes & Follow-up
        if consultation.notes:
            lbl = P(f"<b>{t['advice_notes']}</b>", "bold")
            val = P(consultation.notes, "body")
            notes_row = [val, lbl] if st["is_rtl"] else [lbl, val]
            col_w = [400, 140] if st["is_rtl"] else [140, 400]
            story.append(Table([notes_row], colWidths=col_w, style=[('VALIGN', (0, 0), (-1, -1), 'TOP'), ('PADDING', (0, 0), (-1, -1), 2)]))
            story.append(Spacer(1, 5))

        if consultation.follow_up_date:
            fu_str = consultation.follow_up_date.strftime('%d-%b-%Y') if hasattr(consultation.follow_up_date, 'strftime') else str(consultation.follow_up_date)
            lbl = P(f"<b>{t['follow_up_date']}</b>", "bold")
            val = P(f"<b><font color='#0D9488'>{fu_str}</font></b>", "body")
            fu_row = [val, lbl] if st["is_rtl"] else [lbl, val]
            col_w = [400, 140] if st["is_rtl"] else [140, 400]
            story.append(Table([fu_row], colWidths=col_w, style=[('VALIGN', (0, 0), (-1, -1), 'TOP'), ('PADDING', (0, 0), (-1, -1), 2)]))
            story.append(Spacer(1, 10))

        # 7. Signature Block
        story.append(Spacer(1, 16))
        sig_data = [
            [P(""), P("____________________________________", "right_sub")],
            [P(""), P(f"<b>{doc_name}</b>", "right_title")],
            [P(""), P(f"<font size=8 color='#64748B'>{doc_designation}</font>", "right_sub")],
            [P(""), P(f"<font size=7 color='#0F766E'>{t['doctor_signature']}</font>", "right_sub")],
        ]
        if st["is_rtl"]:
            sig_data = [
                [P("____________________________________", "doc_sub"), P("")],
                [P(f"<b>{doc_name}</b>", "doc_name"), P("")],
                [P(f"<font size=8 color='#64748B'>{doc_designation}</font>", "doc_sub"), P("")],
                [P(f"<font size=7 color='#0F766E'>{t['doctor_signature']}</font>", "doc_sub"), P("")],
            ]
        sig_table = Table(sig_data, colWidths=[270, 270])
        sig_table.setStyle(TableStyle([
            ('PADDING', (0, 0), (-1, -1), 1),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT' if not st["is_rtl"] else 'LEFT'),
        ]))
        story.append(sig_table)

        # 8. Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=12, spaceAfter=4))
        story.append(P(f"<i>{t['footer_disclaimer']}</i>", "footer"))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
