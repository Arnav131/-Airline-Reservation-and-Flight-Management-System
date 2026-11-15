"""
Master PPTX Project Report Generator for IARFMS DBMS Project.
Generates an A4 portrait-mode presentation matching the 33-page academic report,
with updated university logos (Chandigarh University & NAAC A+),
native cover page, and customized student details for Arnav Prajapati (24BAI70131).
"""
import io
import os
import fitz  # PyMuPDF
from PIL import Image
import pptx
from pptx import Presentation
from pptx.util import Inches, Mm, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

PDF_PATH = r"C:\Users\arnav\Downloads\IARFMS_Project_Report.pdf"
LOGO_CU_PATH = r"C:\Users\arnav\.gemini\antigravity\brain\e917d5fc-b0ad-4d2c-bbb9-42f6f9414373\.user_uploaded\media_1794727912966_c4e59e29.png"
LOGO_NAAC_PATH = r"C:\Users\arnav\.gemini\antigravity\brain\e917d5fc-b0ad-4d2c-bbb9-42f6f9414373\.user_uploaded\media_1794727919758_c69c1d9a.png"
LOGO_CU_VERT_PATH = r"C:\Users\arnav\.gemini\antigravity\brain\e917d5fc-b0ad-4d2c-bbb9-42f6f9414373\.user_uploaded\media_1794727899710_2e376ad5.jpg"

OUTPUT_PPTX_PROJECT = r"d:\ML_PROJECTS\DBMS_PROJECT\IARFMS_Project_Report.pptx"
OUTPUT_PPTX_DOWNLOADS = r"C:\Users\arnav\Downloads\IARFMS_Project_Report.pptx"


def build_cover_slide(prs):
    """Build a native, high-precision A4 portrait cover slide."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # A4 dimensions in Mm: 210 x 297
    slide_w_mm = 210
    slide_h_mm = 297

    # 1. Outer Border Box (5mm margin)
    border = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Mm(10), Mm(10), Mm(slide_w_mm - 20), Mm(slide_h_mm - 20)
    )
    border.fill.background()
    border.line.color.rgb = RGBColor(40, 40, 40)
    border.line.width = Pt(1.5)

    # 2. Main Title Text Box
    tx_box = slide.shapes.add_textbox(Mm(15), Mm(16), Mm(slide_w_mm - 30), Mm(95))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    def add_p(text, font_size, bold=False, space_after=6, space_before=0, color=RGBColor(0, 0, 0)):
        p = tf.add_paragraph() if tf.paragraphs and tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = text
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Times New Roman"
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.font.color.rgb = color
        p.space_after = Pt(space_after)
        p.space_before = Pt(space_before)
        return p

    add_p("PROJECT REPORT", 24, bold=True, space_after=14)
    add_p("Industry Based Case Study Assignment", 15, bold=True, space_after=10)
    add_p("GROUP 4 – Airline Reservation and Flight Management System", 14, bold=True, space_after=2)
    add_p("(IARFMS)", 14, bold=True, space_after=18)

    add_p("BACHELOR OF ENGINEERING", 13, bold=True, space_after=3)
    add_p("IN", 11, bold=True, space_after=3)
    add_p("Computer Science", 13, bold=True, space_after=2)
    add_p("(AI-ML)", 13, bold=True, space_after=18)

    add_p("Subject: Advanced Database Management Systems (ADBMS)", 13, bold=True, space_after=0)

    # 3. Submitted by Box
    sub_box = slide.shapes.add_textbox(Mm(15), Mm(118), Mm(slide_w_mm - 30), Mm(42))
    stf = sub_box.text_frame
    stf.word_wrap = True
    stf.margin_left = stf.margin_right = stf.margin_top = stf.margin_bottom = 0

    p_sub = stf.paragraphs[0]
    p_sub.text = "Submitted by:"
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.font.name = "Times New Roman"
    p_sub.font.size = Pt(14)
    p_sub.font.bold = True
    p_sub.space_after = Pt(6)

    p_name1 = stf.add_paragraph()
    p_name1.text = "Arnav Prajapati (24BAI70131)"
    p_name1.alignment = PP_ALIGN.CENTER
    p_name1.font.name = "Times New Roman"
    p_name1.font.size = Pt(13)
    p_name1.font.bold = True
    p_name1.space_after = Pt(3)

    p_name2 = stf.add_paragraph()
    p_name2.text = "Sahil Panwar (Group 4 - Section 5)"
    p_name2.alignment = PP_ALIGN.CENTER
    p_name2.font.name = "Times New Roman"
    p_name2.font.size = Pt(12)
    p_name2.space_after = Pt(3)

    p_grp = stf.add_paragraph()
    p_grp.text = "Group Contributors: Abhinav (24BAI70143), Diksha (24BAI70140)"
    p_grp.alignment = PP_ALIGN.CENTER
    p_grp.font.name = "Times New Roman"
    p_grp.font.size = Pt(10)
    p_grp.font.color.rgb = RGBColor(100, 100, 100)

    # 4. Under Guidance Box
    guide_box = slide.shapes.add_textbox(Mm(15), Mm(166), Mm(slide_w_mm - 30), Mm(32))
    gtf = guide_box.text_frame
    gtf.word_wrap = True
    gtf.margin_left = gtf.margin_right = gtf.margin_top = gtf.margin_bottom = 0

    p_gtitle = gtf.paragraphs[0]
    p_gtitle.text = "Under the Guidance of"
    p_gtitle.alignment = PP_ALIGN.CENTER
    p_gtitle.font.name = "Times New Roman"
    p_gtitle.font.size = Pt(13)
    p_gtitle.font.bold = True
    p_gtitle.space_after = Pt(5)

    p_gname = gtf.add_paragraph()
    p_gname.text = "Mr. Anand Sharma"
    p_gname.alignment = PP_ALIGN.CENTER
    p_gname.font.name = "Times New Roman"
    p_gname.font.size = Pt(13)
    p_gname.font.bold = True
    p_gname.space_after = Pt(3)

    p_gdept = gtf.add_paragraph()
    p_gdept.text = "Dept.- AIT-CSE"
    p_gdept.alignment = PP_ALIGN.CENTER
    p_gdept.font.name = "Times New Roman"
    p_gdept.font.size = Pt(12)

    # 5. University Logos (CU Logo + NAAC A+ Logo side-by-side)
    # CU Logo (horizontal emblem with tagline)
    if os.path.exists(LOGO_CU_PATH):
        slide.shapes.add_picture(LOGO_CU_PATH, Mm(38), Mm(206), width=Mm(72))
    elif os.path.exists(LOGO_CU_VERT_PATH):
        slide.shapes.add_picture(LOGO_CU_VERT_PATH, Mm(45), Mm(206), height=Mm(38))

    # NAAC Logo
    if os.path.exists(LOGO_NAAC_PATH):
        slide.shapes.add_picture(LOGO_NAAC_PATH, Mm(120), Mm(206), width=Mm(52))

    # 6. University Title Text
    uni_box = slide.shapes.add_textbox(Mm(15), Mm(252), Mm(slide_w_mm - 30), Mm(15))
    utf = uni_box.text_frame
    utf.word_wrap = True
    p_uni = utf.paragraphs[0]
    p_uni.text = "Chandigarh University"
    p_uni.alignment = PP_ALIGN.CENTER
    p_uni.font.name = "Times New Roman"
    p_uni.font.size = Pt(15)
    p_uni.font.bold = True

    # Page 1 indicator
    pg_box = slide.shapes.add_textbox(Mm(15), Mm(275), Mm(slide_w_mm - 30), Mm(10))
    ptf = pg_box.text_frame
    p_pg = ptf.paragraphs[0]
    p_pg.text = "1"
    p_pg.alignment = PP_ALIGN.CENTER
    p_pg.font.name = "Times New Roman"
    p_pg.font.size = Pt(11)


def generate_full_presentation():
    print(f"Opening reference report: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"Found {total_pages} total pages in PDF.")

    prs = Presentation()
    # Set exact A4 portrait dimensions
    prs.slide_width = Mm(210)
    prs.slide_height = Mm(297)

    # Slide 1: High-Resolution Native Cover Page
    print("Generating Slide 1: University Cover Page with official CU & NAAC logos...")
    build_cover_slide(prs)

    # Slides 2 to 33: High-Resolution A4 Portrait Pages with Updated Running Footer
    blank_layout = prs.slide_layouts[6]

    for page_idx in range(1, total_pages):
        page_num = page_idx + 1
        page = doc[page_idx]

        # Redact existing footer containing "Abhinav & Diksha"
        # Footer bounding region across all pages: y: 790 to 812 pt
        page.add_redact_annot(fitz.Rect(140, 788, 470, 812), fill=(1, 1, 1))
        page.apply_redactions()

        # Insert updated, centered footer text
        new_footer = f"IARFMS – Group 4 | Arnav Prajapati (24BAI70131) | Page {page_num}"
        text_w = fitz.get_text_length(new_footer, fontname="helv", fontsize=9)
        start_x = (595.3 - text_w) / 2.0
        page.insert_text(fitz.Point(start_x, 802.5), new_footer, fontsize=9, fontname="helv", color=(0.18, 0.18, 0.18))

        # Render page at 220 DPI for high print clarity
        pix = page.get_pixmap(dpi=220)
        img_bytes = pix.tobytes("png")
        image_stream = io.BytesIO(img_bytes)

        # Add Slide in PPTX
        slide = prs.slides.add_slide(blank_layout)
        # Place full bleed on A4 slide
        slide.shapes.add_picture(image_stream, 0, 0, width=Mm(210), height=Mm(297))

        if page_num % 5 == 0 or page_num == total_pages:
            print(f"Rendered Slide {page_num}/{total_pages} ...")

    # Save to project folder and downloads
    prs.save(OUTPUT_PPTX_PROJECT)
    print(f"✅ Saved project report PPTX to: {OUTPUT_PPTX_PROJECT}")

    try:
        prs.save(OUTPUT_PPTX_DOWNLOADS)
        print(f"✅ Saved copy to Downloads: {OUTPUT_PPTX_DOWNLOADS}")
    except Exception as exc:
        print(f"Note: Could not write to Downloads ({exc})")


if __name__ == "__main__":
    generate_full_presentation()
