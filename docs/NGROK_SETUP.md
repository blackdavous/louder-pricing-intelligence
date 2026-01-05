# Ngrok Setup para Louder Price Intelligence

## 1. Ngrok está instalado en:
```
C:\Users\byed2\ngrok\ngrok.exe
```

## 2. Configurar Ngrok (Opcional - para sesiones persistentes)

Crea una cuenta gratis en: https://dashboard.ngrok.com/signup

Luego ejecuta:
```powershell
& "$env:USERPROFILE\ngrok\ngrok.exe" config add-authtoken TU_AUTH_TOKEN
```

## 3. Ejecutar Ngrok

### Opción A: Sin autenticación (sesión temporal)
```powershell
& "$env:USERPROFILE\ngrok\ngrok.exe" http 8000
```

### Opción B: Con autenticación (recomendado)
```powershell
# Primero obtén tu authtoken de: https://dashboard.ngrok.com/get-started/your-authtoken
& "$env:USERPROFILE\ngrok\ngrok.exe" config add-authtoken TU_TOKEN_AQUI

# Luego ejecuta:
& "$env:USERPROFILE\ngrok\ngrok.exe" http 8000
```

## 4. Obtener tu URL HTTPS

Cuando ejecutes ngrok, verás algo como:

```
Session Status                online
Account                       tu_cuenta (Plan: Free)
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copia la URL:** `https://abc123.ngrok-free.app`

## 5. Configurar en Mercado Libre

### Redirect URI:
```
https://abc123.ngrok-free.app/auth/callback
```

### Callbacks URL:
```
https://abc123.ngrok-free.app/webhooks/mercadolibre
```

## 6. Agregar a .env

```env
NGROK_URL=https://abc123.ngrok-free.app
MERCADOLIBRE_REDIRECT_URI=https://abc123.ngrok-free.app/auth/callback
```

## 7. Mantener Ngrok ejecutando

Abre una terminal separada y deja ngrok corriendo mientras desarrollas:

```powershell
& "$env:USERPROFILE\ngrok\ngrok.exe" http 8000
```

## Notas Importantes:

⚠️ **La URL cambia cada vez que reinicias ngrok** (en plan gratuito)
✅ **Con cuenta gratis tienes sesiones de 2 horas**
🔄 **Si la URL cambia, actualiza en Mercado Libre**
💰 **Plan pago tiene URLs fijas**

## Alternativa: Crear alias para uso fácil

```powershell
# Agregar al perfil de PowerShell
Set-Alias -Name ngrok -Value "$env:USERPROFILE\ngrok\ngrok.exe"

# Luego puedes usar simplemente:
ngrok http 8000
```
