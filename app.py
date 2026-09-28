import streamlit as st
import pandas as pd

st.set_page_config(page_title="e-Taxes vs 1C Üzləşmə", layout="wide")

st.title("📊 e-Taxes və 1C Qaimə Mütəqabil Yoxlama Sistemi")
st.write("e-Taxes portalından və 1C-dən yüklədiyiniz Excel fayllarını daxil edin.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. e-Taxes Faylı")
    etaxes_file = st.file_uploader("e-Taxes Excel faylını yükləyin", type=["xlsx", "xls"], key="e_file")
    e_skip = st.number_input("e-Taxes Başlıq Sətri Nömrəsi:", min_value=0, max_value=25, value=7, step=1, help="Sütun adlarında 'Unnamed' çoxdursa, bu ədədi düzgün sətir tapılanadək artırın.")

with col2:
    st.header("2. 1C Faylı")
    onec_file = st.file_uploader("1C Alışlar Excel faylını yükləyin", type=["xlsx", "xls"], key="o_file")
    o_skip = st.number_input("1C Başlıq Sətri Nömrəsi:", min_value=0, max_value=25, value=0, step=1)

def load_file(file, header_row):
    file.seek(0)
    df = pd.read_excel(file, header=header_row)
    # Boş sətir və sütunları silirik
    df = df.dropna(how='all').dropna(how='all', axis=1)
    df.columns = [str(c).strip() for c in df.columns]
    return df

if etaxes_file and onec_file:
    try:
        df_etaxes = load_file(etaxes_file, e_skip)
        df_1c = load_file(onec_file, o_skip)

        st.success("Fayllar oxundu!")
        
        # Unnamed sütunları süzgəcdən keçiririk
        valid_e_cols = [c for c in df_etaxes.columns if not c.startswith('Unnamed:')]
        valid_o_cols = [c for c in df_1c.columns if not c.startswith('Unnamed:')]

        if not valid_e_cols:
            valid_e_cols = list(df_etaxes.columns)
        if not valid_o_cols:
            valid_o_cols = list(df_1c.columns)

        st.markdown("---")
        
        # Önizləmə funksiyası (istifadəçinin düzgün sətir seçdiyini görməsi üçün)
        with st.expander("🔍 Faylların İlkin Görünüşünü Yoxla (Önizləmə)"):
            p1, p2 = st.columns(2)
            with p1:
                st.subheader("e-Taxes faylının ilk 3 sətri:")
                st.dataframe(df_etaxes.head(3))
            with p2:
                st.subheader("1C faylının ilk 3 sətri:")
                st.dataframe(df_1c.head(3))

        st.subheader("⚙️ Sütun Eyniləşdirilməsi")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**e-Taxes Faylı Sütunları:**")
            e_voen = st.selectbox("VÖEN Sütunu (e-Taxes)", valid_e_cols, key="ev")
            e_qaime = st.selectbox("Qaimə № Sütunu (e-Taxes)", valid_e_cols, key="eq")
            e_mebleg = st.selectbox("Yekun Məbləğ Sütunu (e-Taxes)", valid_e_cols, key="em")

        with c2:
            st.markdown("**1C Faylı Sütunları:**")
            o_voen = st.selectbox("VÖEN Sütunu (1C)", valid_o_cols, key="ov")
            o_qaime = st.selectbox("Qaimə № Sütunu (1C)", valid_o_cols, key="oq")
            o_mebleg = st.selectbox("Yekun Məbləğ Sütunu (1C)", valid_o_cols, key="om")

        if st.button("🚀 Yoxlamanı Başlat"):
            # Mətn təmizlənməsi
            df_etaxes['clean_qaime'] = df_etaxes[e_qaime].astype(str).str.strip().str.upper()
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
