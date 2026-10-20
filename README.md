# Futmondo Scheduler

Scheduler público y sin datos privados para MACHO'S LEAGUE.

El repositorio público solo contiene la lógica de programación. El código real, el JSON y los datos de Futmondo permanecen en `cllorentejaime-sys/futmondo-reader-cloud` (privado).

## Funcionamiento

- 08:07 Europe/Madrid: análisis completo y publicación del JSON privado.
- 22:07 Europe/Madrid: análisis completo y publicación del JSON privado.
- Cada análisis calcula el siguiente vencimiento de bloqueo.
- Se programa un disparo puntual 60 minutos antes del vencimiento y otro de respaldo 20 minutos antes.
- Cuando arranca el renovador, el script existente de Futmondo espera hasta la ventana válida y reintenta cada 60 s solo dentro de esa vigilancia.
- Tras renovar, actualiza el JSON, avisa por Telegram y reprograma el siguiente vencimiento.
- No existe polling periódico cada 5 ni cada 30 minutos.

## Configuración privada necesaria

En Settings → Secrets and variables → Actions:

Secrets:
- PRIVATE_REPO_TOKEN
- FUTMONDO_EMAIL
- FUTMONDO_PASSWORD
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

Variables:
- FUTMONDO_CHAMPIONSHIP_ID
- FUTMONDO_USERTEAM_ID

No escribas esos valores en archivos del repositorio.

## Seguridad

El repositorio público no debe contener credenciales, tokens, IDs privados de sesión ni el JSON de Futmondo. El token de GitHub debe tener acceso mínimo de lectura/escritura al repositorio privado `futmondo-reader-cloud`.
