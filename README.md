# Aureola Scanner

![AUREOLA Scanner Banner](assets/aureola_banner.png)

Aureola Scanner es un avanzado escáner de seguridad web diseñado para identificar vulnerabilidades en aplicaciones web. Realiza múltiples comprobaciones, incluyendo la detección de exposición de datos sensibles, formularios inseguros y posibles exploits.
# Demostracion de escaneo simple
![Demo de Aureola Scanner](assets/Example.gif)

---

## ⚠️ Aviso Legal y Ético

> **Uso exclusivo para fines educativos y de investigación**  
> Esta herramienta ha sido creada únicamente con el propósito de demostrar la potencia de la inteligencia artificial aplicada a la ciberseguridad y la automatización.  
> **Aureola Scanner está destinada solo para pruebas en entornos propios, laboratorios, sistemas bajo tu control o con autorización explícita.**
>
> - **No utilices esta herramienta para atacar, dañar o comprometer sistemas de terceros sin permiso.**
> - El uso irresponsable, ilegal o malintencionado está estrictamente prohibido.
> - El creador y colaboradores de Aureola Scanner **no se hacen responsables** de cualquier daño, pérdida o consecuencia derivada del uso de este software.
>
> **¡Respeta la ley y la ética profesional!**

---

## 🛠️ Roadmap y Estado

> **Mantenimiento:**  
> Este script recibirá mantenimiento y actualizaciones periódicas a lo largo del tiempo, hasta que decida enfocar mis esfuerzos en herramientas más modernas o alternativas.  
> ¡Sigue el repositorio para estar al tanto de futuras mejoras, nuevas funciones y avisos importantes!

---

> **⚠️ Nota de compatibilidad:**  
> Para la mejor experiencia visual y funcional, se recomienda ejecutar Aureola Scanner desde **PowerShell en Windows**.  
> Actualmente, el programa **solo tiene soporte para Windows**. El soporte para otros sistemas operativos podría añadirse en el futuro.

---

## 🤖 Sobre la creación del proyecto

> **Nota importante:**  
> Este script ha sido creado y potenciado principalmente con la ayuda de inteligencias artificiales, como **ChatGPT** y **GitHub Copilot**.  
> El objetivo es demostrar cómo las herramientas de IA pueden acelerar el desarrollo de soluciones de ciberseguridad y automatización.

---

## Tabla de Contenidos
- [Características](#características)
- [Instalación](#instalación)
- [Uso](#uso)
- [Configuración Avanzada](#configuración-avanzada)
- [Ejemplos](#ejemplos)
- [Preguntas Frecuentes](#preguntas-frecuentes)
- [Contribuir](#contribuir)
- [Licencia](#licencia)
- [Agradecimientos](#agradecimientos)
- [Contacto](#contacto)

## Características
- Escaneo de datos sensibles como correos, claves API y contraseñas.
- Detección de formularios inseguros y posibles vulnerabilidades XSS.
- Soporte para técnicas avanzadas de evasión de firewalls (WAF).
- Generación de reportes detallados en múltiples formatos (HTML, JSON, TXT).
- Soporte para autenticación (cookies, tokens, HTTP Auth).
- Escaneo multihilo y personalización de profundidad.
- Integración con CI/CD y automatización mediante scripts.

## Instalación

1. Clona el repositorio:
   ```
   git clone https://github.com/iPhersa/Aureolas.git
   ```
2. Accede al directorio del proyecto:
   ```
   cd Aureolas
   ```
3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

## Uso

Ejecuta el escáner con el siguiente comando básico:
```
python main.py --url http://example.com --depth 2 --threads 5
```

### Opciones principales

- `--url`: URL objetivo a escanear.
- `--depth`: Profundidad de escaneo (por defecto: 2).
- `--threads`: Número de hilos para el escaneo (por defecto: 5).
- `--output`: Ruta del archivo de reporte.
- `--format`: Formato del reporte (`html`, `json`, `txt`).
- `--auth`: Archivo o string de autenticación.
- `--exclude`: Lista de rutas a excluir.

## Configuración Avanzada

> **Nota:** Actualmente, `main.py` **no permite la ejecución de configuraciones personalizadas** mediante archivos YAML o JSON. Todas las opciones deben pasarse como argumentos en la línea de comandos.

```yaml
target: "http://example.com"
depth: 3
threads: 10
output: "report.html"
format: "html"
auth:
  type: "token"
  value: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
exclude:
  - "/logout"
  - "/admin"
```

## Ejemplos


- Escaneo rápido con reporte en JSON:
  ```
  python main.py --url http://test.com --format json --output resultado.json
  ```
- Escaneo autenticado:
  ```
  python main.py --url http://test.com --auth "cookie:sessionid=abc123"
  ```
- Integración en CI/CD (GitHub Actions):
  ```yaml
  - name: Ejecutar Aureola Scanner
    run: python main.py --url ${{ secrets.TARGET_URL }} --output report.html
  ```

### Ejemplos avanzados

- Escaneo profundo con múltiples hilos y exclusión de rutas sensibles:
  ```
  python main.py --url https://victima.com --depth 4 --threads 15 --exclude /logout /admin /private
  ```

- Escaneo con autenticación básica HTTP y proxy:
  ```
  python main.py --url https://intranet.empresa.com --user admin --password SuperSecret --proxy http://127.0.0.1:8080
  ```

- Escaneo con cabeceras y cookies personalizadas (simulación de sesión real):
  ```
  python main.py --url https://portal.com --headers "X-Bypass:yes" "X-Requested-With:XMLHttpRequest" --cookies "sessionid=abc123" "csrftoken=xyz789"
  ```

- Escaneo forzando método POST y timeout personalizado:
  ```
  python main.py --url https://api.objetivo.com --method POST --timeout 25
  ```

- Escaneo silencioso y guardando solo vulnerabilidades detectadas:
  ```
  python main.py --url https://objetivo.com --silent --only-vulns --output vulns.txt
  ```

- Escaneo de una API REST autenticada por token:
  ```
  python main.py --url https://api.empresa.com/v1/users --headers "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  ```

- Escaneo de un entorno staging con reporte HTML:
  ```
  python main.py --url https://staging.sitio.com --output reporte_staging.html --format html
  ```

- Escaneo de una aplicación con autenticación por JWT y exclusión de rutas administrativas:
  ```
  python main.py --url https://app.com --headers "Authorization: Bearer <jwt_token>" --exclude /admin /settings
  ```

- Escaneo de un sitio con verificación SSL desactivada (entornos de pruebas):
  ```
  python main.py --url https://dev.local --no-verify-ssl
  ```

- Escaneo masivo de múltiples objetivos (usando un script externo):
  ```python
  # scan_multiple.py
  import os
  targets = ["https://site1.com", "https://site2.com", "https://site3.com"]
  for t in targets:
      os.system(f"python main.py --url {t} --output report_{t.replace('https://','').replace('.','_')}.txt")
  ```

## Preguntas Frecuentes

**¿Aureola Scanner soporta autenticación?**  
Sí, soporta cookies, tokens y autenticación básica.

**¿Puedo excluir rutas específicas?**  
Sí, usa la opción `--exclude` o configúralo en el archivo de configuración.

**¿Qué formatos de reporte están disponibles?**  
HTML, JSON y TXT.

## Contribuir

¡Las contribuciones son bienvenidas! Por favor, abre un issue o envía un pull request para mejoras o correcciones.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más información.

## Agradecimientos

- Gracias a los contribuidores y la comunidad open-source por su apoyo.
- Inspirado por herramientas como OWASP ZAP y Nikto.

## Contacto

¿Tienes dudas o sugerencias?  
- Email: iPhersa@aureola.io
- Twitter: [@iPhersaX](https://twitter.com/AureolaSec)
- Issues: [GitHub Issues](https://github.com/yourusername/Aureola-Scanner/issues)