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
- Solo se escala a pseudocódigo o un ejemplo mínimo **genérico** (nunca del archivo real) cuando el usuario pide explícitamente que se le explique un concepto nuevo (ej. `Protocol`, `@dataclass`, excepciones custom, `Decimal`, stub vs fake).
- Cuando el usuario pregunta algo conceptual ("¿qué es DI?", "no sé cómo hacer X"), se le explica el concepto con un ejemplo genérico no relacionado a su dominio, y después vuelve a escribir él su versión real.
- Cuando el usuario pide explícitamente una opinión de diseño ("¿qué opinás?", "¿voy bien?"), sí se le da una recomendación directa con el razonamiento — pero la decisión final queda en sus manos.
- Excepción: verificaciones diagnósticas de solo lectura (correr `manage.py shell`/`pytest` para confirmar que algo funciona, `git status`, instalar dependencias que el usuario pidió explícitamente) sí las puede hacer el asistente — no es "hacerle el código", es confirmar que lo que escribió funciona o preparar el entorno que pidió.

## Decisiones de arquitectura tomadas

### 1. Capas: domain / infrastructure / controllers (aplicación)

```
fintech/
  domain/            # Python puro, CERO imports de Django
    user.py           # entidad User (dataclass)
    repository.py      # UserRepository (Protocol/contrato)
    exceptions.py       # UserNotFound
  infrastructure/      # sabe de Django, implementa los contratos del dominio
    user_repository.py  # DjangoUserRepository (implementa UserRepository)
  controllers/          # capa de orquestación/aplicación
    users.py             # UserController — depende de UserRepository vía DI, nunca de Django directo
  models/                # ya existía: los models.Model de Django (filas de la tabla)
  views/                  # ya existía: DRF views — es la capa HTTP, responsable de convertir
                          #   HttpRequest/DRF Request a dict plano antes de pasarlo al controller
  test/                    # tests con pytest (carpeta nueva, distinta del tests.py default de Django)
```

**Por qué esta separación:** Dependency Inversion Principle (la D de SOLID). Los módulos de alto nivel (dominio, orquestación) no dependen de infraestructura (Django); ambos dependen de una abstracción (`Protocol`). La infraestructura implementa esa abstracción, no al revés.

### 2. `User` de dominio es un Active Record → se descartó. Se eligió Opción B (DDD puro)

Se discutieron dos opciones:
- **Opción A (pragmática):** `User(models.Model)` con reglas de negocio como métodos directamente en el modelo Django.
- **Opción B (DDD puro, la elegida):** entidad de dominio en Python plano, desacoplada de Django, con un Repository que mapea entre el dominio y el ORM.

**Por qué B:** el usuario quiere tests unitarios que no toquen la base de datos, y quiere practicar inyección de dependencias explícitamente. B es la que lo permite.

### 3. `UserRepository` es un `typing.Protocol`, no un `abc.ABC`

Se explicó la diferencia (nominal typing vs structural typing / duck typing). Se eligió `Protocol` porque encaja mejor con el objetivo de poder pasar un `FakeUserRepository` en los tests sin necesidad de heredar de nada.

**Contrato final de `UserRepository`** (`domain/repository.py`):
```python
class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User: ...
    def get_by_email(self, email: str) -> User: ...
    def save(self, user: User) -> User: ...
```
- Sin `delete` — decisión consciente (YAGNI). En un dominio financiero probablemente nunca se borra un `User` de verdad (auditoría/regulación); si hace falta inhabilitar, a futuro se agregaría un campo `active` en vez de un delete real. No implementar hasta que haga falta.
- `save` es **upsert único** (reemplaza a tener `create`/`update` separados). Aprovecha que `Model.save()` de Django ya decide INSERT vs UPDATE según si `pk` es `None` o no — mismo patrón se aplicó en el dominio y en `FakeUserRepository`.
- Lectura por `id` **o** `email`: se decidió por **dos métodos explícitos** (`get_by_id`, `get_by_email`) en vez de uno flexible con parámetros opcionales, para evitar ambigüedad y tipar mejor.
- **No encontrado → excepción propia** (`UserNotFound(value: str | int, param: str)`), no `None`.
- **⚠️ Todavía sin resolver:** esto puede no ser ideal para casos donde "no encontrado" es un resultado esperado (ej. chequear si un email ya existe antes de crear un user) — ahí usar excepciones para control de flujo normal es mal visto. **Pendiente para cuando se implemente la validación de email único en `create_user`** — capaz conviene un método aparte tipo `exists_by_email(email) -> bool`.

### 4. Tipos de dinero: `Decimal`, nunca `float`

`float` tiene errores de precisión binaria (`0.1 + 0.2 != 0.3`). Django ya usa `Decimal` internamente para `DecimalField`, así que el dominio sigue el mismo tipo. Si se necesita construir un `Decimal` desde un literal, hacerlo desde string (`Decimal("0.1")`), nunca desde un float (`Decimal(0.1)`), porque hereda la imprecisión.

**⚠️ Deuda técnica pendiente:** `UserController.create_user` (ver más abajo) todavía tiene `balance=0` (int) en vez de `Decimal("0")` — se detectó en la fase de refactor del ciclo TDD pero no se corrigió todavía. Es lo primero para retocar mañana.

### 5. Aggregate identificado: `User` + `Transaction`

El usuario identificó esto solo, sin que se le sugiriera: un retiro/depósito necesita crear una `Transaction` **y** actualizar `balance` del `User` **atómicamente** — si uno pasa sin el otro, el sistema queda en estado inválido. Eso es la definición de un DDD Aggregate.

- **Aggregate Root = `User`** (único punto de entrada).
- **`Transaction`** es miembro del aggregate — tiene identidad propia pero su ciclo de vida está atado al `User` (confirmado por el modelo Django existente: `Transaction.user` es FK, no hay relación entre dos `User`s, o sea no son transferencias entre cuentas, son operaciones sobre una sola cuenta).
- Implicación de diseño (**todavía no implementada**): el `UserController` no debería crear una `Transaction` y actualizar `balance` como dos pasos sueltos. La entidad `User` de dominio debería exponer un método de comportamiento (ej. `user.retirar(monto)`) que garantice ambos cambios juntos.
- Cuidado de nomenclatura: hay dos conceptos llamados "transacción" — la entidad de dominio `Transaction` y la transacción de base de datos (`django.db.transaction.atomic`). No confundir cuando se implemente la persistencia del aggregate completo.
- Pendiente: decidir si `User` (dataclass) queda mutable o inmutable. Se dejó **mutable por ahora**, a revisar cuando se implemente `retirar()`/el aggregate completo.

### 6. `@dataclass` para entidades de dominio

`domain/user.py`:
```python
@dataclass
class User:
    name: str
    email: str
    balance: Decimal
    id: Optional[int] = None
```
Regla de Python recordada: los campos sin valor default van antes que los que sí tienen default — por eso `id` (con default `None`, porque un `User` nuevo aún no tiene id asignado por la DB) va al final.

### 7. `request_data` es un `dict` plano — conversión HTTP la hace la vista

Decisión del usuario, confirmada como correcta: `UserController.create_user(request_data: dict)` recibe un dict simple. La conversión de `HttpRequest`/DRF `Request` a ese dict es responsabilidad de `UserView` (capa HTTP) — el controller nunca debe saber que Django/DRF existen. Mismo principio DIP que el resto del diseño. **Todavía no se actualizó `UserView` para hacer esta conversión y llamar al controller** (sigue con el placeholder viejo).

### 8. `create_user` devuelve el `User` de dominio, no un dict

Se discutió explícitamente (el usuario preguntó "¿qué opinás?"). Decisión: devolver el `User` (dataclass), no un dict armado a mano.

**Por qué:** un dict obliga a acordarse de claves como string (sin autocompletado, sin chequeo de tipos); el `User` tipado es un contrato más fuerte para cualquier caller (view, test, un futuro comando de consola). El problema real que motivaba el dict — "que el view lo pueda convertir a JSON fácil" — ya tiene solución idiomática en DRF: los `Serializer`. Que el controller arme el JSON a mano sería mezclarle una responsabilidad de presentación (viola SRP). Esto además resuelve solo la inconsistencia que había entre `create_user` (usaba `"name"`) y `get_data` (usaba `"username"`) — deja de ser problema del controller.

**Pendiente:** `get_data()` también debería revisarse con este mismo criterio cuando se rediseñe (ver punto 9).

### 9. `UserController` NO guarda el usuario creado como estado de instancia

Se decidió explícitamente que `create_user` no debe guardar `self.user` (o similar) después de crear. Consecuencia: `get_data()` (que antes leía `self.user.name` etc. asumiendo que el constructor recibía un usuario puntual) quedó **sin rediseñar** — hoy es `pass`. Camino más probable cuando se retome: que reciba un `user_id` como parámetro y use `self.user_repo.get_by_id(user_id)`, ya que ese método ya existe y funciona tanto en `DjangoUserRepository` como en `FakeUserRepository`. No se cerró esta decisión todavía, queda para cuando se escriba el test de `get_data`.

## Infraestructura de testing

- Se instaló `pytest` (ya estaba en el venv) + `pytest-django==4.14.0`.
- `pytest.ini` en la raíz, con `DJANGO_SETTINGS_MODULE = senior_test.settings` y `python_files = test/*.py tests.py`.
- `requirements.txt` estaba corrupto (generado con PowerShell en UTF-16, se leía con espacios entre cada carácter) — se regeneró limpio con `pip freeze` desde bash.
- Convención de nombres de pytest que ya causó bugs reales en la sesión — **recordar siempre**: clases de test deben empezar con `Test` (mayúscula), métodos con `test_` (minúscula). Un nombre mal puesto no da error, simplemente "0 tests collected" en silencio.
- Los tests actuales (dominio puro + `FakeUserRepository`) **no necesitan** `django.test.TestCase`, alcanza con clases simples (estilo `pytest`) sin heredar de nada — no tocan la base de datos, así que no hace falta el overhead de setup/teardown de DB que sí trae `django.test.TestCase`.

## Estado actual del código

- ✅ `fintech/domain/user.py` — entidad `User`, completa y correcta.
- ✅ `fintech/domain/repository.py` — `Protocol UserRepository`, completo y correcto.
- ✅ `fintech/domain/exceptions.py` — `UserNotFound(value: str | int, param: str)`, completo y correcto.
- ✅ `fintech/infrastructure/user_repository.py` — `DjangoUserRepository`, completo, revisado, y verificado que importa sin errores contra Django real.
- ✅ `fintech/test/test_controllers.py` — contiene `FakeUserRepository` (fake real con estado en memoria, dos dicts `_by_id`/`_by_email`) y `TestUserController.test_insert_user`, que **pasa** (verificado con `pytest`, 1 passed).
- ⏳ `fintech/controllers/users.py` — `UserController.__init__` recibe `user_repo: UserRepository` vía DI (correcto). `create_user` implementado y con test en verde, pero con la deuda del punto 4 (`balance=0` debería ser `Decimal("0")`), y sin ninguna validación todavía (email duplicado, campos vacíos). `get_data()` es `pass`, sin rediseñar (ver punto 9).
- ⏳ `fintech/views/user.py` — sigue con el placeholder original (`{"message": "Hello, World!"}` / `"User created successfully!"`), no llama todavía a `UserController`.
- ⚠️ Hallazgo pendiente de prolijar (no bloqueante, preexistente): `fintech/models/__init__.py` hace `from .transaction import User, Transaction` — `User` en realidad está definido en `models/user.py`, funciona solo porque `transaction.py` lo re-exporta indirectamente (import transitivo frágil). Corregir en algún momento a `from .user import User` + `from .transaction import Transaction`.

## Próximos pasos (para retomar mañana)

En orden sugerido:
1. Refactor rápido: `balance=0` → `Decimal("0")` en `create_user` (deuda del punto 4).
2. Seguir el ciclo TDD para `create_user` con casos nuevos — el que se dejó pendiente explícitamente es **email duplicado**: escribir el test primero, y ahí sí resolver la pregunta abierta del punto 3 (`exists_by_email` vs `get_by_email` + `except UserNotFound`).
3. Validaciones básicas de `create_user` (¿`name`/`email` vacíos o ausentes?).
4. Rediseñar y testear `get_data()` (ver punto 9 — probablemente con `user_id` como parámetro).
5. Conectar `UserView` con `UserController` de verdad (ver punto 7 — hoy el view sigue con el placeholder).
6. Más adelante: `User.retirar(monto)` / `User.depositar(monto)` en el dominio y la persistencia atómica del aggregate completo (`User` + `Transaction`) vía `DjangoUserRepository` (entra `django.db.transaction.atomic` — ver punto 5).
