# Power Automate — recordatorios de PractiCV

Estado: **checkpoint v0.2 cerrado como flujo manual**. No es una automatización
programada.

## 1. Qué hace

El flujo `PractiCV Recordatorios` recibe un archivo exportado por PractiCV
(`calendar.ics` o `applications.csv`), lo adjunta a un correo y lo envía. No lee
la base, no recalcula matches y no decide a quién alertar.

## 2. Por qué es manual

- Microsoft retiró Power Automate para cuentas personales (`outlook.com`) el
  27 de julio de 2025. La cuenta personal ya no puede entrar al portal.
- El tenant UNMSM no tiene un OneDrive usable: el navegador cae en
  `PolicyViolationThrottle.htm`. Sin almacenamiento en la nube no hay flujo
  programado que lea el archivo.
- El trigger HTTP es Premium. No se usa.
- Power Automate Desktop está instalado, pero exige un flujo de escritorio y
  la PC encendida; no se implementó en este checkpoint.

Por eso v0.2 usa el **flujo manual estándar** de Power Automate: el usuario
exporta, ejecuta el flujo y adjunta el archivo.

## 3. Diseño del flujo

| Parte | Configuración |
|---|---|
| Nombre | `PractiCV Recordatorios` |
| Entorno | UNMSM (cuenta work/school) |
| Trigger | `Manually trigger a flow`, input **File** llamado `Export PractiCV` |
| Acción | `Send an email (V2)` — Office 365 Outlook |
| Conexión | `PractiCV Outlook` |
| Destinatario | correo configurado en el flujo (no se versiona) |
| Asunto | `PractiCV: recordatorios de postulaciones` |
| Adjunto · nombre | `Export PractiCV name` |
| Adjunto · contenido | `Export PractiCV contentBytes` |
| Body | texto fijo que aclara que el envío es manual |

El flujo no usa OneDrive, SharePoint, HTTP trigger ni conectores Premium.

## 4. Cómo ejecutarlo

1. En PractiCV, exporta el calendario `.ics` o el CSV de postulaciones.
2. Power Automate → **My flows** → `PractiCV Recordatorios` → **Run**.
3. Adjunta el archivo exportado y ejecuta.
4. Revisa el correo y el historial de ejecuciones.

## 5. Evidencia

- Ejecución del **2026-11-23 12:19**, duración **985 ms**, estado **Succeeded**.
- Adjunto de prueba: `calendar.ics` (2.7 KB) generado por el E2E de v0.1.
- Captura: `docs/assets/power-automate-run.png`.
- Intentos previos (12:12 y 12:15) fallaron con `Unauthorized` por la conexión;
  se recreó la conexión `PractiCV Outlook` y la tercera ejecución pasó.
- El correo llegó al buzón del destinatario a las 12:19. Outlook lo clasificó
  como **correo no deseado** y bloqueó el `.ics` (ver sección 7).

La captura muestra el historial de ejecuciones, no el buzón. La recepción del
correo se confirma en el cliente de correo del destinatario.

## 6. Límites

- **Manual:** hay que ejecutar el flujo y adjuntar el archivo cada vez.
- **Sin deduplicación:** el ICS/CSV ya viene del export de PractiCV.
- **Sin programación:** no hay scheduler ni lectura de una carpeta.
- **Un archivo por ejecución:** el flujo adjunta el archivo del trigger; no
  adjunta ICS y CSV a la vez.
- **Reautenticación:** si el tenant invalida la conexión, el flujo falla con
  `Unauthorized`; hay que volver a conectar `PractiCV Outlook`.
- **Filtro del buzón:** Outlook puede mandar el correo a no deseado y bloquear
  el adjunto `.ics`.
- **Sin secretos en el repo:** la conexión y el destinatario viven en Power
  Automate, no en Git.
- **PII:** la documentación y la captura no incluyen direcciones de correo.

## 7. Problema conocido: Outlook bloquea el `.ics`

En la prueba real el correo cayó en **Correo no deseado** y Outlook mostró
"Los datos adjuntos de este mensaje se han bloqueado por su seguridad". No es un
fallo del flujo: es una política del cliente de correo.

Workarounds:

1. Marcar el mensaje como **No es correo no deseado** y agregar el remitente a
   remitentes seguros.
2. Si el `.ics` sigue bloqueado, comprimirlo en `.zip` antes de ejecutar el
   flujo.
3. Para el Kanban, enviar el CSV; suele ser menos propenso al bloqueo.
4. También se puede abrir el `.ics` desde el export local sin pasar por correo.

El cuerpo del correo aclara que se adjunta **el calendario `.ics` o el CSV**,
porque el flujo acepta un archivo por ejecución.

## 8. Reproducirlo

1. Crear un flujo instantáneo en la cuenta UNMSM.
2. Añadir `Manually trigger a flow` y un input de tipo **File**.
3. Añadir `Send an email (V2)` con la conexión de Outlook.
4. Configurar asunto, cuerpo y destinatario.
5. En `Attachments`, usar el nombre y el contenido del archivo del trigger.
6. Guardar, ejecutar con un export real y verificar el estado.
