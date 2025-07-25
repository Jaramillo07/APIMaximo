import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Smart Maintenance AI", page_icon="🔧", layout="wide")

st.title("🔧 Smart Maintenance AI")
st.markdown("**Prototipo: Maximo API + Gemini AI**")

# Sidebar
st.sidebar.header("🔐 Credenciales")
usuario = st.sidebar.text_input("Usuario:")
contrasena = st.sidebar.text_input("Contraseña:", type="password")

# Gemini API
if 'gemini_api_key' in st.secrets:
    gemini_key = st.secrets['gemini_api_key']
    st.sidebar.success("✅ Gemini configurado")
else:
    gemini_key = st.sidebar.text_input("Gemini API Key:", type="password")

# Inicializar estado de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'session' not in st.session_state:
    st.session_state.session = None

def login_to_maximo(user, password):
    url = "https://rbmanca0.michelin.com/maximo/j_security_check"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Content-type": "application/x-www-form-urlencoded"
    }
    data = {"j_username": user, "j_password": password}
    session = requests.Session()
    
    try:
        response = session.post(url, headers=headers, data=data, verify=False, timeout=10)
        if response.status_code == 200:
            return session, True
        return None, False
    except:
        return None, False

def get_orders(session):
    query = ("oslc.where=siteid=\"MX2\" and spi:worktype in [\"I\",\"E\",\"S\"] "
             "and spi:maintenanceshop=\"MX2-NTCH\" and status in [\"PREPARED\",\"WFSCH\"] "
             "and spi:istask=false&oslc.select=wonum,description,status,worktype,spi:location"
             "&oslc.paging=true&oslc.pageSize=10")
    
    url = f"https://rbmanca0.michelin.com/maximo/api/os/mxapiwodetail?{query}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    try:
        response = session.get(url, headers=headers, verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("rdfs:member", [])
        return []
    except:
        return []

def test_gemini(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Responde: 'Gemini OK'"}]}]
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            return True, data['candidates'][0]['content']['parts'][0]['text']
        return False, "Error en API"
    except:
        return False, "Error de conexión"

def analyze_order(api_key, order):
    prompt = f"""Analiza esta orden:
ORDEN: {order.get('spi:wonum', 'N/A')}
DESCRIPCIÓN: {order.get('spi:description', 'N/A')}
TIPO: {order.get('spi:worktype', 'N/A')}

Proporciona:
1. Problema identificado
2. Posibles causas  
3. Recomendaciones
4. Recursos necesarios"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            return True, data['candidates'][0]['content']['parts'][0]['text']
        return False, "Error en análisis"
    except:
        return False, "Error de conexión"

# INTERFAZ PRINCIPAL
if not st.session_state.logged_in:
    st.header("🔐 Iniciar Sesión")
    
    if st.button("🚀 INICIAR SESIÓN EN MAXIMO", type="primary"):
        if usuario and contrasena:
            with st.spinner("Conectando a Maximo..."):
                session, login_ok = login_to_maximo(usuario, contrasena)
            
            if login_ok:
                st.session_state.logged_in = True
                st.session_state.session = session
                st.success("✅ Login exitoso!")
                st.rerun()
            else:
                st.error("❌ Error en login")
        else:
            st.warning("⚠️ Ingresa usuario y contraseña")
    
    st.info("💡 Ingresa tus credenciales en el sidebar y haz click para iniciar")

else:
    st.header("🎛️ Panel de Control")
    st.success("✅ Conectado a Maximo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 Test Gemini"):
            if gemini_key:
                with st.spinner("Probando Gemini..."):
                    gemini_ok, gemini_msg = test_gemini(gemini_key)
                
                if gemini_ok:
                    st.success("✅ Gemini funcionando!")
                    st.info(f"Respuesta: {gemini_msg}")
                else:
                    st.error(f"❌ Error: {gemini_msg}")
            else:
                st.warning("⚠️ Falta API Key de Gemini")
    
    with col2:
        if st.button("📊 Obtener Órdenes"):
            with st.spinner("Obteniendo órdenes..."):
                ordenes = get_orders(st.session_state.session)
            
            if ordenes:
                st.success(f"✅ {len(ordenes)} órdenes obtenidas!")
                
                # Guardar en session state
                st.session_state.ordenes = ordenes
                
                # Mostrar tabla
                df_data = []
                for orden in ordenes:
                    df_data.append({
                        'WO': orden.get('spi:wonum', 'N/A'),
                        'Descripción': orden.get('spi:description', 'N/A')[:40] + '...',
                        'Tipo': orden.get('spi:worktype', 'N/A'),
                        'Estado': orden.get('spi:status', 'N/A')
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("⚠️ No se obtuvieron órdenes")
    
    with col3:
        if st.button("🧠 Análisis IA"):
            if gemini_key and 'ordenes' in st.session_state and st.session_state.ordenes:
                with st.spinner("Analizando con IA..."):
                    ai_ok, ai_msg = analyze_order(gemini_key, st.session_state.ordenes[0])
                
                if ai_ok:
                    st.success("✅ Análisis completado!")
                    with st.expander("🔍 Ver análisis"):
                        st.markdown(ai_msg)
                else:
                    st.error(f"❌ Error: {ai_msg}")
            else:
                st.warning("⚠️ Primero obtén órdenes y configura Gemini")
    
    # Botón de logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.session = None
        if 'ordenes' in st.session_state:
            del st.session_state.ordenes
        st.rerun()

# Info sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Instrucciones")
st.sidebar.info("1. Ingresa credenciales\n2. Inicia sesión\n3. Usa los botones del panel")

st.markdown("---")
st.markdown("🔧 **Smart Maintenance AI** - Prototipo")
