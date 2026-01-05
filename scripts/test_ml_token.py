"""
Test simple de conexión a Mercado Libre API.

Verifica que el token funciona sin hacer requests pesados.
Ideal para probar antes de escalar.
"""
import json
import time
from pathlib import Path
import requests
from datetime import datetime, timedelta


def load_token():
    """Cargar token desde ml_token.json"""
    token_path = Path(__file__).parent.parent / "ml_token.json"
    
    if not token_path.exists():
        return None, "Token file not found"
    
    with open(token_path, 'r') as f:
        data = json.load(f)
    
    # Check if token is expired
    acquired_at = data.get("acquired_at", 0)
    expires_in = data.get("expires_in", 21600)
    
    acquired_time = datetime.fromtimestamp(acquired_at)
    expiry_time = acquired_time + timedelta(seconds=expires_in)
    now = datetime.now()
    
    is_expired = now > expiry_time
    time_left = (expiry_time - now).total_seconds() / 3600  # hours
    
    return data, {
        "acquired_at": acquired_time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expiry_time.strftime("%Y-%m-%d %H:%M:%S"),
        "is_expired": is_expired,
        "hours_left": round(time_left, 2)
    }


def test_token_validity(access_token: str):
    """
    Test 1: Verificar que el token es válido.
    Endpoint ligero que no consume muchos recursos.
    """
    print("\n" + "="*60)
    print("TEST 1: Validez del Token")
    print("="*60)
    
    url = "https://api.mercadolibre.com/users/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Token VÁLIDO")
            print(f"   User ID: {user_data.get('id')}")
            print(f"   Nickname: {user_data.get('nickname')}")
            print(f"   Country: {user_data.get('country_id')}")
            print(f"   Site: {user_data.get('site_id')}")
            return True, user_data
        elif response.status_code == 401:
            print("❌ Token EXPIRADO o INVÁLIDO")
            print(f"   Error: {response.text}")
            return False, None
        else:
            print(f"⚠️ Respuesta inesperada: {response.status_code}")
            print(f"   {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False, None


def test_search_lightweight(access_token: str):
    """
    Test 2: Búsqueda ligera (1 resultado).
    Verifica que podemos hacer búsquedas sin abusar.
    """
    print("\n" + "="*60)
    print("TEST 2: Búsqueda Ligera (1 resultado)")
    print("="*60)
    
    url = "https://api.mercadolibre.com/sites/MLM/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": "audifonos",
        "limit": 1  # Solo 1 resultado para no abusar
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Búsqueda exitosa")
            print(f"   Total encontrados: {data.get('paging', {}).get('total', 0)}")
            
            results = data.get('results', [])
            if results:
                item = results[0]
                print(f"   Ejemplo:")
                print(f"     - ID: {item.get('id')}")
                print(f"     - Título: {item.get('title', '')[:50]}...")
                print(f"     - Precio: ${item.get('price', 0):,.2f}")
            
            return True, data
        elif response.status_code == 429:
            print("⚠️ RATE LIMIT ALCANZADO")
            print("   Necesitamos espaciar las requests")
            return False, None
        elif response.status_code == 403:
            print("❌ ACCESO PROHIBIDO (403)")
            print("   El token no tiene permisos o la cuenta está limitada")
            return False, None
        else:
            print(f"⚠️ Error: {response.status_code}")
            print(f"   {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None


def test_categories(access_token: str):
    """
    Test 3: Obtener categorías (público, sin rate limit alto).
    """
    print("\n" + "="*60)
    print("TEST 3: Obtener Categorías")
    print("="*60)
    
    url = "https://api.mercadolibre.com/sites/MLM/categories"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ {len(categories)} categorías disponibles")
            
            # Find audio category
            audio_cats = [c for c in categories if 'audio' in c.get('name', '').lower()]
            if audio_cats:
                print(f"   Categoría Audio encontrada:")
                for cat in audio_cats[:3]:
                    print(f"     - {cat.get('name')} (ID: {cat.get('id')})")
            
            return True, categories
        else:
            print(f"⚠️ Error: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None


def main():
    """Ejecutar todos los tests."""
    print("\n" + "="*60)
    print("🔍 TEST DE CONEXIÓN A MERCADO LIBRE API")
    print("="*60)
    print("Verificando token y conectividad de forma segura...")
    
    # Load token
    token_data, status = load_token()
    
    if not token_data:
        print(f"\n❌ Error: {status}")
        print("\nAsegúrate de que ml_token.json existe en el directorio raíz.")
        return
    
    # Show token status
    print("\n📋 Estado del Token:")
    print(f"   Adquirido: {status['acquired_at']}")
    print(f"   Expira: {status['expires_at']}")
    print(f"   Tiempo restante: {status['hours_left']} horas")
    
    if status['is_expired']:
        print("\n⚠️ EL TOKEN ESTÁ EXPIRADO")
        print("   Necesitas renovarlo con el refresh_token")
        print(f"   Refresh Token: {token_data.get('refresh_token')}")
        return
    
    access_token = token_data.get("access_token")
    
    # Run tests
    results = {
        "validity": False,
        "search": False,
        "categories": False
    }
    
    # Test 1: Token validity
    results["validity"], _ = test_token_validity(access_token)
    
    if not results["validity"]:
        print("\n❌ Token inválido. No se pueden ejecutar más tests.")
        return
    
    # Small delay to avoid rate limit
    time.sleep(1)
    
    # Test 2: Search
    results["search"], _ = test_search_lightweight(access_token)
    
    # Small delay
    time.sleep(1)
    
    # Test 3: Categories
    results["categories"], _ = test_categories(access_token)
    
    # Summary
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        icon = "✅" if passed_test else "❌"
        print(f"{icon} {test_name.upper()}: {'PASS' if passed_test else 'FAIL'}")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("✅ TODOS LOS TESTS PASARON")
        print("\n🚀 El token está funcionando correctamente.")
        print("   Puedes proceder con la integración completa.")
    elif passed > 0:
        print(f"⚠️ {passed}/{total} TESTS PASARON")
        print("\n   Algunos tests fallaron. Revisar configuración.")
    else:
        print("❌ TODOS LOS TESTS FALLARON")
        print("\n   Verificar credenciales y conectividad.")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
