# Tienda Minimal - Demo

Instrucciones rápidas para correr el proyecto localmente:

1. Crear y activar un entorno virtual, instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Aplicar migraciones y ejecutar el servidor:

```powershell
python manage.py migrate
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/` en el navegador.
