import streamlit as st
import json
import os
import uuid
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Agenda iDISCO+", page_icon="🧠", layout="wide")
DATA_FILE = 'idisco_agenda.json'

# --- GESTIONE DATI ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- LOGICA DEL PROTOCOLLO ---
def generate_protocol(start_date, ab1_days, ab2_days, fasi_scelte=None, ab1_info="", ab2_info=""):
    if fasi_scelte is None:
        fasi_scelte = ["Dehydration MeOH & 66% DCM", "Wash MeOH & Bleaching H2O2", "Wash PBST & Permeabilization", "Blocking", "Wash PBSTwHep (Post-Ab1)", "Wash PBSTwHep (Post-Ab2)", "Dehydration, DCM, RI matching (DBE)"]
        
    tasks = []
    current_date = start_date
    
    def add_task(name, days_duration):
        nonlocal current_date
        tasks.append({"id": str(uuid.uuid4()), "name": name, "date": current_date.strftime("%Y-%m-%d")})
        current_date += timedelta(days=days_duration)

    if "Dehydration MeOH & 66% DCM" in fasi_scelte: add_task("Dehydration MeOH & 66% DCM o.n.", 1)
    if "Wash MeOH & Bleaching H2O2" in fasi_scelte: add_task("Wash MeOH, Rehydration & Bleaching H2O2 o.n.", 1)
    if "Wash PBST & Permeabilization" in fasi_scelte: add_task("Wash PBST & Permeabilization o.n.", 1)
    if "Blocking" in fasi_scelte: add_task("Blocking o.n.", 1)
    
    # Formattazione per gli anticorpi
    ab1_suffix = f" ({ab1_info})" if ab1_info.strip() else ""
    for i in range(ab1_days): add_task(f"Antibody I{ab1_suffix} - Giorno {i+1}/{ab1_days}", 1)
    
    if "Wash PBSTwHep (Post-Ab1)" in fasi_scelte: add_task("Wash PBSTwHep o.n.", 1)
    
    # Formattazione per gli anticorpi
    ab2_suffix = f" ({ab2_info})" if ab2_info.strip() else ""
    for i in range(ab2_days): add_task(f"Antibody II{ab2_suffix} - Giorno {i+1}/{ab2_days}", 1)
    
    if "Wash PBSTwHep (Post-Ab2)" in fasi_scelte: add_task("Wash PBSTwHep o.n.", 1)
    if "Dehydration, DCM, RI matching (DBE)" in fasi_scelte: add_task("Dehydration, DCM, RI matching (DBE) + FINE", 1)
    
    add_task("FINE PROTOCOLLO", 0)
    return tasks

# --- FUNZIONI DI SUPPORTO ---
def get_giorno_sett(date_obj):
    return ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"][date_obj.weekday()]

# --- INTERFACCIA UTENTE ---
def main():
    st.title("🧠 Agenda Protocollo iDISCO+")
    
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    
    # --- SIDEBAR (PANNELLO DI CONTROLLO) ---
    st.sidebar.header("Pannello Controllo")
    
    # Nuovo Esperimento
    # 1. Nuovo Esperimento
    with st.sidebar.expander("🟢 Nuovo Esperimento", expanded=False):
        exp_name = st.text_input("Nome Esperimento", key="new_exp_name")
        exp_color = st.text_input("Colore/Emoji (es. B, R, 🟢)", value="🔵", key="new_exp_color")
        start_date = st.date_input("Data Inizio", datetime.today(), key="new_exp_start")
        
        ab1_days = st.number_input("Giorni Ab I", min_value=1, value=3, key="new_exp_ab1")
        ab1_info = st.text_input("Dettagli Ab I (es. Anti-NeuN 1:500)", key="new_exp_ab1_info")
        
        ab2_days = st.number_input("Giorni Ab II", min_value=1, value=3, key="new_exp_ab2")
        ab2_info = st.text_input("Dettagli Ab II (es. Dk anti-Ms 1:1000)", key="new_exp_ab2_info")
        
        st.write("⚙️ Fasi Standard (Rimuovi le X per saltare uno step):")
        opzioni_fasi = [
            "Dehydration MeOH & 66% DCM",
            "Wash MeOH & Bleaching H2O2",
            "Wash PBST & Permeabilization",
            "Blocking",
            "Wash PBSTwHep (Post-Ab1)",
            "Wash PBSTwHep (Post-Ab2)",
            "Dehydration, DCM, RI matching (DBE)"
        ]
        fasi_scelte = st.multiselect("Step inclusi:", options=opzioni_fasi, default=opzioni_fasi, label_visibility="collapsed")
        
        if st.button("Crea Protocollo"):
            if exp_name:
                exp_id = str(uuid.uuid4())
                start_datetime = datetime.combine(start_date, datetime.min.time())
                
                # Ora fasi_scelte e le info degli anticorpi sono definite correttamente prima di chiamare la funzione
                tasks = generate_protocol(start_datetime, ab1_days, ab2_days, fasi_scelte, ab1_info, ab2_info)
                
                st.session_state.data[exp_id] = {
                    "name": exp_name,
                    "color": exp_color,
                    "tasks": tasks
                }
                save_data(st.session_state.data)
                st.success("Protocollo creato!")
                st.rerun()
            else:
                st.error("Inserisci un nome per l'esperimento.")

    if st.session_state.data:
        exp_list = [(k, v['name']) for k, v in st.session_state.data.items()]
        
        # Elimina Esperimento
        with st.sidebar.expander("❌ Elimina Esperimento", expanded=False):
            exp_to_del = st.selectbox("Quale eliminare?", options=[e[1] for e in exp_list], key="del_exp_select")
            exp_id_to_del = next((e[0] for e in exp_list if e[1] == exp_to_del), None)
            
            if st.button("Conferma Eliminazione", key="del_exp_btn"):
                if exp_id_to_del:
                    del st.session_state.data[exp_id_to_del]
                    save_data(st.session_state.data)
                    st.warning(f"Esperimento {exp_to_del} eliminato.")
                    st.rerun()

        # Aggiungi Step
        with st.sidebar.expander("➕ Aggiungi Step Personalizzato", expanded=False):
            exp_to_mod = st.selectbox("Esperimento", options=[e[1] for e in exp_list], key="add_step_exp_select")
            exp_id_to_mod = next((e[0] for e in exp_list if e[1] == exp_to_mod), None)
            
            if exp_id_to_mod:
                tasks = st.session_state.data[exp_id_to_mod]['tasks']
                task_names = [f"{datetime.strptime(t['date'], '%Y-%m-%d').strftime('%d/%m')} - {t['name']}" for t in tasks]
                ref_task_name = st.selectbox("Dopo quale step?", options=task_names, key="add_step_ref_task")
                ref_task_idx = task_names.index(ref_task_name)
                
                new_step_name = st.text_input("Nome Nuovo Step", value="Extra Wash", key="add_step_new_name")
                new_step_duration = st.number_input("Durata (Giorni)", min_value=1, value=1, key="add_step_duration")
                
                if st.button("Aggiungi e Slitta", key="add_step_btn"):
                    ref_date = datetime.strptime(tasks[ref_task_idx]['date'], "%Y-%m-%d")
                    new_date = ref_date + timedelta(days=1)
                    
                    nuovo_task = {
                        "id": str(uuid.uuid4()),
                        "name": f"⚙️ {new_step_name}",
                        "date": new_date.strftime("%Y-%m-%d")
                    }
                    tasks.insert(ref_task_idx + 1, nuovo_task)
                    
                    for i in range(ref_task_idx + 2, len(tasks)):
                        vecchia_data = datetime.strptime(tasks[i]['date'], "%Y-%m-%d")
                        nuova_data = vecchia_data + timedelta(days=new_step_duration)
                        tasks[i]['date'] = nuova_data.strftime("%Y-%m-%d")
                        
                    save_data(st.session_state.data)
                    st.success(f"Step '{new_step_name}' aggiunto e date successive slittate.")
                    st.rerun()
                    
        # Rimuovi Step
        with st.sidebar.expander("➖ Rimuovi Step", expanded=False):
            exp_to_rem = st.selectbox("Da quale esperimento?", options=[e[1] for e in exp_list], key="rem_step_exp")
            exp_id_to_rem = next((e[0] for e in exp_list if e[1] == exp_to_rem), None)
            
            if exp_id_to_rem:
                tasks = st.session_state.data[exp_id_to_rem]['tasks']
                task_names = [f"{datetime.strptime(t['date'], '%Y-%m-%d').strftime('%d/%m')} - {t['name']}" for t in tasks if "FINE" not in t['name']]
                
                if task_names:
                    task_to_rem_name = st.selectbox("Quale step eliminare?", options=task_names, key="rem_step_task")
                    task_idx_to_rem = task_names.index(task_to_rem_name)
                    
                    if st.button("Elimina e Anticipa Date", key="rem_step_btn"):
                        tasks.pop(task_idx_to_rem) 
                        for i in range(task_idx_to_rem, len(tasks)):
                            v_data = datetime.strptime(tasks[i]['date'], "%Y-%m-%d")
                            tasks[i]['date'] = (v_data - timedelta(days=1)).strftime("%Y-%m-%d")
                            
                        save_data(st.session_state.data)
                        st.warning("Step rimosso e date anticipate di 1 giorno!")
                        st.rerun()

        # Pausa / Slitta
        with st.sidebar.expander("⏸️ Pausa / Slitta Date", expanded=False):
            exp_to_pause = st.selectbox("Esperimento da fermare", options=[e[1] for e in exp_list], key="pause_exp_select")
            exp_id_to_pause = next((e[0] for e in exp_list if e[1] == exp_to_pause), None)
            
            if exp_id_to_pause:
                tasks = st.session_state.data[exp_id_to_pause]['tasks']
                task_names = [f"{datetime.strptime(t['date'], '%Y-%m-%d').strftime('%d/%m')} - {t['name']}" for t in tasks]
                start_task_name = st.selectbox("Prima di quale step", options=task_names, key="pause_start_task")
                start_task_idx = task_names.index(start_task_name)
                
                pause_days = st.number_input("Giorni di stop", min_value=1, value=1, key="pause_days")
                
                if st.button("Applica Pausa", key="pause_btn"):
                    for i in range(start_task_idx, len(tasks)):
                        vecchia_data = datetime.strptime(tasks[i]['date'], "%Y-%m-%d")
                        nuova_data = vecchia_data + timedelta(days=pause_days)
                        tasks[i]['date'] = nuova_data.strftime("%Y-%m-%d")
                        
                    save_data(st.session_state.data)
                    st.info(f"Protocollo slittato di {pause_days} giorni da '{tasks[start_task_idx]['name']}' in poi.")
                    st.rerun()

    else:
        st.info("Benvenuto! Usa il pannello a sinistra per creare il tuo primo esperimento.")

    # --- MAIN CONTENT: L'AGENDA GLOBALE ---
    st.subheader("🗓️ Agenda Globale (Visualizzazione ad Agenda)")
    
    all_tasks = []
    if st.session_state.data:
        for exp_id, exp_info in st.session_state.data.items():
            for task in exp_info['tasks']:
                date_obj = datetime.strptime(task['date'], "%Y-%m-%d").date()
                all_tasks.append({
                    'title': f"{task['name']}",
                    'raw_date': date_obj,
                    'exp_name': exp_info['name'],
                    'color': exp_info['color'],
                    'is_weekend': date_obj.weekday() >= 5
                })
        
        # Ordina cronologicamente
        all_tasks.sort(key=lambda x: x['raw_date'])
        
        if all_tasks:
            current_date = None
            
            for t in all_tasks:
                if t['raw_date'] != current_date:
                    current_date = t['raw_date']
                    giorno_sett = get_giorno_sett(current_date)
                    date_str = current_date.strftime("%d/%m/%Y")
                    
                    # Stile per la data (rosso se weekend)
                    color_style = "color: red; font-weight: bold;" if t['is_weekend'] else "color: black; font-weight: bold;"
                    avviso_weekend = " [!!! WEEKEND !!!]" if t['is_weekend'] else ""
                    
                    st.markdown(f"### <span style='{color_style}'>{giorno_sett} {date_str}{avviso_weekend}</span>", unsafe_allow_html=True)
                
                # Formattazione del task
                st.markdown(f"> **{t['color']} {t['exp_name']}**: {t['title']}", unsafe_allow_html=True)
        else:
            st.info("Nessun task in agenda.")
            
if __name__ == '__main__':
    main()