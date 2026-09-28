import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="e-Taxes vs 1C Üzləşmə", layout="wide")

st.title("📊 e-Taxes və 1C Qaimə Mütəqabil Yoxlama Sistemi")
st.write("e-Taxes və 1C Excel fayllarını daxil edin.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. e-Taxes Faylı")
    etaxes_file = st.file_uploader("e-Taxes Excel faylını yükləyin", type=["xlsx", "xls"], key="e_file")

with col2:
    st.header("2. 1C Faylı")
    onec_file = st.file_uploader("1C Alışlar Excel faylını yükləyin", type=["xlsx", "xls"], key="o_file")

def find_header_and_read(file):
    file.seek(0)
    preview_df = pd.read_excel(file, header=None, nrows=10)
    
    header_idx = 0
    for idx, row in preview_df.iterrows():
        row_str = " ".join(row.dropna().astype(str)).lower()
        if any(keyword in row_str for keyword in ["vöen", "voen", "qaimə", "qaime", "nömrə", "nomre", "məbləğ", "mebleg", "adı", "adi"]):
            header_idx = idx
            break

    file.seek(0)
    df = pd.read_excel(file, header=header_idx)
    df = df.dropna(how='all').dropna(how='all', axis=1)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def extract_numbers(val):
    """Mətndən yalnız rəqəmləri çıxarır (xüsusən qaimə nömrəsi üçün)"""
    if pd.isna(val):
        return ""
    nums = re.sub(r'\D', '', str(val))
    if len(nums) >= 8:
        return nums[-8:]
    return nums

if etaxes_file and onec_file:
    try:
        df_etaxes = find_header_and_read(etaxes_file)
        df_1c = find_header_and_read(onec_file)

        st.success("Hər iki fayl uğurla oxundu!")

        st.markdown("---")
        st.subheader("⚙️ Sütun Eyniləşdirilməsi")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**e-Taxes Faylı Sütunları:**")
            v_idx = next((i for i, col in enumerate(df_etaxes.columns) if "vöen" in col.lower() or "voen" in col.lower()), 0)
            e_voen = st.selectbox("VÖEN Sütunu (e-Taxes)", df_etaxes.columns, index=v_idx, key="ev")
            
            a_idx = next((i for i, col in enumerate(df_etaxes.columns) if "adı" in col.lower() or "adi" in col.lower() or "şirkət" in col.lower() or "sirket" in col.lower()), 0)
            e_ad = st.selectbox("Şirkət Adı Sütunu (e-Taxes)", df_etaxes.columns, index=a_idx, key="ea")

            q_idx = next((i for i, col in enumerate(df_etaxes.columns) if "nömrə" in col.lower() or "nomre" in col.lower() or "qaimə" in col.lower()), 0)
            e_qaime = st.selectbox("Qaimə Nömrəsi Sütunu (e-Taxes)", df_etaxes.columns, index=q_idx, key="eq")
                
            m_idx = next((i for i, col in enumerate(df_etaxes.columns) if "məbləğ" in col.lower() or "mebleg" in col.lower() or "mablağ" in col.lower()), 0)
            e_mebleg = st.selectbox("Yekun Məbləğ Sütunu (e-Taxes)", df_etaxes.columns, index=m_idx, key="em")

        with c2:
            st.markdown("**1C Faylı Sütunları:**")
            ov_idx = next((i for i, col in enumerate(df_1c.columns) if "vöen" in col.lower() or "voen" in col.lower()), 0)
            oa_idx = next((i for i, col in enumerate(df_1c.columns) if "partnyor" in col.lower() or "adı" in col.lower() or "adi" in col.lower() or "kontragent" in col.lower()), 0)
            oq_idx = next((i for i, col in enumerate(df_1c.columns) if "nömrə" in col.lower() or "nomre" in col.lower()), 0)
            om_idx = next((i for i, col in enumerate(df_1c.columns) if "məbləğ" in col.lower() or "mebleg" in col.lower()), 0)
            val_idx = next((i for i, col in enumerate(df_1c.columns) if "valyuta" in col.lower() or "val" in col.lower() or "curr" in col.lower()), None)

            o_voen = st.selectbox("VÖEN Sütunu (1C)", df_1c.columns, index=ov_idx, key="ov")
            o_ad = st.selectbox("Şirkət Adı / Partnyor Sütunu (1C)", df_1c.columns, index=oa_idx, key="oa")
            o_qaime = st.selectbox("Qaimə № Sütunu (1C)", df_1c.columns, index=oq_idx, key="oq")
            o_mebleg = st.selectbox("Yekun Məbləğ Sütunu (1C)", df_1c.columns, index=om_idx, key="om")
            
            # Valyuta Sütunu seçimi
            val_options = ["Yoxdur"] + list(df_1c.columns)
            default_val_index = val_options.index(df_1c.columns[val_idx]) if val_idx is not None else 0
            o_valyuta = st.selectbox("Valyuta Sütunu (1C) [İstəyə bağlı]", val_options, index=default_val_index, key="oval")

            # Valyuta seçildikdə birbaşa həmin valyutaların siyahısını göstəririk
            selected_curr = "Bütün Valyutalar"
            if o_valyuta != "Yoxdur":
                unique_currencies = sorted(df_1c[o_valyuta].dropna().astype(str).str.upper().unique().tolist())
                
                # AZN sıradadırsa susmaya görə AZN seçilsin
                azn_index = 1
                for idx, curr in enumerate(unique_currencies):
                    if "AZN" in curr:
                        azn_index = idx + 1
                        break
                        
                selected_curr = st.selectbox(
                    "💱 Valyutanı Seçin (1C):", 
                    ["Bütün Valyutalar"] + unique_currencies, 
                    index=azn_index if len(unique_currencies) >= azn_index else 0, 
                    key="scurr"
                )

        if st.button("🚀 Yoxlamanı Başlat"):
            # 1C Faylını seçilmiş valyutaya görə filtrləyirik
            df_1c_filtered = df_1c.copy()
            if o_valyuta != "Yoxdur" and selected_curr != "Bütün Valyutalar":
                df_1c_filtered = df_1c[df_1c[o_valyuta].astype(str).str.upper() == selected_curr].copy()

            # Təmiz rəqəmli qaimə key-i yaradırıq
            df_etaxes['clean_qaime'] = df_etaxes[e_qaime].apply(extract_numbers)
            df_1c_filtered['clean_qaime'] = df_1c_filtered[o_qaime].apply(extract_numbers)

            # Məbləğləri rəqəmə çevirmək
            df_etaxes['num_mebleg'] = pd.to_numeric(df_etaxes[e_mebleg].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
            df_1c_filtered['num_mebleg'] = pd.to_numeric(df_1c_filtered[o_mebleg].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)

            # Boş olmayan qaimələri filtrləyirik
            df_etaxes_valid = df_etaxes[df_etaxes['clean_qaime'] != ''].copy()
            df_1c_valid = df_1c_filtered[df_1c_filtered['clean_qaime'] != ''].copy()

            # 1. e-Taxes-də olub 1C-də OLMAYANLAR
            etaxes_not_in_1c = df_etaxes_valid[~df_etaxes_valid['clean_qaime'].isin(df_1c_valid['clean_qaime'])].copy()

            # 2. 1C-də olub e-Taxes-də OLMAYANLAR
            onec_not_in_etaxes = df_1c_valid[~df_1c_valid['clean_qaime'].isin(df_etaxes_valid['clean_qaime'])].copy()

            # 3. Məbləğ Fərqi Olanlar
            merged = pd.merge(
                df_etaxes_valid, df_1c_valid, 
                on='clean_qaime', 
                suffixes=('_eTaxes', '_1C')
            )
            merged['Məbləğ_Fərqi'] = (merged['num_mebleg_eTaxes'] - merged['num_mebleg_1C']).round(2)
            price_mismatch = merged[merged['Məbləğ_Fərqi'].abs() > 0.01].copy()

            st.markdown("---")
            st.header("📊 Ümumi Hesabat (Dashboard)")

            # Dashboard Göstəriciləri
            total_e_sum = df_etaxes_valid['num_mebleg'].sum()
            total_1c_sum = df_1c_valid['num_mebleg'].sum()
            diff_sum = total_e_sum - total_1c_sum

            curr_label = f" ({selected_curr})" if selected_curr != "Bütün Valyutalar" else ""

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"e-Taxes Ümumi Dövriyyə", f"{total_e_sum:,.2f} AZN")
            m2.metric(f"1C Ümumi Dövriyyə{curr_label}", f"{total_1c_sum:,.2f} {selected_curr if selected_curr != 'Bütün Valyutalar' else ''}")
            m3.metric("Fərq (Dövriyyə)", f"{diff_sum:,.2f}", delta=f"{diff_sum:,.2f}", delta_color="inverse")
            m4.metric("Çatışmayan Qaimə Sayı", f"{len(etaxes_not_in_1c) + len(onec_not_in_etaxes)} ədəd")

            st.markdown("---")
            st.header("📈 Yoxlama Nəticələri")

            tab1, tab2, tab3 = st.tabs([
                f"❌ 1C-də Olmayanlar ({len(etaxes_not_in_1c)})", 
                f"⚠️ Portalda Olmayanlar ({len(onec_not_in_etaxes)})", 
                f"💰 Məbləğ Fərqi Olanlar ({len(price_mismatch)})"
            ])

            with tab1:
                st.error("Bu qaimələr e-Taxes portalında var, lakin 1C-yə (seçilmiş valyutaya) işlənməyib:")
                st.dataframe(etaxes_not_in_1c.drop(columns=['clean_qaime', 'num_mebleg'], errors='ignore'), use_container_width=True)

            with tab2:
                st.warning("Bu qaimələr 1C-də var, lakin e-Taxes portalında tapılmadı:")
                st.dataframe(onec_not_in_etaxes.drop(columns=['clean_qaime', 'num_mebleg'], errors='ignore'), use_container_width=True)

            with tab3:
                st.info("Bu qaimələr hər iki tərəfdə var, lakin məbləğləri üst-üstə düşmür:")
                st.dataframe(price_mismatch.drop(columns=['clean_qaime', 'num_mebleg_eTaxes', 'num_mebleg_1C'], errors='ignore'), use_container_width=True)

    except Exception as e:
        st.error(f"Yoxlama zamanı xəta baş verdi: {e}")
