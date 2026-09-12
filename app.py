import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import tempfile
import os
import subprocess
import datetime

from enf_core import extract_enf, find_best_match, detect_jump
import db

st.set_page_config(page_title="سَبْر | Sabr", page_icon="🔎", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Tajawal:wght@400;500;700;800&display=swap');

    :root{
        --bg-0:#050a16; --panel:#0c1a33; --panel-2:#10213f;
        --blue:#1f5fc4; --blue-bright:#4d8dff; --blue-soft:#2a3f66;
        --purple:#7c5cff; --purple-soft:#9b7bff;
        --text:#eef2fa; --text-dim:#8ea0c2;
        --border:rgba(255,255,255,0.09);
        --glow: 0 0 40px rgba(124,92,255,0.18);
    }

    html, body, [class*="css"] { font-family: 'Tajawal', 'Inter', sans-serif; font-size: 12px; }

    .stApp{
        background:
            radial-gradient(ellipse 60% 40% at 20% 0%, rgba(124,92,255,0.18), transparent 60%),
            radial-gradient(ellipse 50% 40% at 85% 15%, rgba(77,141,255,0.16), transparent 55%),
            radial-gradient(ellipse 70% 50% at 50% 100%, rgba(31,95,196,0.10), transparent 60%),
            var(--bg-0);
    }

    .block-container{ max-width: 1400px; padding-top: 0.6rem; padding-bottom: 0.4rem; padding-left: 1.4rem; padding-right: 1.4rem; }

    h1, h2, h3, p, label, .stMarkdown, span { color: var(--text) !important; }

    /* hero title */
    .sabr-hero{ text-align:center; padding: 4px 0 4px; position:relative; }
    .sabr-hero h1{
        font-size: 22px; font-weight:800; margin:0; letter-spacing:0.3px; display:inline;
        background: linear-gradient(90deg, #ffffff 8%, var(--blue-bright) 50%, var(--purple-soft) 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent !important;
    }
    .sabr-hero p{ color: var(--text-dim) !important; font-size:10.5px; display:inline; margin-right:8px; }
    .sabr-hero .tag{ display:none; }

    /* card-style bordered containers */
    div[data-testid="stVerticalBlockBorderWrapper"]{
        background: linear-gradient(165deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015));
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        padding: 8px 10px !important;
        box-shadow: 0 8px 18px rgba(0,0,0,0.28);
        backdrop-filter: blur(10px);
        margin-bottom: 6px !important;
    }
    /* tighten default Streamlit gaps between stacked elements */
    div[data-testid="stVerticalBlock"]{ gap: 0.3rem !important; }
    div[data-testid="element-container"]{ margin-bottom: 0 !important; }

    /* stat / metric cards */
    div[data-testid="stMetric"]{
        background: linear-gradient(165deg, rgba(124,92,255,0.10), rgba(77,141,255,0.04));
        border: 1px solid rgba(124,92,255,0.22);
        border-radius: 10px;
        padding: 5px 10px !important;
        min-height: unset !important;
    }
    div[data-testid="stMetricLabel"]{ color: var(--text-dim) !important; font-size: 9.5px !important; line-height:1.2 !important; }
    div[data-testid="stMetricValue"]{
        color: var(--text) !important; font-weight:800 !important; line-height:1.2 !important;
        font-size: 15px !important;
        background: linear-gradient(90deg, var(--blue-bright), var(--purple-soft));
        -webkit-background-clip: text; background-clip: text; color: transparent !important;
    }
    div[data-testid="stMetricDelta"]{ display:none !important; }

    /* alerts — unify to match dark theme instead of default bright colors */
    div[data-testid="stAlert"]{
        border-radius: 10px !important; backdrop-filter: blur(6px);
        background: rgba(255,255,255,0.045) !important;
        border: 1px solid var(--border) !important;
        padding: 6px 10px !important; font-size: 10.5px !important;
    }
    div[data-testid="stAlert"] p{ color: var(--text) !important; font-size: 10.5px !important; }
    div[data-testid="stAlert"] svg{ display:none; }

    /* section headers with accent bar */
    h3{ position:relative; padding-right:10px !important; font-size:11.5px !important; margin:2px 0 !important; }
    h3::before{
        content:''; position:absolute; right:0; top:4px; bottom:4px; width:4px;
        border-radius:4px; background: linear-gradient(180deg, var(--blue-bright), var(--purple));
    }

    /* buttons */
    .stButton>button{
        background: linear-gradient(90deg, var(--blue), var(--purple));
        color: #fff; border: none; border-radius: 8px;
        padding: 0.3rem 0.9rem; font-weight:700; letter-spacing:0.2px; font-size:11px !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        box-shadow: 0 4px 10px rgba(124,92,255,0.28);
    }
    .stButton>button:hover{ transform: translateY(-1px); }
    .stButton>button:active{ transform: translateY(0px); }
    .stButton>button:disabled{ background:#2a3f66; box-shadow:none; opacity:0.6; }

    /* file uploader — compact, dropzone height is a hard Streamlit floor */
    [data-testid="stFileUploaderDropzone"]{
        background: rgba(255,255,255,0.025) !important;
        border: 1.5px dashed var(--blue-soft) !important;
        border-radius: 10px !important;
        padding: 2px 6px !important;
        min-height: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] button{ font-size:10px !important; padding:0.2rem 0.6rem !important; }
    [data-testid="stFileUploaderDropzoneInstructions"] span{ font-size:10px !important; }
    [data-testid="stFileUploaderDropzone"]:hover{ border-color: var(--purple-soft) !important; }
    [data-testid="stFileUploaderFile"]{ font-size:10px !important; padding:2px 4px !important; }

    /* inputs */
    input, .stDateInput input, .stTimeInput input, [data-baseweb="select"] *{
        background: rgba(255,255,255,0.045) !important;
        border-radius: 8px !important; color: var(--text) !important;
        border: 1px solid var(--border) !important;
        font-size: 11px !important; padding: 0.25rem 0.5rem !important;
    }
    .stSelectbox label, .stDateInput label, .stTimeInput label{ font-size:10px !important; }

    hr{ border-color: var(--border) !important; margin:4px 0 !important; }

    ::-webkit-scrollbar{ width:6px; }
    ::-webkit-scrollbar-thumb{ background: var(--blue-soft); border-radius:8px; }

    /* force column stacking only on true phone widths — keep the dense
       grid intact on iPad so everything still fits one screen there */
    @media (max-width: 560px){
        div[data-testid="stHorizontalBlock"]{
            flex-direction: column !important;
            gap: 6px !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{
            width: 100% !important;
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }
    /* sidebar styling to match the dark glass theme */
    section[data-testid="stSidebar"]{
        background: linear-gradient(180deg, #071022, #050a16) !important;
        border-left: 1px solid var(--border);
        width: 190px !important;
    }
    section[data-testid="stSidebar"] .sabr-side-logo{
        font-size: 20px; font-weight:800; text-align:center; margin-top:2px;
        background: linear-gradient(90deg, #ffffff 10%, var(--blue-bright) 55%, var(--purple-soft) 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent !important;
    }
    section[data-testid="stSidebar"] .sabr-side-tag{
        text-align:center; font-size:9px; color:var(--text-dim) !important; margin-bottom:8px;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"]{ gap: 0.25rem !important; }

    /* overview accent hero card */
    .sabr-accent-card{
        border-radius: 12px; padding: 8px 14px;
        background: linear-gradient(120deg, var(--blue) 0%, var(--purple) 100%);
        box-shadow: 0 8px 18px rgba(124,92,255,0.26);
        margin-bottom: 6px;
        display:flex; align-items:center; gap:10px; flex-wrap:wrap;
    }
    .sabr-accent-card h4{ margin:0; font-size:12px; color:#fff !important; font-weight:800; white-space:nowrap; }
    .sabr-accent-card p{ margin:0; color:rgba(255,255,255,0.88) !important; font-size:10px; line-height:1.4; }

    /* recent log table */
    div[data-testid="stDataFrame"]{ border-radius: 10px; overflow:hidden; border:1px solid var(--border); }

    /* mini stat card with sparkline / gauge */
    .sabr-mini-card{
        border-radius: 10px; padding: 6px 10px;
        background: linear-gradient(165deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015));
        border: 1px solid var(--border);
        margin-bottom: 5px;
    }
    .sabr-mini-card .lbl{ font-size:9px; color:var(--text-dim); margin-bottom:1px; }
    .sabr-mini-card .val{ font-size:13px; font-weight:800; color:var(--text); }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div class="sabr-side-logo">سَبْر</div>
        <div class="sabr-side-tag">ENF · التحقق من الأدلة الرقمية</div>
        """,
        unsafe_allow_html=True,
    )
    total_points = db.archive_count()
    oldest, newest = db.archive_time_range()
    if total_points > 0:
        span_label = f"{oldest.strftime('%m-%d %H:%M')} → {newest.strftime('%m-%d %H:%M')}"
    else:
        span_label = "لا يوجد بعد"
    st.caption("نموذج أولي يثبت المبدأ العلمي — وليس نظامًا معتمدًا رسميًا للاستخدام القضائي الفعلي بعد.")

db_ready = True


def make_sparkline(values):
    fig = go.Figure(go.Scatter(
        y=values, mode="lines",
        line=dict(color="#4d8dff", width=1.5),
        fill="tozeroy", fillcolor="rgba(77,141,255,0.14)",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), height=30,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def make_gauge(percent):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percent,
        number={"suffix": "%", "font": {"size": 16, "color": "#eef2fa"}},
        gauge={
            "axis": {"range": [0, 100], "visible": False},
            "bar": {"color": "#4d8dff"},
            "bgcolor": "rgba(255,255,255,0.06)",
            "borderwidth": 0,
        },
    ))
    fig.update_layout(
        margin=dict(l=6, r=6, t=6, b=6), height=80,
        paper_bgcolor="rgba(0,0,0,0)", font={"color": "#eef2fa"},
    )
    return fig


def run_verification_flow(key_prefix):
    """منطق تحليل تسجيل والتحقق منه — دالة مشتركة تُستخدم من بطاقة
    التحقق السريع بالنظرة العامة، ومن تبويب التحقق الكامل، لتفادي تكرار
    الكود بمكانين."""
    suspect_file = st.file_uploader(
        "فيديو أو ملف صوتي للتحقق (mp4/wav/mp3)",
        type=["mp4", "wav", "mp3", "m4a"],
        key=f"suspect_{key_prefix}",
    )

    if suspect_file is not None and st.button("تحليل والتحقق من الأرشيف الدائم", key=f"btn_{key_prefix}", disabled=not db_ready):
        archive_times, archive_freqs = db.load_reference_archive()

        if len(archive_freqs) == 0:
            st.error("الأرشيف المرجعي فارغ — أضيفي تسجيلًا مرجعيًا أولًا بتبويب الأرشيف المرجعي.")
            return

        suffix = "." + suspect_file.name.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(suspect_file.read())
            raw_path = tmp.name

        audio_path = raw_path + "_converted.wav"
        convert_result = subprocess.run(
            ["ffmpeg", "-y", "-i", raw_path, "-ar", "16000", "-ac", "1", "-vn", audio_path],
            capture_output=True,
        )

        if convert_result.returncode != 0 or not os.path.exists(audio_path):
            st.error("تعذّر تحويل الملف المرفوع. تأكدي أن الملف سليم وغير تالف.")
            with st.expander("تفاصيل الخطأ التقنية"):
                st.code(convert_result.stderr.decode(errors="ignore")[-1500:])
            os.unlink(raw_path)
            return

        with st.spinner("جاري استخراج بصمة ENF ومقارنتها بالأرشيف الدائم..."):
            q_times, q_freqs = extract_enf(audio_path)

        st.line_chart(pd.DataFrame({"التردد (هرتز)": q_freqs}), height=110)

        jump_idx = detect_jump(q_freqs)

        if jump_idx is None:
            best_i, confidence = find_best_match(archive_times, archive_freqs, q_freqs)
            if best_i is not None and confidence > 0.3:
                matched_start = archive_times[best_i]
                matched_end = archive_times[min(best_i + len(q_freqs) - 1, len(archive_times) - 1)]
                st.success(
                    f"✅ التسجيل يبدو أصليًا — درجة الثقة: {confidence:.0%}\n\n"
                    f"الوقت المطابق بالأرشيف: من **{matched_start.strftime('%Y-%m-%d %H:%M:%S')}** "
                    f"إلى **{matched_end.strftime('%Y-%m-%d %H:%M:%S')}**"
                )
                db.log_verification(
                    suspect_file.name, "أصلي", confidence,
                    f"{matched_start.strftime('%Y-%m-%d %H:%M:%S')} → {matched_end.strftime('%H:%M:%S')}",
                )
            else:
                st.warning(
                    "لم يُعثر على تطابق قوي بالأرشيف الحالي — "
                    "قد يكون التسجيل من فترة غير مغطاة بالأرشيف بعد، أو بعيدًا عن مصدر كهرباء."
                )
                db.log_verification(suspect_file.name, "غير محدد", confidence, "لا يوجد تطابق قوي")
        else:
            part1 = q_freqs[:jump_idx]
            part2 = q_freqs[jump_idx:]
            i1, c1 = find_best_match(archive_times, archive_freqs, part1)
            i2, c2 = find_best_match(archive_times, archive_freqs, part2)

            msg = f"⚠️ تم اكتشاف تلاعب محتمل عند النقطة {jump_idx} من التسجيل.\n\n"
            if i1 is not None:
                t1_start = archive_times[i1]
                t1_end = archive_times[min(i1 + len(part1) - 1, len(archive_times) - 1)]
                msg += f"الجزء الأول يطابق: **{t1_start.strftime('%Y-%m-%d %H:%M:%S')} → {t1_end.strftime('%H:%M:%S')}** (ثقة {c1:.0%})\n\n"
            if i2 is not None:
                t2_start = archive_times[i2]
                msg += f"الجزء الثاني يطابق: بدايةً من **{t2_start.strftime('%Y-%m-%d %H:%M:%S')}** (ثقة {c2:.0%})\n\n"
            if i1 is not None and i2 is not None:
                gap = (t2_start - t1_end)
                msg += f"**الفترة المفقودة (المحذوفة/المدموجة): {gap}**"

            st.error(msg)
            avg_conf = np.mean([c for c in [c1, c2] if c is not None]) if (i1 is not None or i2 is not None) else 0.0
            db.log_verification(suspect_file.name, "متلاعب فيه", float(avg_conf), msg[:200])

        os.unlink(raw_path)
        if audio_path != raw_path:
            os.unlink(audio_path)

st.markdown(
    """
    <div class="sabr-accent-card">
        <h4>سَبْر</h4>
        <p>التحقق من صحة الأدلة الرقمية عبر بصمة الشبكة الكهربائية السعودية</p>
    </div>
    """,
    unsafe_allow_html=True,
)

v_count = db.verification_count()
recent = db.get_recent_verifications(1)
last_result = recent[0][2] if recent else "لا يوجد بعد"

ov1, ov2, ov3, ov4 = st.columns(4)
with ov1:
    with st.container(border=True):
        st.metric("نقاط الأرشيف", f"{total_points:,}")
        if total_points > 1:
            _, spark_freqs = db.load_reference_archive()
            spark_vals = spark_freqs[-30:] if len(spark_freqs) > 30 else spark_freqs
            st.plotly_chart(make_sparkline(spark_vals), width="stretch", config={"displayModeBar": False})
with ov2:
    with st.container(border=True):
        st.metric("النطاق الزمني", span_label if total_points > 0 else "لا يوجد بعد")
with ov3:
    with st.container(border=True):
        st.metric("عدد عمليات التحقق", f"{v_count:,}")
with ov4:
    with st.container(border=True):
        st.metric("آخر نتيجة", last_result)

col_a, col_b, col_c = st.columns(3)

# ---------- Column A: reference archive ----------
with col_a:
    with st.container(border=True):
        st.subheader("الأرشيف المرجعي")
        c1, c2 = st.columns(2)
        with c1:
            ref_date = st.date_input("التاريخ", value=datetime.date.today(), label_visibility="collapsed")
        with c2:
            ref_time = st.time_input("الوقت", value=datetime.time(0, 0), label_visibility="collapsed")

        ref_file = st.file_uploader("ملف الأرشيف (wav/mp3/m4a)", type=["wav", "mp3", "m4a"], key="ref", label_visibility="collapsed")

        if ref_file is not None and st.button("استخراج وحفظ", disabled=not db_ready, key="btn_ref"):
            start_dt = datetime.datetime.combine(ref_date, ref_time)
            raw_suffix = "." + ref_file.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=raw_suffix) as tmp:
                tmp.write(ref_file.read())
                raw_ref_path = tmp.name

            ref_path = raw_ref_path + "_converted.wav"
            convert_result = subprocess.run(
                ["ffmpeg", "-y", "-i", raw_ref_path, "-ar", "16000", "-ac", "1", ref_path],
                capture_output=True,
            )
            if convert_result.returncode != 0 or not os.path.exists(ref_path):
                st.error("تعذّر تحويل الملف الصوتي. تأكدي أن الملف سليم.")
                with st.expander("تفاصيل الخطأ"):
                    st.code(convert_result.stderr.decode(errors="ignore")[-1000:])
            else:
                with st.spinner("جاري الاستخراج والحفظ..."):
                    t, f = extract_enf(ref_path)
                    saved_count = db.save_reference_points(start_dt, t, f)
                st.success(f"تم حفظ {saved_count} نقطة بشكل دائم.")

            os.unlink(raw_ref_path)
            if os.path.exists(ref_path):
                os.unlink(ref_path)

# ---------- Column B: verify a recording ----------
with col_b:
    with st.container(border=True):
        st.subheader("التحقق من تسجيل")
        run_verification_flow(key_prefix="main")

# ---------- Column C: insights + mini log ----------
with col_c:
    with st.container(border=True):
        st.subheader("نسبة الأصالة")
        all_logs = db.get_recent_verifications(2000)
        total_logs = len(all_logs)
        orig_count = sum(1 for r in all_logs if r[2] == "أصلي")
        orig_pct = (orig_count / total_logs * 100) if total_logs > 0 else 0
        st.plotly_chart(make_gauge(orig_pct), width="stretch", config={"displayModeBar": False})

        duration_hours = (newest - oldest).total_seconds() / 3600 if total_points > 0 else 0
        db_size_kb = os.path.getsize(db.DB_PATH) / 1024 if os.path.exists(db.DB_PATH) else 0
        st.markdown(
            f"""
            <div class="sabr-mini-card">
                <div class="lbl">مدة الأرشيف / حجم القاعدة</div>
                <div class="val">{duration_hours:.1f} س · {db_size_kb:.0f} KB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("آخر العمليات")
        log_rows = db.get_recent_verifications(3)
        if log_rows:
            log_df = pd.DataFrame(log_rows, columns=["الوقت", "الملف", "النتيجة", "الثقة", "التفاصيل"])
            log_df["الوقت"] = pd.to_datetime(log_df["الوقت"]).dt.strftime("%m-%d %H:%M")
            log_df["الثقة"] = log_df["الثقة"].apply(lambda c: f"{c:.0%}" if pd.notna(c) else "—")
            st.dataframe(
                log_df[["الوقت", "النتيجة", "الثقة"]],
                hide_index=True, width="stretch",
            )
        else:
            st.caption("لا توجد عمليات بعد.")
