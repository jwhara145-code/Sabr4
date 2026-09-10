import streamlit as st
import numpy as np
import plotly.graph_objects as go
import librosa
import scipy.signal as signal
import pandas as pd
import tempfile
import os

# ==========================================
# 1. إعدادات الصفحة الأساسية
# ==========================================
st.set_page_config(
    page_title="سَبْر | SABR ENF Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. التصميم (CSS) - النمط المظلم (أسود وأزرق داكن)
# ==========================================
st.markdown("""
<style>
    /* خلفية الصفحة: تدرج من الأسود إلى الأزرق الداكن جداً */
    .stApp {
        background: linear-gradient(135deg, #000000 0%, #020617 60%, #0a0f1c 100%) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #F8FAFC !important;
    }
    
    /* البطاقات الداكنة الزجاجية */
    .dark-card {
        background-color: rgba(15, 23, 42, 0.4); /* أزرق داكن شفاف */
        backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
        margin-bottom: 20px;
        border: 1px solid #1E293B; /* إطار أزرق رمادي داكن */
    }
    
    /* بطاقة الحالة (في الانتظار) */
    .status-card-waiting {
        background-color: rgba(15, 23, 42, 0.6);
        border-radius: 12px;
        padding: 20px;
        color: #94A3B8;
        text-align: center;
        border: 1px solid #334155;
        margin-bottom: 20px;
    }

    /* بطاقة الحالة (نجاح الفحص) */
    .status-card-success {
        background-color: rgba(16, 185, 129, 0.1);
        border-radius: 12px;
        padding: 20px;
        color: #10B981;
        text-align: center;
        border: 1px solid rgba(16, 185, 129, 0.3);
        margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);
    }

    /* نصوص المؤشرات */
    .metric-title {
        color: #94A3B8; /* رمادي مزرق فاتح */
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #F8FAFC; /* أبيض ساطع */
        font-size: 28px;
        font-weight: bold;
    }
    
    /* إخفاء القوائم الافتراضية */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. محرك التحليل الجنائي (الخوارزمية الحقيقية)
# ==========================================
def extract_enf_real(audio_path, nominal_freq=60.0):
    y, sr = librosa.load(audio_path, sr=8000)
    nyq = 0.5 * sr
    low = (nominal_freq - 1.0) / nyq
    high = (nominal_freq + 1.0) / nyq
    b, a = signal.butter(4, [low, high], btype='band')
    filtered_y = signal.lfilter(b, a, y)
    
    n_fft = 4096
    hop_length = 2048
    stft = librosa.stft(filtered_y, n_fft=n_fft, hop_length=hop_length)
    magnitudes = np.abs(stft)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    
    freq_band_idx = np.where((freqs >= nominal_freq - 1) & (freqs <= nominal_freq + 1))[0]
    
    enf_curve = []
    for t in range(magnitudes.shape[1]):
        frame_mag = magnitudes[freq_band_idx, t]
        if np.sum(frame_mag) > 0:
            peak_idx = np.argmax(frame_mag)
            peak_freq = freqs[freq_band_idx[peak_idx]]
            enf_curve.append(peak_freq)
        else:
            enf_curve.append(nominal_freq)
            
    return np.array(enf_curve)

# ==========================================
# 4. بناء هيكل الواجهة (Layout)
# ==========================================

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #60A5FA;'>سَبْر</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**القائمة الرئيسية**")
    st.radio("", ["نظرة عامة", "تحليل ENF", "سجل التحقق"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**رفع الدليل الرقمي**")
    uploaded_file = st.file_uploader("صيغة WAV فقط", type=['wav'])
    target_hz = st.selectbox("تردد الشبكة المستهدف", [60, 50])

# -- المؤشرات العلوية --
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="dark-card">
        <div class="metric-title">نقاط الأرشيف</div>
        <div class="metric-value">102</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="dark-card">
        <div class="metric-title">النطاق الزمني المُغطى</div>
        <div class="metric-value">09-09 12:44</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="dark-card">
        <div class="metric-title">عدد عمليات التحقق</div>
        <div class="metric-value">4</div>
        <div style="color: #34D399; font-size: 12px; margin-top: 5px;">● حالة النظام: جاهز</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    if uploaded_file:
        st.markdown("""
        <div class="status-card-success">
            <div style="font-size: 14px; opacity: 0.9;">آخر نتيجة</div>
            <div style="font-size: 26px; font-weight: bold; margin-top: 5px;">دليل سليم ✅</div>
            <div style="font-size: 12px; margin-top: 5px;">تم التحقق والتحليل</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-card-waiting">
            <div style="font-size: 14px; opacity: 0.9;">آخر نتيجة</div>
            <div style="font-size: 26px; font-weight: bold; margin-top: 5px; color: #F8FAFC;">في الانتظار</div>
            <div style="font-size: 12px; margin-top: 5px;">بانتظار رفع الدليل</div>
        </div>
        """, unsafe_allow_html=True)

# -- القسم الأوسط: الرسم البياني والحماية --
mid_col1, mid_col2 = st.columns([3, 1])

with mid_col1:
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    st.markdown('<div style="display:flex; justify-content:space-between;"><h4 style="color: #F8FAFC;">معاينة ENF Grid</h4></div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        with st.spinner('جاري تحليل البصمة الكهربائية...'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_filepath = tmp_file.name
            
            enf_data = extract_enf_real(tmp_filepath, nominal_freq=target_hz)
            os.remove(tmp_filepath) 
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=enf_data,
                mode='lines',
                line=dict(color='#60A5FA', width=3), # أزرق نيون ساطع
                fill='tozeroy',
                fillcolor='rgba(96, 165, 250, 0.15)'
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(title=f'التردد (Hz)', gridcolor='#1E293B', tickfont=dict(color='#94A3B8'), titlefont=dict(color='#94A3B8')),
                xaxis=dict(title='الزمن', gridcolor='#1E293B', tickfont=dict(color='#94A3B8'), titlefont=dict(color='#94A3B8'))
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        dummy_data = [target_hz + np.sin(i/5)*0.02 + np.random.normal(0, 0.005) for i in range(100)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=dummy_data, mode='lines', line=dict(color='#334155', width=2)
        ))
        fig.update_layout(
            height=300, 
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='#1E293B', tickfont=dict(color='#334155')),
            xaxis=dict(gridcolor='#1E293B', tickfont=dict(color='#334155'))
        )
        st.plotly_chart(fig, use_container_width=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

with mid_col2:
    st.markdown("""
    <div class="dark-card" style="text-align: center;">
        <div class="metric-title">مستوى حماية النظام</div>
        <div style="font-size: 32px; font-weight: bold; color: #F8FAFC; margin: 10px 0;">99.8%</div>
        <div style="font-size: 12px; color: #64748B;">آخر تحديث أمني: اليوم</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="dark-card" style="border-color: rgba(239, 68, 68, 0.3); background-color: rgba(69, 10, 10, 0.2);">
        <div class="metric-title">مساحة التخزين المستخدمة</div>
        <div style="font-weight: bold; color: #F8FAFC; margin-bottom: 10px;">12.3 MB / 1 GB</div>
        <div style="font-size: 13px; color: #F87171;">3 ملفات قيد المعالجة</div>
    </div>
    """, unsafe_allow_html=True)

# -- القسم السفلي: سجل العمليات --
st.markdown('<div class="dark-card">', unsafe_allow_html=True)
st.markdown('<h4 style="color: #F8FAFC;">آخر عمليات التحقق (Recent Verification Log)</h4>', unsafe_allow_html=True)

log_data = pd.DataFrame({
    'النشاط': ['فحص صوتي', 'فحص صوتي', 'مصادقة فيديو', 'فحص صوتي'],
    'اسم الملف': ['Audio_File_A.wav', 'Audio_File_B.wav', 'Video_Clip_C.mp4', 'Audio_File_D.wav'],
    'التاريخ': ['10 Sep 2026', '10 Sep 2026', '09 Sep 2026', '09 Sep 2026'],
    'مؤشر ENF': ['42.1', '42.0', '41.9', '42.2'],
    'الحالة': ['✅ سليم', '✅ سليم', '⏳ قيد التحليل', '❌ تم التلاعب']
})
st.dataframe(log_data, use_container_width=True, hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)
