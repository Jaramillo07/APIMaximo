import streamlit as st
import requests
import pandas as pd
import urllib3

# Deshabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de la página
st.set_page_config(
    page_title="Smart Maintenance AI",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Smart Maintenance AI - Prototipo")
st.markdown("**Integración Maximo API + Gemini AI para análisis inteligente de mantenimiento**")

# Sidebar para credenciales
st.sidebar.header("🔐 Credenciales Maximo")
usuario = st.sidebar.text_input("Usuario:")
contrasena = st.sidebar.text_input("Contraseña:", type="password")

# Gemini API - Usar secrets si está disponible
if 'gemini_api_key' in st.secrets:
    gemini_key = st.secrets['gemini_api_key']
    st.sidebar.header("🤖 Gemini AI")
    st.sidebar.success("✅ API Key configurada")
    st.sidebar.info("IA lista para análisis automático")
else:
    st.sidebar.header("🤖 API Key Gemini")
    gemini_key = st.sidebar.text_input("Gemini API Key:", type="password")
    st.sidebar.caption("Obtén tu key en: https://makersuite.google.com/app/apikey")

def test_gemini_basic(api_key):
    """Test básico de Gemini"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Responde solo: 'Gemini funcionando correctamente'"
            }]
        }]
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            respuesta = data['candidates'][0]['content']['parts'][0]['text']
            return True, respuesta
        else:
            return False, f"Error {response.status_code}"
    except Exception as e:
        return False, str(e)

def login_maximo(usuario, contrasena):
    """Login a Maximo"""
    base_url = "https://rbmanca0.michelin.com/"
    login_url = f"{base_url}maximo/j_security_check"
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Content-type": "application/x-www-form-urlencoded",
        "Connection": "keep-alive"
    }
    
    data = {
        "j_username": usuario, 
        "j_password": contrasena
    }
    
    session = requests.Session()
    
    try:
        response = session.post(login_url, headers=headers, data=data, verify=False, timeout=10)
        if response.status_code == 200:
            return session, True
        else:
            return None, False
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, False

def get_work_orders(session):
    """Obtener órdenes de trabajo"""
    base_url = "https://rbmanca0.michelin.com/"
    
    query_params = (
        "oslc.where=siteid=\"MX2\" "
        "and spi:worktype in [\"I\",\"E\",\"S\"] "
        "and spi:maintenanceshop=\"MX2-NTCH\" "
        "and status in [\"PREPARED\",\"WFSCH\"] "
        "and spi:istask=false"
        "&oslc.select=wonum,description,status,worktype,spi:location"
        "&oslc.paging=true&oslc.pageSize=10"
    )
    
    api_url = f"{base_url}maximo/api/os/mxapiwodetail?{query_params}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    try:
        response = session.get(api_url, headers=headers, verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("rdfs:member", [])
        else:
            st.error(f"Error en consulta: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error en request: {e}")
        return []

def analyze_with_gemini(api_key, orden):
    """Analizar orden con Gemini"""
    prompt = f"""
    Analiza esta orden de trabajo de mantenimiento:
    
    ORDEN: {orden.get('spi:wonum', 'N/A')}
    DESCRIPCIÓN: {orden.get('spi:description', 'N/A')}
    TIPO: {orden.get('spi:worktype', 'N/A')}
    UBICACIÓN: {orden.get('spi:location', 'N/A')}
    
    Proporciona análisis conciso:
    1. PROBLEMA identificado
    2. POSIBLES CAUSAS
    3. RECOMENDACIONES
    4. RECURSOS necesarios
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            analisis = data['candidates'][0]['content']['parts'][0]['text']
            return True, analisis
        else:
            return False, f"Error {response.status_code}"
    except Exception as e:
        return False, str(e)

# Interface principal
st.header("🧪 Tests de Conectividad")

# Test Gemini
if gemini_key:
    if st.button("🤖 Test Gemini API"):
        with st.spinner("Probando Gemini..."):
            gemini_ok, gemini_msg = test_gemini_basic(gemini_key)
        
        if gemini_ok:
            st.success("✅ Gemini funcionando!")
            st.info(f"Respuesta: {gemini_msg}")
        else:
            st.error(f"❌ Error Gemini: {gemini_msg}")
else:
    st.info("💡 Configura Gemini API Key para continuar")

# Test completo
if st.button("🔄 Test Completo: Maximo + IA"):
    if usuario and contrasena and gemini_key:
        # Login Maximo
        with st.spinner("Conectando a Maximo..."):
            session, login_ok = login_maximo(usuario, contrasena)
        
        if login_ok:
            st.success("✅ Maximo: Login exitoso!")
            
            # Obtener datos
            with st.spinner("Obteniendo órdenes..."):
                ordenes = get_work_orders(session)
            
            if ordenes:
                st.success(f"✅ Obtenidas {len(ordenes)} órdenes!")
                
                # Mostrar datos
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📋 Órdenes de Maximo")
                    df_data = []
                    for orden in ordenes:
                        df_data.append({
                            'WO': orden.get('spi:wonum', 'N/A'),
                            'Descripción': orden.get('spi:description', 'N/A')[:30] + '...',
                            'Tipo': orden.get('spi:worktype', 'N/A'),
                            'Estado': orden.get('spi:status', 'N/A')
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)
                
                # Análisis IA
                with col2:
                    st.subheader("🤖 Análisis IA")
                    with st.spinner("Analizando con Gemini..."):
                        ai_ok, ai_msg = analyze_with_gemini(gemini_key, ordenes[0])
                    
                    if ai_ok:
                        st.success("✅ Análisis completado!")
                        with st.expander("🧠 Ver análisis completo"):
                            st.markdown(ai_msg)
                    else:
                        st.error(f"❌ Error IA: {ai_msg}")
                
                # Métricas
                st.subheader("📊 Resumen")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🔐 Maximo", "✅ OK")
                with col2:
                    st.metric("📊 Órdenes", len(ordenes))
                with col3:
                    st.metric("🤖 IA", "✅ OK" if ai_ok else "❌ Error")
                with col4:
                    tipos = [o.get('spi:worktype', 'N/A') for o in ordenes]
                    tipo_comun = max(set(tipos), key=tipos.count) if tipos else "N/A"
                    st.metric("📈 Tipo común", tipo_comun)
                
                # Éxito completo
                if login_ok and ai_ok:
                    st.balloons()
                    st.success("🎉 ¡INTEGRACIÓN EXITOSA! Maximo + Gemini funcionando")
                    st.info("🚀 Listo para desarrollar Smart Maintenance AI completo")
            
            else:
                st.warning("⚠️ No se obtuvieron órdenes")
        else:
            st.error("❌ Error en login de Maximo")
    else:
        st.warning("⚠️ Faltan credenciales")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Instrucciones")
st.sidebar.info("1. Ingresa credenciales Maximo\n2. Prueba Gemini\n3. Ejecuta test completo")
st.sidebar.markdown("### 🎯 Objetivo")
st.sidebar.success("Validar integración para Smart Maintenance AI")

# Footer
st.markdown("---")
st.markdown("🔧 **Smart Maintenance AI** - Prototipo de integración")
