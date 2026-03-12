#Qué es S3 y qué problema resuelve

Antes de la nube guardar archivos tenía tres problemas:

Límite de espacio: un servidor tiene un disco de tamaño fijo
Disponibilidad: si el servidor falla, los archivos no son accesibles
Acceso: los archivos solo son accesibles desde la red donde está el servidor

#S3 — Simple Storage Service resuelve los tres.
No tiene límite práctico de espacio, replica cada archivo automáticamente
en múltiples datacenters dentro de la región, y cualquier cosa con internet puede acceder mediante HTTP.

AWS garantiza 99.999999999% de durabilidad. Si guardas 10 millones de objetos,
estadísticamente perderías uno cada 10.000 años.

#Almacenamiento de objetos vs disco duro

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

#Buckets

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

#Privacidad por defecto

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

#Storage Classes

No todos los datos se acceden igual. Guardar logs de hace 3 años con la misma
clase que los logs de hoy es desperdiciar dinero.

#S3 Standard

Acceso frecuente. Máxima disponibilidad y rendimiento.
Ejemplos: imágenes de una web activa, logs del día actual.
Coste: más alto por GB, sin coste por lectura.

#S3 Standard-IA (Infrequent Access)

Acceso infrecuente pero necesitas disponibilidad inmediata cuando lo pides.

Ejemplos: backups de la semana pasada, logs del mes anterior.
Coste: más barato por GB, cobra por cada GB leído.

#S3 Glacier Instant Retrieval

Acceso muy infrecuente, menos de una vez al trimestre, pero acceso instantáneo.
Ejemplos: backups mensuales, datos de auditoría del año pasado.
Coste: muy barato por GB, cobra más por lectura.

#S3 Glacier Flexible Retrieval

Archivado a largo plazo. El acceso tarda entre minutos y horas.
Ejemplos: logs de hace 2 años, documentos legales que debes guardar 7 años.
Coste: muy barato, pero la espera puede ser de horas.

#S3 Intelligent-Tiering

AWS monitoriza el patrón de acceso de cada objeto y lo mueve automáticamente.
Si no se accede en 30 días lo baja a IA. Si alguien lo accede lo sube a Standard.
Para cuando no sabes con qué frecuencia se accederá a los datos.
Tiene coste adicional pequeño por objeto monitoreado.

#Lifecycle Policies vs Intelligent-Tiering — diferencia clave

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

#Versioning

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

#Casos reales donde el versioning salva el día:

Script con bug sobreescribe 10.000 archivos con datos incorrectos → recuperas versiones anteriores
Desarrollador borra accidentalmente configuración de producción → restauras en 2 minutos
Ransomware cifra todos los archivos del bucket → restauras versiones anteriores al cifrado

El coste aumenta porque guardas múltiples versiones.
En producción se combina con lifecycle policies que eliminan versiones antiguas.

#Bucket Policies

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

#Static Website Hosting

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


#Presigned URLs

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

#S3 + CloudFront

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

#Ventajas adicionales sobre S3 directo:

HTTPS con tu propio dominio y certificado SSL gratuito de ACM
Coste menor a escala: CloudFront cobra menos por GB que S3 directo
y la caché reduce peticiones al origen


##Comandos útiles S3

# Crear bucket
aws s3api create-bucket \
  --bucket NOMBRE --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1

# Verificar Block Public Access
aws s3api get-public-access-block --bucket NOMBRE

# Subir archivo
aws s3 cp archivo.txt s3://BUCKET/carpeta/archivo.txt

# Subir carpeta entera
aws s3 cp carpeta/ s3://BUCKET/carpeta/ --recursive

# Listar objetos
aws s3 ls s3://BUCKET/
aws s3 ls s3://BUCKET/carpeta/

# Tamaño total del bucket
aws s3 ls s3://BUCKET/ --recursive --human-readable --summarize

# Descargar objeto
aws s3 cp s3://BUCKET/archivo.txt ./archivo.txt

# Borrar objeto
aws s3 rm s3://BUCKET/archivo.txt

# Sincronizar carpeta local con bucket
aws s3 sync carpeta/ s3://BUCKET/carpeta/

##Labs realizados

#Lab 1 — Bucket, objetos y privacidad

Creado bucket s3-labs-iriome-2026 en eu-west-1
Verificado Block Public Access activado por defecto
Subidos objetos en distintas rutas (logs/, configs/, backups/)
Verificado que los objetos son privados: el navegador devuelve AccessDenied
Entendido que los PRE en el listado son prefijos, no carpetas reales

#Lab 2 — Static Website Hosting

Creado bucket web-estatica-iriome-2026
Desactivado Block Public Access conscientemente
Creado index.html y error.html
Activado website hosting con IndexDocument y ErrorDocument
Añadida bucket policy con s3:GetObject para Principal *
Web accesible desde el navegador sin ningún servidor
Página 404 personalizada funcionando


#Lo que aprendí rompiendo cosas

Desactivar Block Public Access no hace los objetos públicos automáticamente.

Son dos pasos separados e independientes:

Desactivar Block Public Access (permite que existan políticas públicas)
Añadir bucket policy con Allow GetObject a * (hace los objetos públicos)
Si haces solo el paso 1 sin el paso 2, los objetos siguen siendo privados.
AWS diseñó esto así intencionadamente para evitar exposiciones accidentales.

#Cuándo lo usaría en trabajo real

Backups del Expense Tracker → s3-labs con lifecycle policy Standard → IA → Glacier
Assets estáticos de una web → S3 + CloudFront delante
Artefactos de CI/CD (imágenes Docker, binarios compilados) → bucket privado
Terraform remote state → bucket privado con versioning activado
Logs de aplicación → bucket con lifecycle policy que mueve a Glacier y borra después de X días
Compartir archivos con clientes o usuarios temporalmente → Presigned URLs
