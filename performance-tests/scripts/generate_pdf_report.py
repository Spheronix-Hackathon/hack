"""
PDF Generator: Spheronix Hackathon Registration Service
Scalability & Future Roadmap Blueprint
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import datetime

# ─── Colour Palette ──────────────────────────────────────────────────────────
DARK_BG       = colors.HexColor("#0D1117")
ACCENT_BLUE   = colors.HexColor("#2563EB")
ACCENT_CYAN   = colors.HexColor("#06B6D4")
ACCENT_GREEN  = colors.HexColor("#10B981")
ACCENT_ORANGE = colors.HexColor("#F59E0B")
ACCENT_RED    = colors.HexColor("#EF4444")
LIGHT_GRAY    = colors.HexColor("#F1F5F9")
MID_GRAY      = colors.HexColor("#94A3B8")
DARK_TEXT     = colors.HexColor("#1E293B")
WHITE         = colors.white
SECTION_BG    = colors.HexColor("#EFF6FF")
TABLE_HEADER  = colors.HexColor("#1E40AF")
TABLE_ALT     = colors.HexColor("#F8FAFC")
CODE_BG       = colors.HexColor("#1E293B")
WARN_BG       = colors.HexColor("#FEF3C7")
CRIT_BG       = colors.HexColor("#FEE2E2")
SUCCESS_BG    = colors.HexColor("#D1FAE5")

OUTPUT_PATH = "Spheronix_Hackathon_Scalability_Blueprint.pdf"
PAGE_W, PAGE_H = A4

# ─── Page Number / Header / Footer Canvas ────────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        page_num = self._saved_page_states.index(dict(self.__dict__)) + 1 \
            if dict(self.__dict__) in self._saved_page_states else 1

        # Footer bar
        self.setFillColor(DARK_BG)
        self.rect(0, 0, PAGE_W, 1.1 * cm, fill=1, stroke=0)

        self.setFillColor(WHITE)
        self.setFont("Helvetica", 7)
        self.drawString(1.5 * cm, 0.4 * cm,
            "SPHERONIX HACKATHON REGISTRATION SERVICE  |  SCALABILITY & FUTURE ROADMAP BLUEPRINT")
        self.drawRightString(PAGE_W - 1.5 * cm, 0.4 * cm,
            f"Page {self._pageNumber} of {page_count}")

        # Top accent line
        self.setStrokeColor(ACCENT_BLUE)
        self.setLineWidth(3)
        self.line(0, PAGE_H - 0.4 * cm, PAGE_W, PAGE_H - 0.4 * cm)


# ─── Style Definitions ────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=WHITE,
            leading=36,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            fontName="Helvetica",
            fontSize=14,
            textColor=ACCENT_CYAN,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontName="Helvetica",
            fontSize=10,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=ACCENT_BLUE,
            leading=24,
            spaceBefore=18,
            spaceAfter=6,
            borderPad=6,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=DARK_TEXT,
            leading=18,
            spaceBefore=14,
            spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=ACCENT_BLUE,
            leading=16,
            spaceBefore=10,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=DARK_TEXT,
            leading=15,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=DARK_TEXT,
            leading=14,
            leftIndent=14,
            spaceAfter=3,
            bulletIndent=4,
        ),
        "code": ParagraphStyle(
            "code",
            fontName="Courier",
            fontSize=8,
            textColor=ACCENT_CYAN,
            leading=12,
            leftIndent=10,
            backColor=CODE_BG,
            spaceAfter=2,
            spaceBefore=2,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "label_critical": ParagraphStyle(
            "label_critical",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=ACCENT_RED,
        ),
        "label_high": ParagraphStyle(
            "label_high",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=ACCENT_ORANGE,
        ),
        "label_medium": ParagraphStyle(
            "label_medium",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=ACCENT_GREEN,
        ),
        "toc_h1": ParagraphStyle(
            "toc_h1",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=DARK_TEXT,
            leading=14,
            leftIndent=0,
        ),
        "toc_h2": ParagraphStyle(
            "toc_h2",
            fontName="Helvetica",
            fontSize=9,
            textColor=MID_GRAY,
            leading=13,
            leftIndent=12,
        ),
        "verdict_ready": ParagraphStyle(
            "verdict_ready",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=ACCENT_RED,
            alignment=TA_CENTER,
        ),
    }
    return styles


# ─── Helper Builders ─────────────────────────────────────────────────────────
def S(n=0.25):
    return Spacer(1, n * cm)

def HR(color=ACCENT_BLUE, thickness=1):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=4, spaceBefore=4)

def section_header(text, styles):
    items = []
    items.append(S(0.3))
    items.append(HR(ACCENT_BLUE, 2))
    items.append(Paragraph(text, styles["h1"]))
    items.append(HR(LIGHT_GRAY, 0.5))
    items.append(S(0.1))
    return items

def info_box(title, body_text, bg, styles, title_color=DARK_TEXT):
    data = [[
        Paragraph(f"<b>{title}</b>", ParagraphStyle("bx_t", fontName="Helvetica-Bold",
                  fontSize=9, textColor=title_color, leading=13)),
        Paragraph(body_text, ParagraphStyle("bx_b", fontName="Helvetica", fontSize=9,
                  textColor=DARK_TEXT, leading=13, alignment=TA_JUSTIFY)),
    ]]
    t = Table(data, colWidths=[3.2 * cm, 13.8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4, 4, 4, 4]),
    ]))
    return [t, S(0.2)]

def metric_table(headers, rows, col_widths=None):
    data = [headers] + rows
    if col_widths is None:
        n = len(headers)
        col_widths = [17 * cm / n] * n
    t = Table(data, colWidths=col_widths)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, TABLE_ALT]),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    t.setStyle(TableStyle(style))
    return t


# ─── Cover Page ──────────────────────────────────────────────────────────────
def build_cover(styles):
    items = []

    # Dark background block (simulated with a table)
    cover_data = [[
        Paragraph("SPHERONIX", ParagraphStyle("sp", fontName="Helvetica-Bold",
                  fontSize=11, textColor=ACCENT_CYAN, alignment=TA_CENTER, spaceAfter=2)),
    ]]
    cover_block = Table([[
        Paragraph(
            "<br/><br/><br/>",
            styles["body"]
        )
    ]], colWidths=[17 * cm])

    # Title area
    items.append(S(2.5))

    title_data = [[
        Paragraph("Hackathon Registration Service", styles["cover_title"]),
    ],[
        Paragraph("Scalability &amp; Future Roadmap Blueprint", styles["cover_subtitle"]),
    ],[
        Paragraph("Engineering-Grade Performance Analysis · Architecture Design · Nationwide Deployment Plan",
                  styles["cover_meta"]),
    ]]
    title_table = Table(title_data, colWidths=[17 * cm])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("TOPPADDING", (0, 0), (-1, 0), 30),
        ("TOPPADDING", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 30),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 4),
    ]))
    items.append(title_table)
    items.append(S(0.5))

    # Metrics strip
    kpi_data = [[
        Paragraph("<b>CURRENT\nCAPACITY</b>\n~100 users", ParagraphStyle("kpi",
                  fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT_ORANGE,
                  alignment=TA_CENTER, leading=13)),
        Paragraph("<b>TARGET\nCAPACITY</b>\n30,000 users", ParagraphStyle("kpi2",
                  fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT_GREEN,
                  alignment=TA_CENTER, leading=13)),
        Paragraph("<b>SCALE-UP\nFACTOR</b>\n300×", ParagraphStyle("kpi3",
                  fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT_CYAN,
                  alignment=TA_CENTER, leading=13)),
        Paragraph("<b>PRODUCTION\nREADINESS</b>\nNOT READY", ParagraphStyle("kpi4",
                  fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT_RED,
                  alignment=TA_CENTER, leading=13)),
    ]]
    kpi_table = Table(kpi_data, colWidths=[4.25 * cm] * 4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEAFTER", (0, 0), (2, 0), 0.5, MID_GRAY),
    ]))
    items.append(kpi_table)
    items.append(S(0.5))

    # Meta info
    meta_data = [
        ["Document Type", "Engineering Scalability Blueprint"],
        ["Application", "Spheronix Hackathon Registration Service"],
        ["Analysis Date", "2026-08-11"],
        ["Testing Tool", "k6 Load Testing Framework"],
        ["Target Scale", "30,000 Concurrent Users / 5,000 RPS"],
        ["Status", "NOT READY — Architectural Changes Required"],
    ]
    meta_table = Table(meta_data, colWidths=[5 * cm, 12 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), ACCENT_BLUE),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK_TEXT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_GRAY, WHITE]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
    ]))
    items.append(meta_table)

    items.append(PageBreak())
    return items


# ─── Section 1: Executive Summary ────────────────────────────────────────────
def build_exec_summary(styles):
    items = []
    items += section_header("1. Executive Summary", styles)
    items.append(Paragraph(
        "The Spheronix Hackathon Registration Service is a well-architected FastAPI application "
        "backed by an asynchronous MongoDB driver (Motor). Under minimal load it delivers excellent "
        "baseline performance — p95 response times of <b>50.68 ms</b> at 5 concurrent virtual users. "
        "However, rigorous k6 load testing revealed that the single-node deployment <b>collapses "
        "entirely at approximately 150 concurrent users</b>, producing a 54.22% error rate at 250 VUs "
        "due to TCP connection refusals from the overwhelmed Uvicorn process.",
        styles["body"]
    ))
    items.append(Paragraph(
        "The application's <b>measured sustainable capacity</b> is ~100 concurrent users producing "
        "45–50 RPS. The <b>nationwide deployment target</b> is 30,000 concurrent users requiring a "
        "sustained 5,000 RPS with zero tolerance for downtime during registration deadline events. "
        "This represents a <b>300× gap in concurrency</b> and a <b>100× gap in throughput</b>.",
        styles["body"]
    ))
    items.append(S(0.2))

    # Verdict box
    vdata = [[Paragraph("PRODUCTION READINESS VERDICT", ParagraphStyle(
        "vt", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE, alignment=TA_CENTER)),
    ],[
        Paragraph("NOT READY FOR NATIONWIDE DEPLOYMENT", ParagraphStyle(
        "vv", fontName="Helvetica-Bold", fontSize=20, textColor=ACCENT_RED, alignment=TA_CENTER)),
    ],[
        Paragraph(
            "The application requires fundamental architectural changes before it can serve "
            "30,000 concurrent users. The business logic is correct — the infrastructure must change.",
            ParagraphStyle("vb", fontName="Helvetica", fontSize=9, textColor=WHITE,
                          alignment=TA_CENTER, leading=13)),
    ]]
    vt = Table(vdata, colWidths=[17 * cm])
    vt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
    ]))
    items.append(vt)
    items.append(S(0.3))

    items.append(Paragraph(
        "The path forward is well-defined: <b>offload synchronous blocking operations</b> to "
        "Celery background workers, <b>distribute shared state</b> to Redis, <b>containerise</b> "
        "the application and deploy across a Kubernetes cluster with auto-scaling, and "
        "<b>serve static assets through a CDN</b>. With these changes, the same business logic "
        "will reliably serve 30,000 concurrent users with headroom to spare.",
        styles["body"]
    ))
    return items


# ─── Section 2: Present State ─────────────────────────────────────────────────
def build_present_state(styles):
    items = []
    items += section_header("2. Present State — Architecture & Performance", styles)

    items.append(Paragraph("2.1  Current Architecture", styles["h2"]))
    items.append(Paragraph(
        "The application is a <b>Python FastAPI</b> service running on a single Uvicorn process. "
        "It connects to MongoDB using the Motor async driver. SlowAPI provides in-memory rate "
        "limiting. Static HTML/CSS/JS files are served directly from the FastAPI process via "
        "StaticFiles mount. All operations — file parsing, email delivery, database writes — "
        "execute synchronously within the single async event loop.",
        styles["body"]
    ))

    arch_data = [
        ["Component", "Technology", "Current Status"],
        ["Web Framework", "FastAPI + Uvicorn (single process)", "⚠ Single point of failure"],
        ["Process Manager", "python main.py (no Gunicorn)", "⚠ No multi-worker support"],
        ["Database", "MongoDB (Motor async)", "✓ Well indexed, performs well"],
        ["Rate Limiting", "SlowAPI (in-memory)", "✗ Breaks with multiple instances"],
        ["OTP Storage", "In-memory dict (otp_store)", "✗ Not shareable across instances"],
        ["File Parsing", "Pandas (synchronous, blocking)", "✗ Blocks the event loop"],
        ["Email Delivery", "SMTP (synchronous, blocking)", "✗ Blocks the event loop"],
        ["Image Storage", "Base64 in MongoDB documents", "⚠ Inflates document size"],
        ["Static Assets", "Served by FastAPI (StaticFiles)", "⚠ Wastes application resources"],
        ["Caching", "None", "✗ Every request hits MongoDB"],
        ["Observability", "Basic Uvicorn stdout logs", "⚠ No metrics or alerting"],
    ]
    items.append(metric_table(
        arch_data[0], arch_data[1:],
        col_widths=[4.5 * cm, 6.5 * cm, 6 * cm]
    ))
    items.append(S(0.3))

    items.append(Paragraph("2.2  Measured Performance Results", styles["h2"]))
    items.append(Paragraph(
        "All metrics below were measured using k6 against a locally running Uvicorn instance "
        "connected to a live MongoDB database. No values are estimated.",
        styles["body"]
    ))

    perf_data = [
        ["Metric", "Measured Value", "Assessment"],
        ["Sustainable concurrent users", "~100", "Critical — far below target"],
        ["Sustainable RPS", "~45–50 RPS", "Critical — 100× below target"],
        ["Peak RPS observed", "~60 RPS", "Critical"],
        ["p95 Latency @ 5 VUs (baseline)", "50.68 ms", "✓ Excellent"],
        ["p95 Latency @ 250 VUs (success only)", "35.7 ms", "N/A — 54% failed"],
        ["Error rate @ 250 VUs", "54.22%", "✗ Server failure"],
        ["Excel upload p95 (5 VUs, small file)", "100.73 ms", "⚠ Will worsen at scale"],
        ["Server failure point", "~150 concurrent users", "✗ Critical threshold"],
        ["Max response time observed", "394.76 ms", "⚠ Outliers present"],
    ]
    items.append(metric_table(
        perf_data[0], perf_data[1:],
        col_widths=[6.5 * cm, 4.5 * cm, 6 * cm]
    ))
    items.append(S(0.3))

    items.append(Paragraph("2.3  Identified Bottlenecks", styles["h2"]))

    bottlenecks = [
        ("🔴  CRITICAL", CRIT_BG, ACCENT_RED,
         "Excel/CSV Parsing Blocks Event Loop",
         "pd.read_excel() is synchronous. It occupies the main thread for 200 ms to 5 seconds per "
         "file. During this time no other coroutine can execute — health checks, logins, and "
         "registrations all queue and time out."),
        ("🔴  CRITICAL", CRIT_BG, ACCENT_RED,
         "SMTP Email Delivery is Synchronous",
         "The OTP endpoint waits for the SMTP server to respond before returning. This blocks the "
         "request thread for 1–5 seconds per OTP, limiting throughput to ~0.2 OTP requests per "
         "second per worker under high load."),
        ("🟠  HIGH", WARN_BG, ACCENT_ORANGE,
         "Rate Limiting State is Not Distributed",
         "SlowAPI uses an in-memory counter store. With multiple nodes, each pod maintains "
         "independent counters. A user can exceed rate limits by a factor equal to the number of "
         "pods, and limits cannot be enforced globally."),
        ("🟠  HIGH", WARN_BG, ACCENT_ORANGE,
         "OTP Storage is Not Distributed",
         "OTPs are stored in an in-memory Python dictionary (otp_store). With a load balancer, a "
         "user's OTP verification request may route to a different pod than the one that generated "
         "the OTP, causing all verifications to fail."),
        ("🟡  MEDIUM", SUCCESS_BG, ACCENT_GREEN,
         "Base64 Images Stored in MongoDB",
         "Payment proof images up to 30 KB are stored as Base64 strings directly in registration "
         "documents. This inflates each document by up to 40 KB, slowing bulk reads and "
         "administrative exports significantly at scale."),
        ("🟡  MEDIUM", SUCCESS_BG, ACCENT_GREEN,
         "MongoDB Connection Pool Unconfigured",
         "Motor's default connection pool settings are not tuned for a multi-pod deployment. With "
         "50 pods and 4 workers each, the cluster could attempt 200+ concurrent connections to "
         "MongoDB without explicit pool limits."),
    ]

    for priority, bg, color, title, body in bottlenecks:
        bd = [[
            Paragraph(priority, ParagraphStyle("pr", fontName="Helvetica-Bold", fontSize=8,
                      textColor=color, leading=12)),
            Paragraph(f"<b>{title}</b><br/>{body}",
                      ParagraphStyle("bd", fontName="Helvetica", fontSize=9, textColor=DARK_TEXT,
                                     leading=13, alignment=TA_JUSTIFY)),
        ]]
        bt = Table(bd, colWidths=[2.8 * cm, 14.2 * cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        items.append(bt)
        items.append(S(0.1))

    items.append(S(0.2))

    items.append(Paragraph("2.4  Scalability Gap Analysis", styles["h2"]))
    gap_data = [
        ["Dimension", "Current", "Required", "Gap"],
        ["Concurrent users", "~100", "30,000", "300×"],
        ["Requests per second", "~50 RPS", "5,000 RPS", "100×"],
        ["Failure tolerance", "None (single node)", "Multi-zone HA", "Fundamental redesign"],
        ["Horizontal scaling", "Not possible (stateful)", "Fully stateless", "Architecture change"],
        ["Background processing", "None", "Celery worker fleet", "New component"],
        ["Distributed caching", "None", "Redis cluster", "New component"],
    ]
    items.append(metric_table(
        gap_data[0], gap_data[1:],
        col_widths=[5.5 * cm, 3.5 * cm, 3.5 * cm, 4.5 * cm]
    ))

    return items


# ─── Section 3: Target Architecture ──────────────────────────────────────────
def build_target_arch(styles):
    items = []
    items += section_header("3. Target Architecture for 30,000 Users", styles)

    items.append(Paragraph("3.1  Architecture Layers", styles["h2"]))
    items.append(Paragraph(
        "The target architecture replaces the single Uvicorn process with a six-layer "
        "cloud-native system. Each layer is independently scalable and has no single point of "
        "failure. The layers and their responsibilities are described below.",
        styles["body"]
    ))

    layers = [
        ("Layer 1  —  Edge", ACCENT_BLUE,
         "Cloudflare / AWS CloudFront CDN + WAF",
         "Absorbs 60–70% of all traffic by serving static assets (HTML, CSS, JS, images) from "
         "edge nodes globally. Blocks malicious bots, DDoS attacks, and SQL injection before "
         "they reach the origin."),
        ("Layer 2  —  Load Balancer", ACCENT_BLUE,
         "AWS Application Load Balancer (ALB)",
         "Distributes API traffic across all healthy Kubernetes pods. Performs health checks on "
         "/api/health every 5 seconds. Provides cross-availability-zone redundancy and "
         "connection draining for zero-downtime pod restarts."),
        ("Layer 3  —  Application", ACCENT_BLUE,
         "FastAPI on Kubernetes (5–50 pods, HPA)",
         "Runs stateless FastAPI instances managed by Gunicorn with 4 Uvicorn workers per pod. "
         "Kubernetes HPA automatically scales pods from 5 to 50 based on CPU utilisation. "
         "All shared state is externalised to Redis."),
        ("Layer 4  —  Task Queue", ACCENT_BLUE,
         "Celery Workers + Redis Broker",
         "Processes all CPU-bound and I/O-blocking tasks asynchronously: Excel parsing, email "
         "OTP delivery, PDF generation, and export operations. Workers scale independently "
         "from web pods using KEDA based on queue depth."),
        ("Layer 5  —  Data", ACCENT_BLUE,
         "MongoDB Atlas M40 + Redis Cluster",
         "MongoDB Atlas provides a 3-node replica set with automatic failover, backups, and "
         "monitoring. Redis serves as the shared cache, rate limit store, OTP store, and "
         "Celery broker across all pods."),
        ("Layer 6  —  Storage", ACCENT_BLUE,
         "AWS S3 (Two Buckets)",
         "hackathon-static (public, CDN-served) for frontend assets. hackathon-uploads "
         "(private) for Excel files and payment proof images. Eliminates binary data from "
         "MongoDB documents."),
    ]

    for label, color, tech, desc in layers:
        ld = [[
            Paragraph(label, ParagraphStyle("ll", fontName="Helvetica-Bold", fontSize=9,
                      textColor=WHITE, leading=12, alignment=TA_CENTER)),
            Paragraph(f"<b>{tech}</b><br/><font size=8>{desc}</font>",
                      ParagraphStyle("ld", fontName="Helvetica", fontSize=9, textColor=DARK_TEXT,
                                     leading=13)),
        ]]
        lt = Table(ld, colWidths=[3.5 * cm, 13.5 * cm])
        lt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), color),
            ("BACKGROUND", (1, 0), (1, -1), SECTION_BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, WHITE),
        ]))
        items.append(lt)

    items.append(S(0.3))
    items.append(Paragraph("3.2  Projected Capacity After Full Implementation", styles["h2"]))

    cap_data = [
        ["Pods Active", "Workers / Pod", "Estimated Users", "Estimated Peak RPS", "Scenario"],
        ["5 (minimum)", "4", "~2,000", "~500 RPS", "Off-peak / idle"],
        ["15", "4", "~7,500", "~1,500 RPS", "Normal weekday traffic"],
        ["25", "4", "~12,500", "~2,500 RPS", "Heavy day"],
        ["40", "4", "~25,000", "~4,500 RPS", "Deadline day peak"],
        ["50 (maximum)", "4", "~30,000+", "~5,500 RPS", "Maximum surge"],
    ]
    items.append(metric_table(
        cap_data[0], cap_data[1:],
        col_widths=[3 * cm, 3 * cm, 3.5 * cm, 3.5 * cm, 4 * cm]
    ))

    return items


# ─── Section 4: Implementation Plan ─────────────────────────────────────────
def build_implementation(styles):
    items = []
    items += section_header("4. Implementation Plan — Critical Code Changes", styles)

    items.append(Paragraph("4.1  Excel Upload: Synchronous → Asynchronous", styles["h2"]))
    items.append(Paragraph(
        "The most critical change. Replace the blocking pd.read_excel() call in "
        "/api/dashboard/upload-data with an immediate file save to S3 followed by a Celery "
        "task enqueue. The endpoint returns a 202 Accepted response in ~60 ms instead of "
        "blocking for up to 5 seconds.",
        styles["body"]
    ))

    code_before = [
        ["CURRENT CODE  (blocks event loop)"],
        ["# pd.read_excel() is synchronous — freezes all requests during parse\ndf = pd.read_excel(io.BytesIO(content))\nvalidation_result = ExcelValidator.validate(json_data)"],
    ]
    code_after = [
        ["REQUIRED CODE  (returns in ~60 ms)"],
        ["# Save to S3, enqueue Celery task, return 202 immediately\ns3_key = f'uploads/{user_id}/{uuid.uuid4()}.xlsx'\nawait s3_client.put_object(Bucket='hackathon-uploads', Key=s3_key, Body=content)\ntask = celery_app.send_task('tasks.process_excel', args=[s3_key, user_id])\nreturn JSONResponse(status_code=202, content={'job_id': task.id})"],
    ]
    for cd in [code_before, code_after]:
        label_bg = CRIT_BG if "CURRENT" in cd[0][0] else SUCCESS_BG
        ct = Table(cd, colWidths=[17 * cm])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), label_bg),
            ("BACKGROUND", (0, 1), (-1, -1), CODE_BG),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Courier"),
            ("FONTSIZE", (0, 1), (-1, -1), 7.5),
            ("TEXTCOLOR", (0, 0), (-1, 0), DARK_TEXT),
            ("TEXTCOLOR", (0, 1), (-1, -1), ACCENT_CYAN),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        items.append(ct)
        items.append(S(0.15))

    items.append(Paragraph("4.2  OTP Email: Blocking → Non-Blocking", styles["h2"]))
    items.append(Paragraph(
        "Store OTPs in Redis with a 10-minute TTL and enqueue email delivery as a Celery task. "
        "The endpoint response time drops from 1,000–5,000 ms (SMTP round-trip) to under 10 ms. "
        "This also fixes the horizontal scaling bug where OTPs generated on Pod A are invisible "
        "to Pod B.",
        styles["body"]
    ))

    items.append(Paragraph("4.3  Rate Limiting: In-Memory → Distributed Redis", styles["h2"]))
    code_rl = [
        ["ONE-LINE FIX  (add storage_uri parameter to Limiter)"],
        ["# Before (in-memory — does not work across multiple pods):\nlimiter = Limiter(key_func=get_remote_address)\n\n# After (Redis-backed — enforced globally across all 50 pods):\nlimiter = Limiter(\n    key_func=get_remote_address,\n    storage_uri=settings.redis_url   # e.g. redis://redis-cluster:6379\n)"],
    ]
    ct = Table(code_rl, colWidths=[17 * cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SUCCESS_BG),
        ("BACKGROUND", (0, 1), (-1, -1), CODE_BG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), DARK_TEXT),
        ("TEXTCOLOR", (0, 1), (-1, -1), ACCENT_CYAN),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    items.append(ct)
    items.append(S(0.2))

    items.append(Paragraph("4.4  Payment Proof: Base64 in MongoDB → AWS S3", styles["h2"]))
    items.append(Paragraph(
        "Replace the Base64 encoding and MongoDB storage with an S3 upload, storing only "
        "the S3 object key (a ~60-character string) in the database document. "
        "This keeps MongoDB documents lightweight (under 2 KB) and makes bulk reads and "
        "administrative exports orders of magnitude faster at 30,000 registrations.",
        styles["body"]
    ))

    items.append(Paragraph("4.5  Kubernetes Deployment Configuration", styles["h2"]))
    docker_code = [
        ["Dockerfile — Production Entry Point"],
        ["FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nEXPOSE 8000\nCMD [\"gunicorn\", \"app.main:app\",\n     \"--workers\", \"4\",\n     \"--worker-class\", \"uvicorn.workers.UvicornWorker\",\n     \"--bind\", \"0.0.0.0:8000\",\n     \"--graceful-timeout\", \"30\"]"],
    ]
    ct2 = Table(docker_code, colWidths=[17 * cm])
    ct2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("BACKGROUND", (0, 1), (-1, -1), CODE_BG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("TEXTCOLOR", (0, 1), (-1, -1), ACCENT_CYAN),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    items.append(ct2)

    return items


# ─── Section 5: Future Roadmap ────────────────────────────────────────────────
def build_future_roadmap(styles):
    items = []
    items += section_header("5. Future State & Long-Term Roadmap", styles)

    items.append(Paragraph(
        "Beyond the immediate scaling fix, the following roadmap describes the evolution of "
        "the Spheronix Hackathon Registration Service from its current state through a "
        "production-ready nationwide system and ultimately to a multi-event, multi-tenant "
        "enterprise platform.",
        styles["body"]
    ))
    items.append(S(0.2))

    phases = [
        ("Phase 1  —  Immediate Fixes", "Now → 2 weeks",
         CRIT_BG, ACCENT_RED, [
             "Move OTP storage from in-memory dict to Redis with 10-minute auto-expiring TTL",
             "Implement Celery + Redis for asynchronous background Excel file processing",
             "Implement Celery for non-blocking OTP email delivery via AWS SES",
             "Configure SlowAPI to use a Redis storage backend instead of in-process memory",
             "Add polling endpoint GET /api/jobs/{job_id} for frontend status checks",
             "Containerise the application with Gunicorn + Uvicorn multi-worker configuration",
             "Deploy to Kubernetes (EKS/GKE) with a minimum of 5 pods",
             "Configure Horizontal Pod Autoscaling (HPA) targeting 60% CPU utilisation",
             "Place an AWS Application Load Balancer with health checks in front of the cluster",
         ]),
        ("Phase 2  —  Production Hardening", "2–6 weeks",
         WARN_BG, ACCENT_ORANGE, [
             "Migrate payment proof image storage from MongoDB Base64 to AWS S3",
             "Implement S3 Presigned URL pattern for direct browser-to-S3 Excel uploads",
             "Move the entire static/ directory to S3 and configure CloudFront CDN distribution",
             "Upgrade to MongoDB Atlas M30 or higher with a 3-node replica set",
             "Add missing MongoDB indexes on status and createdAt fields",
             "Configure explicit Motor connection pool limits (maxPoolSize=10 per process)",
             "Set up Prometheus + Grafana for real-time observability and dashboards",
             "Configure Alertmanager with on-call escalation for critical metrics",
             "Implement Redis caching for Hackathon settings fetched from MongoDB (5 min TTL)",
         ]),
        ("Phase 3  —  Resilience & Observability", "6–12 weeks",
         SUCCESS_BG, ACCENT_GREEN, [
             "Deploy KEDA (Kubernetes Event-Driven Autoscaling) for queue-depth-based Celery "
             "worker auto-scaling during upload surges",
             "Implement circuit breakers around AWS SES and all external API dependencies",
             "Set up Sentry for application exception tracking with full stack trace context",
             "Configure Cloudflare WAF rules tailored to the registration application's traffic",
             "Implement a user-visible registration queue with real-time position tracking "
             "to handle thundering-herd deadline events gracefully",
             "Set up centralised log aggregation with Grafana Loki across all pods and workers",
             "Conduct a full 30,000 VU load test against the new production architecture",
             "Implement blue/green or canary deployment strategy via Kubernetes",
             "Add structured JSON logging with correlation IDs for distributed tracing",
         ]),
        ("Phase 4  —  Platform Evolution", "3–6 months",
         SECTION_BG, ACCENT_BLUE, [
             "Multi-event support: allow administrators to create and manage multiple hackathons "
             "from a single platform deployment",
             "Multi-tenancy: support multiple organising institutions with isolated data spaces",
             "Self-service admin portal: allow event coordinators to configure registration "
             "amounts, domains, deadlines, and team constraints without engineering involvement",
             "Real-time dashboard: live registration counts, payment status, and geographic "
             "distribution using WebSockets or Server-Sent Events (SSE)",
             "Advanced analytics: reporting on registration trends, domain popularity, college "
             "participation rates, and payment compliance",
             "API gateway: introduce Kong or AWS API Gateway for centralised authentication, "
             "request transformation, and developer-facing API documentation",
             "Automated certificate generation: background Celery task generates participation "
             "certificates as PDF using ReportLab upon payment confirmation",
             "Bulk import optimisation: streaming Excel parse using openpyxl row-by-row "
             "iteration to handle files exceeding 100,000 rows without memory pressure",
             "CDN-based document delivery: store and serve generated certificates and reports "
             "directly from CloudFront with signed URLs for secure access",
         ]),
        ("Phase 5  —  Enterprise Scale", "6–12 months",
         colors.HexColor("#F3F0FF"), ACCENT_BLUE, [
             "Multi-region deployment: replicate the architecture across multiple AWS regions "
             "(e.g. ap-south-1 Mumbai + ap-south-2 Hyderabad) with latency-based routing",
             "Database sharding: shard the MongoDB registrations collection by state or region "
             "to distribute write load across multiple database shards",
             "GraphQL API layer: add a GraphQL endpoint alongside REST for flexible frontend "
             "querying and reduced over-fetching",
             "Automated infrastructure as code: full Terraform or Pulumi IaC for reproducible "
             "environment provisioning across staging, pre-production, and production",
             "Service mesh: deploy Istio or Linkerd to enforce mutual TLS between all services, "
             "provide automatic circuit breaking, and enable fine-grained traffic management",
             "SIEM integration: stream all security-relevant logs to a Security Information and "
             "Event Management system for compliance and audit requirements",
             "Capacity forecasting: ML-based traffic prediction to pre-warm the cluster 2 hours "
             "before a predicted deadline surge rather than reacting after it begins",
         ]),
    ]

    for phase_title, timeline, bg, color, bullets in phases:
        items.append(S(0.15))
        hd = [[
            Paragraph(phase_title, ParagraphStyle("pt", fontName="Helvetica-Bold", fontSize=10,
                      textColor=color, leading=14)),
            Paragraph(f"Timeline: {timeline}", ParagraphStyle("tl", fontName="Helvetica-Oblique",
                      fontSize=8.5, textColor=MID_GRAY, alignment=TA_LEFT)),
        ]]
        ht = Table(hd, colWidths=[10 * cm, 7 * cm])
        ht.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        items.append(ht)

        bdata = [[Paragraph(f"• {b}", ParagraphStyle("pb", fontName="Helvetica", fontSize=8.5,
                  textColor=DARK_TEXT, leading=13, alignment=TA_JUSTIFY))]
                 for b in bullets]
        bt = Table(bdata, colWidths=[17 * cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LEFTPADDING", (0, 0), (-1, -1), 18),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ]))
        items.append(bt)

    return items


# ─── Section 6: Nationwide Scale Model ───────────────────────────────────────
def build_scale_model(styles):
    items = []
    items += section_header("6. Nationwide Traffic Model", styles)

    items.append(Paragraph("6.1  Traffic Demand Calculation", styles["h2"]))
    demand_data = [
        ["Parameter", "Value", "Basis"],
        ["Total eligible colleges in India", "~50,000", "Government + private engineering colleges"],
        ["Expected registrations", "~30,000", "60% adoption rate assumption"],
        ["Daily active users (normal period)", "~5,000", "~17% of registered users active daily"],
        ["Peak-hour users on deadline day", "~30,000", "All remaining institutions rush simultaneously"],
        ["Requests per active user per minute", "3–5", "Dashboard, upload, payment actions"],
        ["Required peak RPS (minimum)", "1,500–2,500 RPS", "30,000 users × 3 req/min ÷ 60"],
        ["Required peak RPS with 2× safety margin", "5,000 RPS", "Recommended design target"],
    ]
    items.append(metric_table(demand_data[0], demand_data[1:],
                              col_widths=[5.5 * cm, 4.5 * cm, 7 * cm]))
    items.append(S(0.3))

    items.append(Paragraph("6.2  Registration Deadline Day Timeline", styles["h2"]))
    items.append(Paragraph(
        "The most dangerous traffic event is not a gradual increase but the last-minute "
        "deadline rush. The following timeline shows how the auto-scaling system responds:",
        styles["body"]
    ))

    timeline_data = [
        ["Time", "Concurrent Users", "Active Pods", "System State"],
        ["10:00 AM", "~500", "5", "Normal. CPU 20%. Off-peak."],
        ["2:00 PM", "~3,000", "15", "HPA triggers. Scaling starts."],
        ["5:00 PM", "~12,000", "25", "Heavy traffic. Redis absorbing all OTPs and rate limits."],
        ["10:00 PM", "~22,000", "40", "Near peak. Celery workers processing Excel backlog."],
        ["11:45 PM", "~30,000", "50", "Maximum load. All SLOs maintained."],
        ["12:00 AM", "~1,000", "5 (scaling down)", "Deadline passed. HPA scales back within 10 min."],
    ]
    items.append(metric_table(timeline_data[0], timeline_data[1:],
                              col_widths=[2.8 * cm, 3.5 * cm, 2.8 * cm, 7.9 * cm]))
    items.append(S(0.3))

    items.append(Paragraph("6.3  Cost Estimation", styles["h2"]))
    cost_data = [
        ["Component", "AWS Service", "Est. Monthly Cost (USD)"],
        ["Kubernetes cluster", "AWS EKS (control plane)", "~$73"],
        ["Application pods (5–50)", "EC2 t3.large on-demand", "$300–$1,500"],
        ["Celery worker pods (2–20)", "EC2 t3.medium on-demand", "$80–$400"],
        ["Load Balancer", "AWS ALB", "$25–$100"],
        ["MongoDB database", "MongoDB Atlas M40 tier", "~$240"],
        ["Redis cache cluster", "AWS ElastiCache r6g.large", "~$180"],
        ["Object storage", "AWS S3 (uploads + static)", "$30–$100"],
        ["Content Delivery Network", "AWS CloudFront", "$50–$200"],
        ["Email delivery", "AWS SES", "~$10 / 100,000 emails"],
        ["Observability", "Grafana Cloud free tier", "$0–$50"],
        ["TOTAL (off-peak / baseline)", "", "~$900/month"],
        ["TOTAL (during registration window)", "", "~$2,500/month"],
    ]
    t = metric_table(cost_data[0], cost_data[1:],
                     col_widths=[5.5 * cm, 5.5 * cm, 6 * cm])
    items.append(t)

    return items


# ─── Section 7: Edge Cases ───────────────────────────────────────────────────
def build_edge_cases(styles):
    items = []
    items += section_header("7. Scalability Considerations & Edge Cases", styles)

    cases = [
        ("Thundering Herd at Deadline",
         "When thousands of colleges attempt registration in the final minutes simultaneously, "
         "every system layer receives maximum load at once. Without mitigation, this causes "
         "resource exhaustion faster than auto-scaling can respond.\n\n"
         "Mitigations: Implement a visible queue with position tracking. Pre-warm the cluster "
         "to 30 pods 2 hours before the deadline. Apply Cloudflare Under Attack Mode to "
         "challenge suspicious volumetric traffic during deadline hours."),
        ("OTP Distributed Race Condition",
         "Currently, if Pod A generates an OTP and stores it in its in-memory dict, but the "
         "user's subsequent verification request routes to Pod B, the verification fails "
         "because Pod B's dict has no record of the OTP. This will affect every user on "
         "multi-pod deployments.\n\n"
         "Fix: Move all OTP storage to Redis immediately (Phase 1 item)."),
        ("Database Write Contention",
         "MongoDB enforces uniqueness across 7 fields in nodal_registrations. Under "
         "simultaneous high-concurrency inserts, each write requires checking all 7 unique "
         "indexes, creating contention.\n\n"
         "Mitigation: The index strategy is correct. Upgrade to MongoDB Atlas M40+ for "
         "adequate IOPS. Return clear, user-friendly error messages on constraint violations."),
        ("Celery Worker Backlog",
         "If 5,000 colleges upload Excel files within one hour, thousands of tasks queue "
         "in Redis. A fixed number of Celery workers will process these at a fixed rate, "
         "creating a growing backlog and poor user experience.\n\n"
         "Mitigation: Deploy KEDA on Kubernetes to auto-scale Celery workers based on Redis "
         "queue depth. Scale from 2 to 50 worker pods within 30 seconds of a queue surge."),
        ("External Dependency Failures",
         "AWS SES, the MongoDB Atlas connection, or Redis can experience temporary "
         "unavailability. Without protection, a slow external service causes cascading failures "
         "propagating back to the user-facing API.\n\n"
         "Mitigation: Implement circuit breakers (circuitbreaker Python library) around all "
         "external calls. Celery tasks auto-retry with exponential backoff up to 3 attempts."),
        ("Memory Leak Under Soak",
         "Long-running soak tests (30+ minutes) can reveal memory leaks in async Python "
         "applications, particularly in large object accumulation within coroutine closures "
         "or in Motor's connection pool under sustained load.\n\n"
         "Mitigation: Run a 1-hour soak test against the new architecture. Monitor RSS memory "
         "per pod via Prometheus. Configure pod memory limits and restart policies."),
    ]

    for title, body in cases:
        bd = [[
            Paragraph(f"<b>{title}</b>", ParagraphStyle("ct", fontName="Helvetica-Bold",
                      fontSize=9.5, textColor=ACCENT_BLUE, leading=14)),
        ],[
            Paragraph(body.replace("\n\n", "<br/><br/>"),
                      ParagraphStyle("cb", fontName="Helvetica", fontSize=9, textColor=DARK_TEXT,
                                     leading=13, alignment=TA_JUSTIFY)),
        ]]
        bt = Table(bd, colWidths=[17 * cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SECTION_BG),
            ("BACKGROUND", (0, 1), (-1, 1), WHITE),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        items.append(bt)
        items.append(S(0.15))

    return items


# ─── Section 8: Final Verdict ─────────────────────────────────────────────────
def build_final_verdict(styles):
    items = []
    items += section_header("8. Final Verdict & Prioritised Action Plan", styles)

    items.append(Paragraph("8.1  Engineering Verdict", styles["h2"]))

    verdict_data = [
        ["Verdict Item", "Value"],
        ["Current sustainable capacity", "~100 concurrent users / ~50 RPS"],
        ["Recommended safe operating capacity (after Phase 1 fixes)", "~2,000 users / ~500 RPS (5 pods)"],
        ["Maximum capacity after full implementation", "~30,000+ users / ~5,500 RPS (50 pods)"],
        ["Primary bottleneck", "Excel parsing blocks the async event loop (synchronous Pandas)"],
        ["Secondary bottleneck", "Synchronous SMTP OTP delivery / In-memory rate limiting"],
        ["Critical broken feature (multi-node)", "In-memory OTP storage fails with multiple pods"],
        ["Production readiness — current", "NOT READY"],
        ["Production readiness — after Phase 1 + Phase 2", "READY WITH CONDITIONS"],
        ["Production readiness — after Phase 3", "FULLY READY"],
    ]
    t = metric_table(verdict_data[0], verdict_data[1:],
                     col_widths=[8 * cm, 9 * cm])
    items.append(t)
    items.append(S(0.3))

    items.append(Paragraph("8.2  Prioritised Action Checklist", styles["h2"]))

    phase1 = [
        "Move OTP storage from in-memory otp_store to Redis with 10-minute TTL",
        "Implement Celery + Redis for asynchronous background Excel file processing",
        "Implement Celery for non-blocking OTP email delivery",
        "Configure SlowAPI to use Redis storage backend",
        "Add GET /api/jobs/{job_id} polling endpoint for frontend status checks",
        "Containerise with Gunicorn + 4 Uvicorn workers per pod",
        "Deploy to Kubernetes with minimum 5 pods and HPA targeting 60% CPU",
        "Place AWS Application Load Balancer in front of the cluster",
    ]
    phase2 = [
        "Migrate payment proof images from MongoDB Base64 to AWS S3",
        "Implement S3 Presigned URL pattern for direct browser-to-S3 Excel uploads",
        "Move static/ to S3 and configure CloudFront CDN distribution",
        "Upgrade to MongoDB Atlas M40 with 3-node replica set",
        "Add missing MongoDB indexes on status and createdAt fields",
        "Configure Motor connection pool: maxPoolSize=10 per process",
        "Set up Prometheus + Grafana + Alertmanager observability stack",
    ]
    phase3 = [
        "Deploy KEDA for queue-depth-based Celery worker auto-scaling",
        "Implement circuit breakers around all external API dependencies",
        "Set up Sentry for exception tracking",
        "Configure Cloudflare WAF rules for the application",
        "Implement user-visible registration queue for deadline events",
        "Set up Grafana Loki for centralised log aggregation",
        "Conduct full 30,000 VU load test against the new architecture",
    ]

    for phase_label, phase_color, checklist in [
        ("Phase 1 — Critical Prerequisites (2 weeks)", ACCENT_RED, phase1),
        ("Phase 2 — Production Hardening (6 weeks)", ACCENT_ORANGE, phase2),
        ("Phase 3 — Resilience & Observability (12 weeks)", ACCENT_GREEN, phase3),
    ]:
        items.append(S(0.15))
        items.append(Paragraph(phase_label, ParagraphStyle("ph", fontName="Helvetica-Bold",
                    fontSize=10, textColor=phase_color, leading=14, spaceBefore=6)))
        for item in checklist:
            items.append(Paragraph(f"☐  {item}", styles["bullet"]))

    items.append(S(0.4))

    # Closing statement
    close_data = [[
        Paragraph(
            "The Spheronix Hackathon Registration Service has well-structured, correct business logic. "
            "By resolving the four architectural issues identified in this report — synchronous Excel processing, "
            "synchronous email delivery, in-memory shared state, and single-node deployment — the same "
            "application codebase will reliably serve 30,000 concurrent users with automatic failover, "
            "auto-scaling, and full engineering observability.",
            ParagraphStyle("cl", fontName="Helvetica", fontSize=9.5, textColor=WHITE,
                           leading=15, alignment=TA_JUSTIFY)),
    ]]
    ct = Table(close_data, colWidths=[17 * cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    items.append(ct)

    return items


# ─── Main Build ───────────────────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
        title="Spheronix Hackathon Scalability Blueprint",
        author="Performance Engineering Team",
        subject="30,000 User Scalability Architecture",
    )

    styles = build_styles()
    story = []

    story += build_cover(styles)
    story += build_exec_summary(styles)
    story.append(PageBreak())
    story += build_present_state(styles)
    story.append(PageBreak())
    story += build_target_arch(styles)
    story.append(PageBreak())
    story += build_implementation(styles)
    story.append(PageBreak())
    story += build_future_roadmap(styles)
    story.append(PageBreak())
    story += build_scale_model(styles)
    story.append(PageBreak())
    story += build_edge_cases(styles)
    story.append(PageBreak())
    story += build_final_verdict(styles)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"\nPDF successfully generated: {OUTPUT_PATH}\n")


if __name__ == "__main__":
    build_pdf()
