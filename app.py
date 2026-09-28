import streamlit as st
import pandas as pd

st.set_page_config(page_title="e-Taxes vs 1C Üzləşmə", layout="wide")

st.title("📊 e-Taxes və 1C Qaimə Mütəqabil Yoxlama Sistemi")
st.write("Düzəliş edilmiş e-Taxes və 1C Excel fayllarını daxil edin.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. e-Taxes Faylı")
    etaxes_file = st.file_uploader("e-Taxes Excel faylını yükləyin", type=["xlsx", "xls"], key="e_file")

with col2:
    st.header("2. 1C Faylı")
    onec_file = st.file_uploader("1C Alışlar Excel faylını yükləyin", type=["xlsx", "xls"], key="o_file")

def read_clean_excel(file):
    file.seek(0)
    # 1-ci sətir başlıq olduğu üçün standart pd.read_excel tam kifayətdir
    df = pd.read_excel(file)
    df = df.dropna(how='all').dropna(how='all', axis=1)
    df.columns = [str(c).strip() for c in df.columns]
    return df

if etaxes_file and onec_file:
    try:
        df_etaxes = read_clean_excel(etaxes_file)
        df_1c = read_clean_excel(onec_file)

        st.success("Hər iki fayl uğurla oxundu!")

        st.markdown("---")
        st.subheader("⚙️ Sütun Eyniləşdirilməsi")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**e-Taxes Faylı Sütunları:**")
            e_voen = st.selectbox("VÖEN Sütunu (e-Taxes)", df_etaxes.columns, index=0 if "VÖEN" in df_etaxes.columns else 0, key="ev")
            
            # Əgər seriya və nömrə ayrıdırsa
            has_series = st.checkbox("Qaimə seriyası və nömrəsi ayrı sütunlardadır?", value=True)
            if has_series:
                e_seria = st.selectbox("Qaimə Seriyası Sütunu", df_etaxes.columns, index=df_etaxes.columns.get_loc("Qaimə seriyası") if "Qaimə seriyası" in df_etaxes.columns else 0, key="es")
                e_qaime = st.selectbox("Qaimə Nömrəsi Sütunu", df_etaxes.columns, index=df_etaxes.columns.get_loc("Qaimə nömrəsi") if "Qaimə nömrəsi" in df_etaxes.columns else 0, key="eq")
            else:
                e_qaime = st.selectbox("Qaimə № Sütunu (e-Taxes)", df_etaxes.columns, key="eq_single")
                
            e_mebleg = st.selectbox("Yekun Məbləğ Sütunu (e-Taxes)", df_etaxes.columns, index=df_etaxes.columns.get_loc("Yekun məbləğ") if "Yekun məbləğ" in df_etaxes.columns else 0, key="em")

        with c2:
            st.markdown("**1C Faylı Sütunları:**")
            o_voen = st.selectbox("VÖEN Sütunu (1C)", df_1c.columns, key="ov")
            o_qaime = st.selectbox("Qaimə № Sütunu (1C)", df_1c.columns, key="oq")
            o_mebleg = st.selectbox("Yekun Məbləğ Sütunu (1C)", df_1c.columns, key="om")

        if st.button("🚀 Yoxlamanı Başlat"):
            # e-Taxes Qaimə № təyin edilməsi
            if has_series:
                df_etaxes['clean_qaime'] = df_etaxes[e_seria].astype(str).str.strip() + df_etaxes[e_qaime].astype(str).str.strip()
            else:
                df_etaxes['clean_qaime'] = df_etaxes[e_qaime].astype(str).str.strip()
            
            df_etaxes['clean_qaime'] = df_etaxes['clean_qaime'].str.upper()

            # 1C Qaimə № təmizlənməsi
            df_1c['clean_qaime'] = df_1c[o_qaime].astype(str).str.strip().str.upper()

            # Məbləğləri rəqəmə çevirmək
            df_etaxes['num_mebleg'] = pd.to_numeric(df_etaxes[e_mebleg].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
            df_1c['num_mebleg'] = pd.to_numeric(df_1c[o_mebleg].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)

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
            merged['Məbləğ_Fərqi'] = (merged['num_mebleg_eTaxes'] - merged['num_mebleg_1C']).round(2)
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
                st.dataframe(etaxes_not_in_1c.drop(columns=['clean_qaime', 'num_mebleg'], errors='ignore'))

            with tab2:
                st.warning("Bu qaimələr 1C-də var, lakin e-Taxes portalında tapılmadı:")
                st.dataframe(onec_not_in_etaxes.drop(columns=['clean_qaime', 'num_mebleg'], errors='ignore'))

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
