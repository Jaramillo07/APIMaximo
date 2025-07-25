import streamlit as st
import requests
import pandas as pd
import urllib3

# Deshabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.title("🔧 Smart Maintenance AI - Prototipo")

# Sidebar para credenciales (más simple)
st.sidebar.header("🔐 Credenciales Maximo")
usuario = st.sidebar.text_input("Usuario:")
contrasena = st.sidebar.text_input("Contraseña:", type="password")

st.sidebar.header("🤖 API Key Gemini")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password")
st.sidebar.caption("Obtén tu key en: https://makersuite.google.com/app/apikey")

def test_gemini_api(api_key):
    """Test básico de Gemini API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Responde solo: 'Gemini funcionando en Smart Maintenance AI Prototipo'"
                    }
                ]
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            respuesta = data['candidates'][0]['content']['parts'][0]['text']
            return True, respuesta
        else:
            return False, f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"Error de conexión: {e}"

def analyze_wo_with_gemini(api_key, wo_data):
    """Analizar una orden de trabajo con Gemini"""
    if not wo_data:
        return False, "No hay datos para analizar"
    
    # Tomar la primera orden
    orden = wo_data[0]
    
    prompt = f"""
    Analiza esta orden de trabajo de mantenimiento:
    
    ORDEN: {orden.get('spi:wonum', 'N/A')}
    DESCRIPCIÓN: {orden.get('spi:description', 'N/A')}
    TIPO: {orden.get('spi:worktype', 'N/A')}
    UBICACIÓN: {orden.get('spi:location', 'N/A')}
    
    Proporciona:
    1. TIPO DE PROBLEMA identificado
    2. POSIBLES CAUSAS
    3. RECOMENDACIONES de solución
    4. RECURSOS estimados necesarios
    
    Responde de forma concisa y práctica.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            analisis = data['candidates'][0]['content']['parts'][0]['text']
            return True, analisis
        else:
            return False, f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"Error: {e}"

def login_maximo(usuario, contrasena):
    """Login simple a Maximo"""
    bmaDev = "https://rbmanca0.michelin.com/"
    url = f"{bmaDev}maximo/j_security_check"
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Content-type": "application/x-www-form-urlencoded",
        "Connection": "keep-alive"
    }
    data = {"j_username": usuario, "j_password": contrasena}
    
    session = requests.Session()
    
    try:
        response = session.post(url, headers=headers, data=data, verify=False, timeout=10)
        if response.status_code == 200:
            return session, True
        else:
            return None, False
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, False

def get_simple_wo_data(session):
    """Consulta simple de órdenes"""
    bmaDev = "https://rbmanca0.michelin.com/"
    
    # Consulta básica - solo 5 campos
    query = ("oslc.where=siteid=\"MX2\" "
             "and spi:worktype in [\"I\",\"E\",\"S\"] "
             "and spi:maintenanceshop=\"MX2-NTCH\" "
             "and status in [\"PREPARED\",\"WFSCH\"] "
             "and spi:istask=false"
             "&oslc.select=wonum,description,status,worktype,spi:location"
             "&oslc.paging=true&oslc.pageSize=10")  # Solo 10 registros
    
    url = f"{bmaDev}maximo/api/os/mxapiwodetail?{query}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    try:
        response = session.get(url, headers=headers, verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("rdfs:member", [])
        else:
            st.error(f"Error en consulta: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error en request: {e}")
        return []

# Interface principal
st.header("🧪 Tests de Conectividad")

# Test de Gemini primero (más rápido)
if gemini_key:
    if st.button("🤖 Test Gemini API"):
        with st.spinner("🤖 Probando Gemini..."):
            gemini_ok, gemini_response = test_gemini_api(gemini_key)
        
        if gemini_ok:
            st.success("✅ Gemini API funcionando!")
            st.info(f"🤖 Respuesta: {gemini_response}")
        else:
            st.error(f"❌ Error en Gemini: {gemini_response}")
else:
    st.info("💡 Ingresa credenciales en el sidebar para comenzar")

# Test completo: Maximo + Gemini
if st.button("🔄 Test Completo: Maximo + IA"):
    if usuario and contrasena and gemini_key:
        # 1. Test Maximo
        with st.spinner("🔐 Conectando a Maximo..."):
            session, login_ok = login_maximo(usuario, contrasena)
        
        if login_ok:
            st.success("✅ Maximo: Login exitoso!")
            
            with st.spinner("📊 Obteniendo datos de Maximo..."):
                ordenes = get_simple_wo_data(session)
            
            if ordenes:
                st.success(f"✅ Maximo: {len(ordenes)} órdenes obtenidas!")
                
                # Mostrar tabla básica
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📋 Datos de Maximo")
                    datos_tabla = []
                    for orden in ordenes[:5]:  # Solo 5 para no saturar
                        datos_tabla.append({
                            'WO': orden.get('spi:wonum', 'N/A'),
                            'Descripción': orden.get('spi:description', 'N/A')[:30] + '...',
                            'Tipo': orden.get('spi:worktype', 'N/A'),
                        })
                    
                    df = pd.DataFrame(datos_tabla)
                    st.dataframe(df, use_container_width=True)
                
                # 2. Test Gemini con datos reales
                with col2:
                    st.subheader("🤖 Análisis con IA")
                    with st.spinner("🤖 Analizando con Gemini..."):
                        ai_ok, ai_response = analyze_wo_with_gemini(gemini_key, ordenes)
                    
                    if ai_ok:
                        st.success("✅ Análisis IA completado!")
                        with st.expander("🧠 Ver análisis completo"):
                            st.markdown(ai_response)
                    else:
                        st.error(f"❌ Error en IA: {ai_response}")
                
                # 3. Métricas combinadas
                st.subheader("📊 Resumen del Test")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🔐 Maximo", "✅ OK" if login_ok else "❌ ERROR")
                
                with col2:
                    st.metric("📊 Datos", f"{len(ordenes)} órdenes")
                
                with col3:
                    st.metric("🤖 Gemini", "✅ OK" if ai_ok else "❌ ERROR")
                
                with col4:
                    tipos = [o.get('spi:worktype', 'N/A') for o in ordenes]
                    tipo_comun = max(set(tipos), key=tipos.count)
                    st.metric("📈 Tipo común", tipo_comun)
                
                # 4. Mostrar integración exitosa
                if login_ok and ai_ok:
                    st.balloons()
                    st.success("🎉 ¡INTEGRACIÓN EXITOSA! Maximo + Gemini funcionando perfecto")
                    st.info("🚀 Listo para desarrollar la app completa de Smart Maintenance AI")
                
            else:
                st.warning("⚠️ No se obtuvieron datos de Maximo")
        else:
            st.error("❌ Error en login de Maximo")
    else:
        st.warning("⚠️ Ingresa credenciales en el sidebar para continuar")

# Información
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Cómo usar")
st.sidebar.info("1. Ingresa credenciales arriba\n2. Prueba conexiones\n3. Ve análisis IA")
st.sidebar.markdown("### 🎯 Objetivo")
st.sidebar.success("Validar concepto de Smart Maintenance AI")

# Footer
st.markdown("---")
st.markdown("🔧 **Smart Maintenance AI** - Prototipo de integración Maximo + Gemini")
