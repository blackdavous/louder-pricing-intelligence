"""
Script para renovar el access token de Mercado Libre usando refresh token.
"""
import json
import time
import requests
from pathlib import Path
from datetime import datetime


# Credenciales de la app (desde la conversación)
ML_CLIENT_ID = "5324643418860917"
ML_CLIENT_SECRET = "k1F0WFPtNe2TGNJFcc4uTmAxrpJ8oez3"


def refresh_token():
    """
    Renovar el access token usando el refresh token.
    
    Mercado Libre permite renovar tokens usando el refresh_token
    sin necesidad de volver a autenticar al usuario.
    """
    print("\n" + "="*60)
    print("🔄 RENOVANDO TOKEN DE MERCADO LIBRE")
    print("="*60)
    
    # Load current token
    token_path = Path(__file__).parent.parent / "ml_token.json"
    
    if not token_path.exists():
        print("❌ ml_token.json no encontrado")
        return False
    
    with open(token_path, 'r') as f:
        old_token = json.load(f)
    
    refresh_token_value = old_token.get("refresh_token")
    
    if not refresh_token_value:
        print("❌ refresh_token no encontrado en ml_token.json")
        return False
    
    print(f"📋 Refresh Token: {refresh_token_value[:20]}...")
    
    # Request new token
    url = "https://api.mercadolibre.com/oauth/token"
    
    payload = {
        "grant_type": "refresh_token",
        "client_id": ML_CLIENT_ID,
        "client_secret": ML_CLIENT_SECRET,
        "refresh_token": refresh_token_value
    }
    
    print("\n⏳ Solicitando nuevo token...")
    
    try:
        response = requests.post(url, data=payload, timeout=15)
        
        if response.status_code == 200:
            new_token = response.json()
            
            # Add timestamp
            new_token["acquired_at"] = int(time.time())
            
            # Save to file
            with open(token_path, 'w') as f:
                json.dump(new_token, f, indent=2)
            
            print("\n✅ TOKEN RENOVADO EXITOSAMENTE")
            print(f"   Access Token: {new_token['access_token'][:30]}...")
            print(f"   Token Type: {new_token.get('token_type')}")
            print(f"   Expires In: {new_token.get('expires_in')} segundos ({new_token.get('expires_in')/3600:.1f} horas)")
            print(f"   User ID: {new_token.get('user_id')}")
            print(f"   Refresh Token: {new_token.get('refresh_token')[:30]}...")
            
            acquired = datetime.fromtimestamp(new_token["acquired_at"])
            print(f"\n   Adquirido: {acquired.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Archivo actualizado: {token_path}")
            
            return True
            
        else:
            print(f"\n❌ Error al renovar token: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
            if response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('message', '')
                
                if 'invalid_grant' in error_msg.lower():
                    print("\n⚠️ REFRESH TOKEN INVÁLIDO O EXPIRADO")
                    print("\nNecesitas generar un nuevo token desde cero:")
                    print("1. Ve a https://developers.mercadolibre.com.mx/")
                    print("2. Accede a tu aplicación")
                    print("3. Genera un nuevo authorization code")
                    print("4. Ejecuta el script de primera autenticación")
            
            return False
            
    except Exception as e:
        print(f"\n❌ Error de conexión: {str(e)}")
        return False


def main():
    """Ejecutar renovación de token."""
    success = refresh_token()
    
    if success:
        print("\n" + "="*60)
        print("🎉 LISTO PARA USAR")
        print("="*60)
        print("\nAhora puedes ejecutar:")
        print("  python scripts/test_ml_token.py")
        print("\nPara verificar que el nuevo token funciona.")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("❌ RENOVACIÓN FALLÓ")
        print("="*60)
        print("\nRevisa los mensajes de error arriba.")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()
