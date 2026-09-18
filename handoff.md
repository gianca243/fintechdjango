# Handoff — fintechdjango

Documento de contexto para retomar la sesión de trabajo/aprendizaje en este proyecto. Está pensado para que quien lo lea (yo mismo en otra sesión, u otro asistente) entienda las reglas de colaboración, las decisiones de arquitectura tomadas y en qué estado quedó el código, sin tener que re-derivar nada de la conversación original.

## Objetivo del proyecto

`fintechdjango` es un proyecto de **aprendizaje**, no solo un entregable. El usuario está construyendo una app Django + DRF aplicando de forma incremental:

- **TDD** (Test-Driven Development) — escribir tests antes de la implementación.
- **DDD** (Domain-Driven Design) — separación de capas: dominio puro, aplicación/orquestación, infraestructura.
- **SOLID** — introducido de a poco, atado a decisiones concretas de código, no como teoría suelta.

## Reglas de colaboración (importante, no romper)

**El usuario quiere aprender el proceso, no que le escriban el código.** Esta es la regla más importante de la sesión.

Estilo acordado: **"pistas + revisión"**
- Dar una pista conceptual (qué mirar, qué API, qué concepto) — nunca la solución completa.
- El usuario escribe el código.
- Se revisa lo que escribió señalando errores/gaps concretos (con número de línea), sin corregirlo directamente en el archivo.
- Solo se escala a pseudocódigo o un ejemplo mínimo **genérico** (nunca del archivo real) cuando el usuario pide explícitamente que se le explique un concepto nuevo (ej. `Protocol`, `@dataclass`, `__post_init__`, excepciones custom, `Decimal`, stub vs fake, class-based views/`as_view()`, `asdict`).
- Cuando el usuario pregunta algo conceptual, se le explica con un ejemplo genérico no relacionado a su dominio, y después vuelve a escribir él su versión real.
- Cuando el usuario pide explícitamente una opinión de diseño ("¿qué opinás?", "¿voy bien?"), sí se le da una recomendación directa con el razonamiento — pero la decisión final queda en sus manos. El usuario ya viene aplicando por su cuenta criterios de sesiones anteriores a decisiones nuevas (ver ejemplo en el punto 8 de arquitectura) — cuando eso pase, vale la pena nombrarlo explícitamente, refuerza el aprendizaje.
- Excepción: verificaciones diagnósticas de solo lectura (correr `manage.py shell`/`pytest`/test client, `git status`, instalar dependencias o generar migraciones que el usuario pidió/necesita explícitamente) sí las puede hacer el asistente.

## Decisiones de arquitectura tomadas

### 1. Capas: domain / infrastructure / controllers / views (aplicación)

```
fintech/
  domain/            # Python puro, CERO imports de Django
    user.py           # entidad User (dataclass)
    repository.py      # UserRepository (Protocol/contrato)
    exceptions.py       # todas las excepciones de dominio
  infrastructure/      # sabe de Django, implementa los contratos del dominio
    user_repository.py  # DjangoUserRepository (implementa UserRepository)
  controllers/          # capa de orquestación/aplicación
    users.py             # UserController — depende de UserRepository vía DI, nunca de Django directo
  models/                # los models.Model de Django (filas de la tabla)
  views/                  # capa HTTP (DRF APIView) — convierte HttpRequest/Response
                          #   a/desde dicts planos, mapea excepciones de dominio a status codes
  urls.py                 # URLconf de la app fintech, incluido desde senior_test/urls.py
  test/                    # tests con pytest
    fake_repository.py      # fakes en memoria (FakeUserRepository, FakeTransactionRepository)
    test_user_controllers.py
    test_transaction_controllers.py
```

**Por qué esta separación:** Dependency Inversion Principle (la D de SOLID). Los módulos de alto nivel (dominio, orquestación) no dependen de infraestructura (Django); ambos dependen de una abstracción (`Protocol`). La infraestructura implementa esa abstracción, no al revés.

### 2. `User` de dominio: Opción B (DDD puro), no Active Record

Entidad de dominio en Python plano, desacoplada de Django, con un Repository que mapea entre el dominio y el ORM — elegido para poder tener tests unitarios que no toquen la base de datos, y para practicar DI explícitamente.

### 3. `UserRepository` es un `typing.Protocol`, no un `abc.ABC`

**Contrato final** (`domain/repository.py`):
```python
class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User: ...
    def get_by_email(self, email: str) -> User: ...
    def save(self, user: User) -> User: ...
    def exists_by_email(self, email: str) -> bool: ...
```
- Sin `delete` — YAGNI consciente (dominio financiero, probablemente inhabilitar con un campo `active` a futuro en vez de borrar).
- `save` es **upsert único**. `exists_by_email` se agregó para la validación de email duplicado (ver punto 6) — la lógica de negocio de "¿esto es válido?" vive en el controller, no en el repository (`save` no valida nada, solo persiste).
- Lectura por `id` **o** `email`: dos métodos explícitos, no uno flexible.
- No encontrado → excepción propia (`UserNotFound(value, param)`), no `None`.

### 4. Tipos de dinero: `Decimal`, nunca `float`

Django ya usa `Decimal` internamente para `DecimalField`; el dominio sigue el mismo tipo. Construir siempre desde string (`Decimal("0.1")`), nunca desde float.

### 5. Aggregate `User` + `Transaction` — **en construcción activa ahora mismo**

Identificado por el usuario solo: un retiro/depósito necesita crear una `Transaction` **y** actualizar `balance` del `User` **atómicamente**. `User` = Aggregate Root, `Transaction` = miembro del aggregate.

**Decisiones ya tomadas:**
- La entidad `User` va a exponer métodos de comportamiento (`retirar(monto)`, `depositar(monto)`) en vez de que el controller manipule `balance` y cree `Transaction` como pasos sueltos.
- `Transaction` (dominio) necesita: `id`, `user_id`, `amount`, un campo de **dirección** (depósito vs retiro — nombre y valores todavía sin decidir, ver pendientes), y `status` (resultado de la operación: éxito/fallo — para las pruebas actuales solo se usa `"success"`). Importante: `status` (resultado) y el campo de dirección son **dos campos distintos**, no el mismo.
- Se prefirió un campo de dirección explícito en vez de guardar montos negativos — más claro, evita bugs de signo, más parecido a cómo lo hacen sistemas contables reales.
- Validación de fondos suficientes: sí, `retirar()` debe validarlo. Excepción `NotEnoughFunds(balance, withdrawal_value)` ya escrita en `domain/exceptions.py` (typo corregido: era `__ini__`, se arregló a `__init__`).
- **Qué devuelven `retirar()`/`depositar()`:** el usuario propuso primero devolver un "bulto" con monto + nombre/email del user + nuevo balance (pensado para la respuesta HTTP), y se le hizo notar que esto es exactamente el mismo error que ya había descartado con `create_user` (el dominio no debe armar formatos de presentación). Se corrigió solo: ahora la decisión es que `retirar()`/`depositar()` devuelvan la `Transaction` (con su relación al `User` vía `user_id`), y que sea la capa HTTP/vista quien arme cualquier formato de respuesta combinando datos. Confirmado, buen ejemplo de aplicar un criterio ya aprendido a un caso nuevo.
- Cuidado de nomenclatura: hay dos conceptos llamados "transacción" — la entidad de dominio `Transaction` y la transacción de base de datos (`django.db.transaction.atomic`, que se va a necesitar para persistir el aggregate completo).

**⚠️ Pendiente sin resolver — preguntado, sin respuesta todavía:**
1. **¿`User` mutable o inmutable?** Se volvió a preguntar explícitamente ahora que `retirar()`/`depositar()` están en juego (mutable = modifica `self.balance` in-place; inmutable = devuelve un `User` nuevo). **El usuario todavía no contestó esto** — es lo primero para resolver antes de escribir `retirar()`.
2. **Nombre y valores del campo de dirección en `Transaction`** (¿`type`? ¿`direction`? ¿`"DEPOSITO"/"RETIRO"` o en inglés?) — todavía sin decidir.
3. El modelo Django `Transaction` (`models/transaction.py`) todavía no tiene el campo de dirección — cuando se decida el nombre, va a hacer falta otra migración (mismo patrón que se usó para agregar `balance` a `User`, ver "Infraestructura de testing").

**Plan de ataque acordado:** empezar por la pieza más aislada — `User.retirar()`/`depositar()` como comportamiento de dominio puro, testeado directo (sin repository, sin controller, sin fake). Recién después conectar con persistencia del aggregate completo (ahí entra `atomic`, y probablemente un método nuevo en el repository tipo `save_with_transaction` o similar — todavía no discutido en detalle).

### 6. `@dataclass` con `__post_init__` para invariantes de dominio

`domain/user.py` valida en `__post_init__` que `name`/`email` no sean `None` ni `""`, y junta **todos** los campos inválidos en una lista antes de lanzar una sola excepción (`NotAValidUser(fields: list)`) — en vez de cortar en el primer error. Idea del usuario, buena porque da mejor feedback que fallar en el primer campo encontrado.

Se decidió explícitamente **no usar Pydantic** para esto — razonamiento: Pydantic es para validar datos externos en la frontera (rol que ya cumplen los `Serializer` de DRF), no para reglas de negocio de una entidad de dominio; sumarlo ahí duplicaría con lo que DRF ya va a hacer en la vista, y rompería la regla de "dominio sin dependencias externas".

### 7. `request_data` es un `dict` plano — conversión HTTP la hace la vista

`UserController.create_user`/`get_data` reciben dicts simples. La vista (`UserView`) es responsable de convertir `HttpRequest`/DRF `Request` a esos dicts.

### 8. Los métodos de dominio/controller devuelven objetos tipados, nunca dicts armados a mano

`create_user` devuelve el `User` de dominio (no un dict) — razonamiento: un dict pierde autocompletado/chequeo de tipos, y armar el shape de la respuesta es responsabilidad de presentación (DRF `Serializer`s, o `asdict()` + la vista), no del controller (SRP). Mismo criterio aplicado luego por el propio usuario a `retirar()`/`depositar()` (ver punto 5).

### 9. `UserController` no guarda estado de instancia entre llamadas

`create_user` no guarda `self.user`. Consecuencia: `get_data(request_data: dict)` recibe `{"id": ...}` como parámetro (no state guardado), y usa `self.user_repo.get_by_id(...)`. Valida el `id` con una guarda propia (`NotParamsProvided`) antes de llamar al repository.

## Mapeo de excepciones de dominio → HTTP status (ya implementado en `UserView`)

| Excepción | Status | Nota |
|---|---|---|
| `UserNotFound` | 404 | no encontrado |
| `EmailIsRegistered` | 409 Conflict | datos válidos, pero choca con estado existente (no 400) |
| `NotAValidUser` | 400 Bad Request | datos mal formados/faltantes |
| `NotParamsProvided` | 400 Bad Request | falta un parámetro de búsqueda |
| `NotEnoughFunds` | *(todavía sin vista que la use)* | pendiente cuando se conecte `retirar`/`depositar` a HTTP |

Patrón en la vista: cada except arma `Response({"error": str(e)}, status=...)`, reusando el mensaje que cada excepción ya construye en su propio `super().__init__(...)`.

## Class-based views de DRF — concepto cubierto esta sesión

El usuario viene de FastAPI/Express (routing función-por-endpoint) y se explicó la mecánica de Django/DRF: `path()` necesita una función `request -> response`; una clase (`APIView`) no sirve directo, por eso `.as_view()` devuelve una función-dispatcher que internamente elige qué método de la clase llamar (`get`/`post`/etc.) según `request.method`. Un solo `path()` alcanza para todos los verbos que la clase implemente — no se configura por separado. Si el verbo no está implementado, DRF devuelve `405` solo.

**Convención de path param vs. query param** (discutida, la extensión de "buscar por email" quedó explícitamente pospuesta, el usuario dijo "sigamos con las vistas como íbamos"): path param para identidad primaria del recurso (`/user/<int:id>/`), query param para filtros/búsquedas alternativas (`/user/?email=...`). Pendiente si se retoma: extender `get_data` para aceptar `{"email": ...}` además de `{"id": ...}`, despachando a `get_by_email`.

## Infraestructura de testing y HTTP — verificado funcionando de punta a punta

- `pytest` + `pytest-django==4.14.0` instalados, `pytest.ini` con `DJANGO_SETTINGS_MODULE`.
- Se generó y aplicó `fintech/migrations/0002_user_balance.py` (el campo `balance` de `User` nunca había sido migrado desde que se agregó al modelo).
- Se probó el flujo HTTP real completo (vía `django.test.Client`, sin levantar servidor) — los 5 status codes salen correctos: `201` crear, `200` obtener, `404` no encontrado, `409` email duplicado, `400` campos vacíos.
- Convención de nombres de pytest — **recordar siempre**: clases `Test*`, métodos `test_*`. Un nombre mal puesto da "0 tests collected" en silencio, sin error.
- `senior_test/urls.py` usa `path('', include('fintech.urls'))` (prefijo vacío — `fintech/urls.py` ya incluye `"user/"` en sus propios patrones; usar un prefijo no vacío ahí duplicaría el path). `name=` no es compatible con `include()` en el mismo `path()` (rompe el arranque de Django si se combinan).

## Estado actual del código

- ✅ `fintech/domain/user.py` — entidad `User` con `__post_init__` (valida `name`/`email`), completa.
- ✅ `fintech/domain/repository.py` — `Protocol UserRepository` (4 métodos), completo.
- ✅ `fintech/domain/exceptions.py` — 5 excepciones: `UserNotFound`, `EmailIsRegistered`, `NotAValidUser`, `NotParamsProvided`, `NotEnoughFunds`. Todas completas y con el dato relevante guardado en `self`.
- ✅ `fintech/infrastructure/user_repository.py` — `DjangoUserRepository`, completo (los 4 métodos del Protocol).
- ✅ `fintech/controllers/users.py` — `UserController` con `create_user` y `get_data` completos, con validaciones y DI.
- ✅ `fintech/views/user.py` — `UserView` completo: `get`/`post`, excepciones mapeadas a status codes, `asdict` para el body.
- ✅ `fintech/urls.py` + `senior_test/urls.py` — conectados vía `include()`, dos patrones (`user/`, `user/<int:id>/`).
- ✅ `fintech/test/fake_repository.py` — `FakeUserRepository` (completo, con estado real en memoria) + `FakeTransactionRepository` (recién creada, `pass`, vacía).
- ✅ `fintech/test/test_user_controllers.py` — 5 tests, todos pasando.
- ⏳ `fintech/test/test_transaction_controllers.py` — 1 test (`test_create_deposit`), todavía `pass`, sin escribir.
- ⏳ `domain/transaction.py` — **no existe todavía**, es lo próximo a crear.
- ⏳ `User.retirar()`/`User.depositar()` — no implementados, bloqueados por la decisión de mutabilidad pendiente (ver punto 5).
- ⚠️ Hallazgo pendiente de prolijar (no bloqueante, preexistente): `fintech/models/__init__.py` hace `from .transaction import User, Transaction` en vez de `from .user import User`.

## Próximos pasos (para retomar)

1. **Resolver la mutabilidad de `User` pendiente** (pregunta sin contestar, ver punto 5) — bloquea todo lo demás de `retirar()`.
2. Decidir nombre/valores del campo de dirección en `Transaction`.
3. Crear `domain/transaction.py` (entidad `Transaction`, dataclass).
4. Escribir test de dominio puro para `User.retirar()`/`depositar()` (sin repository) — TDD, empezando por el caso feliz y el de fondos insuficientes (`NotEnoughFunds`).
5. Implementar `retirar()`/`depositar()` en `User`.
6. Recién ahí: persistencia del aggregate completo — nuevo método de repository (persistir `User` actualizado + `Transaction` nueva atómicamente, con `django.db.transaction.atomic`), actualizar `Protocol`, `DjangoUserRepository`, y completar `FakeTransactionRepository`/`FakeUserRepository` en los fakes.
7. Migración nueva en Django para el campo de dirección de `Transaction`.
8. `TransactionController` (o extender `UserController`) + vista HTTP para retiro/depósito, con `NotEnoughFunds` mapeada a un status code (sin decidir todavía — probablemente 400 o 422).
9. Más adelante, si se retoma: extender `get_data` para buscar también por `email` vía query param (pospuesto, no descartado).
