import streamlit as st
import pandas as pd

st.set_page_config(page_title="e-Taxes vs 1C Üzləşmə", layout="wide")

st.title("📊 e-Taxes və 1C Qaimə Mütəqabil Yoxlama Sistemi")
st.write("e-Taxes portalından və 1C-dən yüklədiyiniz Excel fayllarını daxil edin.")

def load_excel_smart(file):
    """Excel faylında əsas başlıq sətrini avtomatik tapan funksiya"""
    df_raw = pd.read_excel(file, header=None)
    header_idx = 0
    for idx, row in df_raw.iterrows():
        # Əgər sətirdə çoxlu mətn varsa və ya e-Taxes/1C-nin standart sözləri varsa
        row_str = row.astype(str).str.lower().to_list()
        if any('qaimə' in s or 'voen' in s or 'vöen' in s or 'nömrə' in s or 'məbləğ' in s or 'alınma' in s for s in row_str):
            header_idx = idx
            break
    
    file.seek(0)
    df = pd.read_excel(file, header=header_idx)
    # Təmizləmə: Tamamilə boş olan sütun və sətirləri silmək
    df = df.dropna(how='all').dropna(how='all', axis=1)
    # Sütun adlarındakı boşluqları təmizləmək
    df.columns = [str(c).strip() for c in df.columns]
    return df

col1, col2 = st.columns(2)

with col1:
    etaxes_file = st.file_uploader("1. e-Taxes Excel faylını yükləyin", type=["xlsx", "xls"])

with col2:
    onec_file = st.file_uploader("2. 1C Alışlar Excel faylını yükləyin", type=["xlsx", "xls"])

if etaxes_file and onec_file:
    try:
        df_etaxes = load_excel_smart(etaxes_file)
        df_1c = load_excel_smart(onec_file)

        st.success("Hər iki fayl uğurla oxundu!")
        
        st.subheader("⚙️ Sütun Eyniləşdirilməsi")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**e-Taxes Faylı Sütunları:**")
            e_voen = st.selectbox("VÖEN Sütunu (e-Taxes)", df_etaxes.columns, key="ev")
            e_qaime = st.selectbox("Qaimə № Sütunu (e-Taxes)", df_etaxes.columns, key="eq")
            e_mebleg = st.selectbox("Yekun Məbləğ Sütunu (e-Taxes)", df_etaxes.columns, key="em")

        with c2:
            st.markdown("**1C Faylı Sütunları:**")
            o_voen = st.selectbox("VÖEN Sütunu (1C)", df_1c.columns, key="ov")
            o_qaime = st.selectbox("Qaimə № Sütunu (1C)", df_1c.columns, key="oq")
            o_mebleg = st.selectbox("Yekun Məbləğ Sütunu (1C)", df_1c.columns, key="om")

        if st.button("🚀 Yoxlamanı Başlat"):
            # Təmizləmə
            df_etaxes['clean_qaime'] = df_etaxes[e_qaime].astype(str).str.strip().str.upper()
            df_1c['clean_qaime'] = df_1c[o_qaime].astype(str).str.strip().str.upper()

            # Məbləğləri rəqəmə çevirmək (xətaların qarşısını almaq üçün)
            df_etaxes['num_mebleg'] = pd.to_numeric(df_etaxes[e_mebleg], errors='coerce').fillna(0)
            df_1c['num_mebleg'] = pd.to_numeric(df_1c[o_mebleg], errors='coerce').fillna(0)

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
            merged['Məbləğ_Fərqi'] = merged['num_mebleg_eTaxes'] - merged['num_mebleg_1C']
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
