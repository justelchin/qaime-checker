import streamlit as st
import pandas as pd

st.set_page_config(page_title="e-Taxes vs 1C Üzləşmə", layout="wide")

st.title("📊 e-Taxes və 1C Qaimə Mütəqabil Yoxlama Sistemi")
st.write("e-Taxes portalından və 1C-dən yüklədiyiniz Excel fayllarını daxil edin.")

# Fayl yükləmə hissəsi
col1, col2 = st.columns(2)

with col1:
    etaxes_file = st.file_uploader("1. e-Taxes Excel faylını yükləyin", type=["xlsx", "xls"])

with col2:
    onec_file = st.file_uploader("2. 1C Alışlar Excel faylını yükləyin", type=["xlsx", "xls"])

if etaxes_file and onec_file:
    try:
        df_etaxes = pd.read_excel(etaxes_file)
        df_1c = pd.read_excel(onec_file)

        st.success("Hər iki fayl uğurla yükləndi!")
        
        # Sütun seçimləri
        st.subheader("⚙️ Sütun Eyniləşdirilməsi")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**e-Taxes Faylı Sütunları:**")
            e_voen = st.selectbox("VÖEN Sütunu (e-Taxes)", df_etaxes.columns)
            e_qaime = st.selectbox("Qaimə № Sütunu (e-Taxes)", df_etaxes.columns)
            e_mebleg = st.selectbox("Yekun Məbləğ Sütunu (e-Taxes)", df_etaxes.columns)

        with c2:
            st.markdown("**1C Faylı Sütunları:**")
            o_voen = st.selectbox("VÖEN Sütunu (1C)", df_1c.columns)
            o_qaime = st.selectbox("Qaimə № Sütunu (1C)", df_1c.columns)
            o_mebleg = st.selectbox("Yekun Məbləğ Sütunu (1C)", df_1c.columns)

        if st.button("🚀 Yoxlamanı Başlat"):
            # Təmizləmə
            df_etaxes['clean_qaime'] = df_etaxes[e_qaime].astype(str).str.strip().str.upper()
            df_1c['clean_qaime'] = df_1c[o_qaime].astype(str).str.strip().str.upper()

            # 1. e-Taxes-də olub 1C-də OLMAYANLAR
            etaxes_not_in_1c = df_etaxes[~df_etaxes['clean_qaime'].isin(df_1c['clean_qaime'])].copy()

            # 2. 1C-də olub e-Taxes-də OLMAYANLAR
            onec_not_in_etaxes = df_1c[~df_1c['clean_qaime'].isin(df_etaxes['clean_qaime'])].copy()

            # 3. Məbləğ Fərqi Olanlar
            merged = pd.merge(
                df_etaxes, df_1c, 
                on='clean_qaime', 
                suffixes=('_eTaxes', '_1C')
            )
            merged['Məbləğ_Fərqi'] = merged[e_mebleg + '_eTaxes'] - merged[o_mebleg + '_1C']
            price_mismatch = merged[merged['Məbləğ_Fərqi'].abs() > 0.01].copy()

            st.markdown("---")
            st.header("📈 Yoxlama Nəticələri")

            tab1, tab2, tab3 = st.tabs([
                f"❌ 1C-də Olmayanlar ({len(etaxes_not_in_1c)})", 
                f"⚠️ Portalda Olmayanlar ({len(onec_not_in_etaxes)})", 
                f"💰 Məbləğ Fərqi Olanlar ({len(price_mismatch)})"
            ])

            with tab1:
                st.error("Bu qaimələr e-Taxes portalında var, lakin 1C-yə işlənməyib:")
                st.dataframe(etaxes_not_in_1c.drop(columns=['clean_qaime']))

            with tab2:
                st.warning("Bu qaimələr 1C-də var, lakin e-Taxes portalında tapılmadı:")
                st.dataframe(onec_not_in_etaxes.drop(columns=['clean_qaime']))

            with tab3:
                st.info("Bu qaimələr hər iki tərəfdə var, lakin məbləğləri üst-üstə düşmür:")
                st.dataframe(price_mismatch[[
                    'clean_qaime', 
                    e_mebleg + '_eTaxes', 
                    o_mebleg + '_1C', 
                    'Məbləğ_Fərqi'
                ]])

    except Exception as e:
        st.error(f"Fayllar oxunarkən xəta baş verdi: {e}")
