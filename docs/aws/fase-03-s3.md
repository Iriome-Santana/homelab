# AWS — Fase 03 S3 (más Labs)

## Qué es S3 y qué problema resuelve

Antes de la nube guardar archivos tenía tres problemas:

Límite de espacio: un servidor tiene un disco de tamaño fijo
Disponibilidad: si el servidor falla, los archivos no son accesibles
Acceso: los archivos solo son accesibles desde la red donde está el servidor

## S3 — Simple Storage Service resuelve los tres.
No tiene límite práctico de espacio, replica cada archivo automáticamente
en múltiples datacenters dentro de la región, y cualquier cosa con internet puede acceder mediante HTTP.

AWS garantiza 99.999999999% de durabilidad. Si guardas 10 millones de objetos,
estadísticamente perderías uno cada 10.000 años.

## Almacenamiento de objetos vs disco duro

Este es el concepto más importante para entender S3 correctamente.

Disco duro (EBS): almacenamiento en bloque. Tiene sectores, sistema de archivos,
directorios reales. Puedes abrir un archivo y modificar una línea en el medio.
Es lo que usa tu EC2.

S3: almacenamiento de objetos. No hay sistema de archivos, no hay sectores,
no hay directorios reales. Es completamente plano por dentro.
Cada objeto tiene tres cosas:

Key:       logs/2026/marzo/app.log     → identificador único del objeto
Content:   los bytes del archivo       → el contenido
Metadata:  tamaño, fecha, content-type → información sobre el objeto

Las barras en la key parecen carpetas pero no lo son. La consola las muestra
como carpetas para facilitar la navegación, pero si preguntas a la API no existe
ningún directorio, solo objetos con keys que contienen barras.

En la CLI aparecen como PRE (prefix), no como directorios reales.
Consecuencia práctica importante: no puedes modificar un objeto parcialmente.
Si quieres cambiar una línea, tienes que descargar el objeto completo,
modificarlo y subir el objeto completo de nuevo.
Por eso S3 no es adecuado para bases de datos, pero es perfecto para
backups, logs, imágenes y archivos estáticos.

## Buckets

Contenedor de objetos. Antes de subir cualquier archivo necesitas crear un bucket.

Reglas:

El nombre es global en todo AWS: no puede haber dos buckets con el mismo nombre
en el mundo entero, en ninguna cuenta, en ninguna región
Solo letras minúsculas, números y guiones
Entre 3 y 63 caracteres
Pertenece a una región específica, los datos físicamente están ahí

En empresas reales los buckets siguen convenciones de nombres:
empresa-produccion-backups-db
empresa-staging-assets-web
empresa-logs-aplicacion-2026

## Privacidad por defecto

Todo objeto en S3 es privado por defecto.

Si alguien intenta acceder a su URL sin credenciales recibe AccessDenied.
AWS activa Block Public Access en todos los buckets nuevos.
Aunque quieras hacer algo público, tienes que desactivar esta protección primero.
Es una red de seguridad para evitar exponer datos accidentalmente.
Verificado en el lab: intentar acceder desde el navegador devuelve:

<Code>AccessDenied</Code>
<Message>Access Denied</Message>

S3 responde en XML porque es una API HTTP, no un servidor web tradicional.
En producción Block Public Access siempre está activado salvo en buckets
de hosting estático donde la exposición pública es intencionada.

## Storage Classes

No todos los datos se acceden igual. Guardar logs de hace 3 años con la misma
clase que los logs de hoy es desperdiciar dinero.

# S3 Standard

Acceso frecuente. Máxima disponibilidad y rendimiento.
Ejemplos: imágenes de una web activa, logs del día actual.
Coste: más alto por GB, sin coste por lectura.

# S3 Standard-IA (Infrequent Access)

Acceso infrecuente pero necesitas disponibilidad inmediata cuando lo pides.

Ejemplos: backups de la semana pasada, logs del mes anterior.
Coste: más barato por GB, cobra por cada GB leído.

# S3 Glacier Instant Retrieval

Acceso muy infrecuente, menos de una vez al trimestre, pero acceso instantáneo.
Ejemplos: backups mensuales, datos de auditoría del año pasado.
Coste: muy barato por GB, cobra más por lectura.

# S3 Glacier Flexible Retrieval

Archivado a largo plazo. El acceso tarda entre minutos y horas.
Ejemplos: logs de hace 2 años, documentos legales que debes guardar 7 años.
Coste: muy barato, pero la espera puede ser de horas.

# S3 Intelligent-Tiering

AWS monitoriza el patrón de acceso de cada objeto y lo mueve automáticamente.
Si no se accede en 30 días lo baja a IA. Si alguien lo accede lo sube a Standard.
Para cuando no sabes con qué frecuencia se accederá a los datos.
Tiene coste adicional pequeño por objeto monitoreado.

## Lifecycle Policies vs Intelligent-Tiering — diferencia clave

Lifecycle Policies: mueven objetos basándose en el TIEMPO.
No importa si el archivo se ha accedido o no.
Tú defines la regla y es determinista y predecible.
Día 0-30:   Standard    (siempre, haya accesos o no)
Día 30-90:  Standard-IA (siempre, haya accesos o no)
Día 90+:    Glacier     (siempre, haya accesos o no)

Úsalas cuando el patrón de acceso es predecible.

Intelligent-Tiering: mueve objetos basándose en el PATRÓN DE ACCESO REAL.
Día 35 sin accesos → baja a IA automáticamente
Día 40 alguien accede → sube a Standard automáticamente
Día 75 sin accesos → baja a IA de nuevo

Úsalo cuando no sabes con qué frecuencia se accederá a los datos.

## Versioning

S3 puede guardar todas las versiones de un objeto.
Cuando activas versioning y sobreescribes un archivo, S3 no borra la versión
anterior, la guarda con un ID de versión distinto.

Subir config.json v1  →  ID: abc123
Subir config.json v2  →  ID: def456  (v1 sigue existiendo)
Subir config.json v3  →  ID: ghi789  (v1 y v2 siguen existiendo)

Si borras un objeto con versioning activado, S3 añade un delete marker
pero no borra las versiones anteriores. Puedes recuperar el archivo
borrando el delete marker.

El versioning no existe para facilitar la edición, existe para protegerte de errores.
Es una red de seguridad, no una herramienta de edición.

### Casos reales donde el versioning salva el día:

Script con bug sobreescribe 10.000 archivos con datos incorrectos → recuperas versiones anteriores
Desarrollador borra accidentalmente configuración de producción → restauras en 2 minutos
Ransomware cifra todos los archivos del bucket → restauras versiones anteriores al cifrado

El coste aumenta porque guardas múltiples versiones.
En producción se combina con lifecycle policies que eliminan versiones antiguas.

## Bucket Policies

Documentos JSON que definen quién puede hacer qué en el bucket.
Similares a las IAM policies pero aplicadas al recurso en lugar del usuario.
Ejemplo usado en el lab de hosting estático:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::web-estatica-iriome-2026/*"
    }
  ]
}

Allow, cualquier persona (*), solo GetObject (leer), sobre todos los objetos.
Cualquiera puede leer, nadie puede escribir ni borrar.
Ejemplo de bucket policy restrictiva (solo acceso desde una VPC):

{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": ["arn:aws:s3:::mi-bucket", "arn:aws:s3:::mi-bucket/*"],
  "Condition": {
    "StringNotEquals": {
      "aws:SourceVpc": "vpc-0072281808b62d0bc"
    }
  }
}

En producción los buckets con datos sensibles tienen políticas así.

## Static Website Hosting

S3 puede servir una web estática directamente sin ningún servidor.
HTML, CSS y JavaScript se sirven directamente desde S3 al navegador.

Antes:  Usuario → EC2 (servidor) → sirve HTML
Ahora:  Usuario → S3 → sirve HTML directamente

No hay EC2, no hay sistema operativo que mantener, no hay parches de seguridad.
Si recibe un millón de visitas, S3 escala automáticamente.
Limitación: solo funciona para webs completamente estáticas.
Si necesitas lógica de servidor (login, base de datos), necesitas algo más.

URL del hosting estático:
http://BUCKET.s3-website-REGION.amazonaws.com
http://web-estatica-iriome-2026.s3-website-eu-west-1.amazonaws.com
Para activarlo hay que:

Desactivar Block Public Access (intencionado y consciente)
Activar website hosting con index y error document
Añadir bucket policy que permita s3:GetObject a Principal: "*"


## Presigned URLs

Permiten dar acceso temporal a un objeto privado sin exponer credenciales
ni hacer el objeto público.
Flujo en producción real:
Usuario pide descargar su factura
    │
Tu servidor genera Presigned URL con expiración de 10 minutos
    │
Le devuelves la URL al usuario
    │
El usuario descarga directamente desde S3
    │
La URL expira, nadie más puede usarla
Tu servidor nunca descarga el archivo ni consume ancho de banda.
AWS verifica la firma criptográfica y el tiempo de expiración en cada petición.

Con boto3:
pythonurl = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'mi-bucket', 'Key': 'facturas/cliente-123.pdf'},
    ExpiresIn=600  # 10 minutos en segundos
)

## S3 + CloudFront

CloudFront es la CDN de AWS. Red de servidores distribuidos por todo el mundo
que cachean contenido cerca de los usuarios.

Sin CloudFront:
Usuario en Tokyo → S3 en Irlanda → 200ms de latencia cada vez

Con CloudFront:
Primera petición:   Usuario Tokyo → Edge Location Tokyo → no tiene caché → S3 Irlanda → guarda caché
Siguientes:         Usuario Tokyo → Edge Location Tokyo → sirve desde caché → 5ms
Más de 400 Edge Locations en todo el mundo.
Arquitectura estándar en producción para contenido estático:
S3 (origen, privado, Block Public Access activado)
    │
    └→ CloudFront (distribución)
          ├→ Edge Location Europa
          ├→ Edge Location América
          └→ Edge Location Asia

El bucket permanece privado. CloudFront accede mediante Origin Access Control (OAC),
una identidad especial que AWS crea para que CloudFront lea el bucket
sin que nadie más pueda acceder directamente.

### Ventajas adicionales sobre S3 directo:

HTTPS con tu propio dominio y certificado SSL gratuito de ACM
Coste menor a escala: CloudFront cobra menos por GB que S3 directo
y la caché reduce peticiones al origen


## Comandos útiles S3

### Crear bucket
aws s3api create-bucket \
  --bucket NOMBRE --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1

### Verificar Block Public Access
aws s3api get-public-access-block --bucket NOMBRE

### Subir archivo
aws s3 cp archivo.txt s3://BUCKET/carpeta/archivo.txt

### Subir carpeta entera
aws s3 cp carpeta/ s3://BUCKET/carpeta/ --recursive

### Listar objetos
aws s3 ls s3://BUCKET/
aws s3 ls s3://BUCKET/carpeta/

### Tamaño total del bucket
aws s3 ls s3://BUCKET/ --recursive --human-readable --summarize

### Descargar objeto
aws s3 cp s3://BUCKET/archivo.txt ./archivo.txt

### Borrar objeto
aws s3 rm s3://BUCKET/archivo.txt

### Sincronizar carpeta local con bucket
aws s3 sync carpeta/ s3://BUCKET/carpeta/

# Labs realizados

## Lab 1 — Bucket, objetos y privacidad

Creado bucket s3-labs-iriome-2026 en eu-west-1
Verificado Block Public Access activado por defecto
Subidos objetos en distintas rutas (logs/, configs/, backups/)
Verificado que los objetos son privados: el navegador devuelve AccessDenied
Entendido que los PRE en el listado son prefijos, no carpetas reales

## Lab 2 — Static Website Hosting

Creado bucket web-estatica-iriome-2026
Desactivado Block Public Access conscientemente
Creado index.html y error.html
Activado website hosting con IndexDocument y ErrorDocument
Añadida bucket policy con s3:GetObject para Principal *
Web accesible desde el navegador sin ningún servidor
Página 404 personalizada funcionando


### Lo que aprendí rompiendo cosas

Desactivar Block Public Access no hace los objetos públicos automáticamente.

Son dos pasos separados e independientes:

Desactivar Block Public Access (permite que existan políticas públicas)
Añadir bucket policy con Allow GetObject a * (hace los objetos públicos)
Si haces solo el paso 1 sin el paso 2, los objetos siguen siendo privados.
AWS diseñó esto así intencionadamente para evitar exposiciones accidentales.

### Cuándo lo usaría en trabajo real

Backups del Expense Tracker → s3-labs con lifecycle policy Standard → IA → Glacier
Assets estáticos de una web → S3 + CloudFront delante
Artefactos de CI/CD (imágenes Docker, binarios compilados) → bucket privado
Terraform remote state → bucket privado con versioning activado
Logs de aplicación → bucket con lifecycle policy que mueve a Glacier y borra después de X días
Compartir archivos con clientes o usuarios temporalmente → Presigned URLs

## Lab 3 — Lifecycle Policies

### Qué es una Lifecycle Policy y qué problema resuelve

Una Lifecycle Policy es una regla automática que mueve o elimina objetos
según su antigüedad, sin intervención manual.

Sin lifecycle policy un bucket de backups crece indefinidamente:
```
Mes 1:   10 GB  →  $0.23/mes
Año 1:  120 GB  →  $2.76/mes
Año 3:  360 GB  →  $8.28/mes   (la mayoría son backups que nunca tocas)
```

Con lifecycle policy los objetos se mueven automáticamente a clases más baratas
y se eliminan cuando ya no tienen valor:
```
Día 0-30:    Standard    →  acceso frecuente, verificación de backups recientes
Día 30-90:   Standard-IA →  ya raramente los necesitas, más barato
Día 90-180:  Glacier     →  archivado, casi nunca se toca, muy barato
Día 180+:    Eliminar    →  ya no tiene valor retenerlos
```

El ahorro a escala es enorme y ocurre automáticamente sin que toques nada.

### Lifecycle Policies vs Intelligent-Tiering — diferencia clave

```
Lifecycle Policies:     mueven por TIEMPO
                        no importa si el archivo se accedió o no
                        determinista y predecible
                        para patrones de acceso predecibles
                        sin coste adicional de monitorización

Intelligent-Tiering:    mueve por PATRÓN DE ACCESO REAL
                        si no se accede en 30 días → baja a IA
                        si alguien lo accede → sube a Standard
                        para patrones de acceso impredecibles
                        tiene coste adicional por objeto monitoreado
```

### Estructura del JSON de una Lifecycle Policy

```
{
  "Rules": [
    {
      "ID": "backups-lifecycle",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "backups/"
      },
      "Transitions": [
        { "Days": 30,  "StorageClass": "STANDARD_IA" },
        { "Days": 90,  "StorageClass": "GLACIER" }
      ],
      "Expiration": {
        "Days": 180
      }
    },
    {
      "ID": "logs-lifecycle",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "logs/"
      },
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

Cada campo tiene su significado:
- `ID`: nombre de la regla, un bucket puede tener múltiples reglas
- `Status`: Enabled o Disabled, puedes desactivar sin borrar
- `Filter.Prefix`: a qué objetos aplica, sin filtro aplica a todo el bucket
- `Transitions`: movimientos entre clases, los días deben ir en orden ascendente
- `Expiration.Days`: después de X días el objeto se elimina automáticamente

### Campo TransitionDefaultMinimumObjectSize
AWS añade automáticamente `"TransitionDefaultMinimumObjectSize": "all_storage_classes_128K"`.
Significa que las transiciones solo aplican a objetos de más de 128KB.
Objetos muy pequeños no se mueven porque el coste de gestionar la transición
sería mayor que el ahorro. Es comportamiento por defecto de AWS, no algo que configuras.

### Comportamiento importante
Los objetos no se mueven inmediatamente al aplicar la política.
AWS evalúa las reglas una vez al día a medianoche UTC.
Los objetos cumplen la antigüedad desde su fecha de creación, no desde que se creó la regla.

### Comandos
```
# Aplicar lifecycle policy desde archivo JSON
aws s3api put-bucket-lifecycle-configuration \
  --bucket BUCKET \
  --lifecycle-configuration file://lifecycle-policy.json

# Ver la lifecycle policy activa
aws s3api get-bucket-lifecycle-configuration --bucket BUCKET
```

### Lo que se configuró en el lab
```
Bucket: s3-labs-iriome-2026

Regla backups-lifecycle (aplica a backups/*):
  Día 30  → STANDARD_IA
  Día 90  → GLACIER
  Día 180 → Eliminar

Regla logs-lifecycle (aplica a logs/*):
  Día 30  → Eliminar
```

Reglas distintas para distintos tipos de datos porque cada uno tiene
un ciclo de vida diferente. Los backups se archivan, los logs simplemente
se eliminan porque pasado un mes no tienen valor.

---

## Lab 4 — Versioning

### Qué es el Versioning y qué problema resuelve

Sin versioning cualquier sobreescritura o borrado es destructivo e irreversible:
```
Sin versioning:
  Sobreescribir → versión anterior desaparece para siempre
  Borrar        → objeto desaparece para siempre
```

Con versioning S3 guarda todas las versiones de un objeto:
```
Con versioning:
  Sobreescribir → nueva versión creada, anteriores conservadas con VersionId único
  Borrar        → añade DeleteMarker, todas las versiones conservadas
  Recuperar     → descargar versión específica o borrar el DeleteMarker
```

### El DeleteMarker

Cuando borras un objeto con versioning activado, S3 no borra nada.
Añade un DeleteMarker: una etiqueta especial que hace que el objeto
parezca borrado cuando lo listas normalmente.

```
aws s3 rm objeto.txt  →  añade DeleteMarker (IsLatest: True)
aws s3 ls             →  no muestra el objeto (parece borrado)
list-object-versions  →  muestra todas las versiones + el DeleteMarker
```

Para recuperar el objeto simplemente borras el DeleteMarker.
Al borrarlo el objeto vuelve y la versión actual es la última antes del borrado.

### Versiones de objetos creados antes de activar versioning

Los objetos que existían antes de activar versioning aparecen con `VersionId: null`.
AWS los conserva pero sin VersionId porque se crearon cuando versioning estaba desactivado.

### Cuándo activar versioning y cuándo no

**Activar siempre:**
```
Terraform state file      → si se corrompe tu infraestructura queda inconsistente
Configuraciones críticas  → un error puede tumbar producción
Certificados y secrets    → irremplazables si se pierden
Backups importantes       → la razón de existir de un backup es poder recuperarlo
```

**No activar:**
```
Logs de aplicación        → se escriben millones de veces, nunca se sobreescriben
                            versioning no aporta nada pero añade coste
Artefactos CI/CD          → se generan constantemente, tienen lifecycle policy corta
Assets web con cambios    → si hay miles de imágenes que cambian frecuentemente
frecuentes                  el coste de almacenar versiones se multiplica rápido
```

**Regla práctica:**
```
¿Perder o corromper este objeto causaría un problema grave?
  Sí → activa versioning
  No → no lo activas, o usa lifecycle policy para limpiar versiones antiguas
```

### Casos reales donde el versioning salva el día
- Script con bug sobreescribe 10.000 archivos → recuperas versiones anteriores
- Desarrollador borra configuración de producción → restauras en 2 minutos
- Ransomware cifra todos los archivos → restauras versiones anteriores al cifrado

### Comandos
```
# Activar versioning
aws s3api put-bucket-versioning \
  --bucket BUCKET \
  --versioning-configuration Status=Enabled

# Verificar que está activo
aws s3api get-bucket-versioning --bucket BUCKET

# Ver todas las versiones de un objeto (formato limpio)
aws s3api list-object-versions \
  --bucket BUCKET \
  --prefix ruta/objeto.txt \
  --query "{Versions: Versions[*].{VersionId:VersionId,IsLatest:IsLatest,Size:Size}, \
           DeleteMarkers: DeleteMarkers[*].{VersionId:VersionId,IsLatest:IsLatest}}" \
  --output table

# Descargar versión específica
aws s3api get-object \
  --bucket BUCKET \
  --key ruta/objeto.txt \
  --version-id ID-DE-LA-VERSION \
  archivo-recuperado.txt

# Borrar versión específica o DeleteMarker
aws s3api delete-object \
  --bucket BUCKET \
  --key ruta/objeto.txt \
  --version-id ID-A-BORRAR
```

### Lo que se demostró en el lab
```
1. Subido config-backup.txt tres veces con contenido diferente
   → tres versiones con VersionIds distintos conservadas

2. Descargada la v1 aunque había dos versiones más recientes encima
   → recuperación de versión específica funciona

3. Borrado el objeto con aws s3 rm
   → aws s3 ls no lo muestra (parece borrado)
   → list-object-versions muestra DeleteMarker + todas las versiones intactas

4. Borrado el DeleteMarker
   → objeto vuelve con la última versión antes del borrado (57 bytes, v3)
```

---

## Lab 5 — Presigned URLs con boto3

### Qué son las Presigned URLs y qué problema resuelven

Para dar acceso a un objeto privado hay opciones malas y una buena:

```
Opción mala 1: hacer el objeto público
               → cualquiera con la URL puede accederlo para siempre

Opción mala 2: descargar en tu servidor y enviarlo al cliente
               → tu servidor consume ancho de banda y CPU innecesariamente

Opción buena:  Presigned URL
               → acceso temporal y firmado criptográficamente
               → solo quien tiene el enlace puede acceder
               → expira en el tiempo que tú decides
               → el cliente descarga directamente desde S3 sin pasar por tu servidor
```

### Cómo funciona por dentro

```
Tu servidor genera Presigned URL con expiración de X segundos
    │
    └→ AWS firma la URL con tus credenciales + timestamp de expiración
           │
           └→ Le mandas la URL al cliente
                  │
                  └→ El cliente hace GET directamente a S3
                         │
                         └→ AWS verifica la firma y el tiempo
                                │
                                ├→ Válida  → devuelve el objeto
                                └→ Expirada → AccessDenied
```

Tu servidor nunca descarga el archivo ni consume ancho de banda.

### Verificado en el lab
```
URL directa:    AccessDenied  → el objeto es privado, Block Public Access activo
Presigned URL:  contenido     → acceso temporal autorizado con firma criptográfica
```

El bucket siguió siendo privado en todo momento.
La Presigned URL dio acceso temporal solo a ese objeto específico.

### Por qué se generó desde la EC2 con IAM Role

En producción el servidor de aplicación genera las Presigned URLs en runtime
usando el IAM Role asignado. No hay credenciales hardcodeadas en el código.
boto3 obtiene las credenciales del Role automáticamente igual que en el Lab 5 de EC2.

### Error encontrado y lección aprendida
Al intentar subir el archivo desde la EC2 con `ec2-s3-readonly-role`:
```
AccessDenied: not authorized to perform: s3:PutObject
```
El Role solo tiene permisos de lectura. No puede escribir en S3.
Solución: subir el archivo desde la máquina local con devops-admin
que sí tiene permisos de escritura.

En producción real esto es correcto: el servidor de aplicación solo necesita
leer objetos y generar URLs. Otro servicio con permisos específicos se encarga
de subir los archivos. Mínimo privilegio por diseño.

### Código boto3
```
import boto3
from datetime import datetime

s3 = boto3.client('s3', region_name='eu-west-1')

url = s3.generate_presigned_url(
    'get_object',                          # operación: descargar objeto
    Params={
        'Bucket': 's3-labs-iriome-2026',
        'Key': 'facturas/factura-cliente-123.txt'
    },
    ExpiresIn=3600                         # expira en 1 hora (segundos)
)

print(url)
# Devuelve URL con parámetros de firma:
# ?X-Amz-Algorithm=AWS4-HMAC-SHA256
# &X-Amz-Credential=...
# &X-Amz-Expires=3600
# &X-Amz-Signature=...   ← firma criptográfica que AWS verifica
```

### Casos de uso reales
```
Usuario descarga su factura      → Presigned URL 10 minutos
Email con enlace de descarga     → Presigned URL 24 horas
Pipeline CI/CD accede artefacto  → Presigned URL 5 minutos
Compartir archivo con un cliente → Presigned URL 7 días
```

---

## Resumen completo de S3

### Para qué sirve S3 en una arquitectura real
```
Backups de base de datos     → bucket privado + versioning + lifecycle policy
Logs de aplicación           → bucket privado + lifecycle policy (sin versioning)
Assets de web estática       → S3 + CloudFront delante
Terraform remote state       → bucket privado + versioning activado
Artefactos CI/CD             → bucket privado + lifecycle policy corta
Compartir archivos privados  → bucket privado + Presigned URLs
Hosting web sin servidor     → Static website hosting + bucket policy pública
```

### Lo que aprendí en este conjunto de labs

El principio de mínimo privilegio aparece constantemente:
- El Role de EC2 tenía ReadOnly y no podía hacer PutObject → correcto por diseño
- La bucket policy de hosting estático solo permite GetObject, no Put ni Delete
- Los buckets privados tienen Block Public Access activado siempre

Cada permiso que no das es una superficie de ataque que no existe.

### Cuándo lo usaría en trabajo real

- Todo proyecto real en AWS usa S3 para algo: backups, logs, assets o state de Terraform
- Lifecycle policies en todos los buckets con datos que crecen con el tiempo
- Versioning en buckets con datos críticos e irremplazables
- Presigned URLs siempre que necesites dar acceso temporal a objetos privados,
  nunca hacer objetos públicos si no es necesario
- S3 + CloudFront para cualquier contenido estático que sirvas a usuarios finales
