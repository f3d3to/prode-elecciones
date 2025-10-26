import json
from pathlib import Path
from typing import Optional, Set, Dict
from prode_backend.settings import BASE_DIR

_cache = {}

def _load_json(name: str):
    if name in _cache:
        return _cache[name]
    path = Path(BASE_DIR) / 'prode' / 'static' / f'{name}.json'
    data = []
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
    _cache[name] = data
    return data

def get_fuerzas() -> Set[str]:
    return set(_load_json('fuerzas'))

def get_provincias() -> Set[str]:
    return set(_load_json('provincias'))

def get_fuerzas_por_provincia() -> Dict[str, Set[str]]:
    """Devuelve un mapa {provincia -> set(fuerzas permitidas)}.

    Si el archivo no existe o está vacío, retorna {} y se usa el conjunto
    global de fuerzas como fallback.
    """
    data = _load_json('fuerzas_por_provincia')
    if not isinstance(data, dict):
        return {}
    out: Dict[str, Set[str]] = {}
    for prov, arr in data.items():
        try:
            out[str(prov)] = set(arr or [])
        except Exception:
            # Ignoramos filas inválidas para no romper validación
            continue
    return out

def validate_national_fuerzas(national: dict, fuerzas: Set[str]) -> Optional[str]:
    for k in national.keys():
        if k not in fuerzas:
            return f'Fuerza "{k}" inválida'
    return None

def validate_provinciales(provinciales: dict, provincias: Set[str], fuerzas: Set[str]) -> Optional[str]:
    for prov, payload in provinciales.items():
        if prov not in provincias:
            return f'Provincia "{prov}" inválida'
        fuerzas_por_prov = get_fuerzas_por_provincia()
        permitidas = fuerzas_por_prov.get(prov) or fuerzas
        porcentajes = payload.get('porcentajes') or payload.get('percentages') or {}
        for k in porcentajes.keys():
            if k not in permitidas:
                return f'Fuerza "{k}" inválida en {prov}'
        winner = payload.get('winner') or payload.get('ganador')
        if winner and winner not in permitidas:
            return f'Ganador "{winner}" inválido en {prov}'
    return None

def validate_top3(top3, fuerzas: Set[str]) -> Optional[str]:
    if top3 is None:
        return None
    if not isinstance(top3, list):
        return 'Top-3 debe ser una lista'
    if len(top3) > 3:
        return 'Top-3 debe tener hasta 3 fuerzas'
    seen = set()
    for f in top3:
        if f in seen:
            return 'Top-3 no debe repetir fuerzas'
        seen.add(f)
        if f not in fuerzas:
            return f'Fuerza "{f}" inválida en Top-3'
    return None

def validate_bonus(bonus: dict, provincias: Set[str]) -> Optional[str]:
    if not bonus:
        return None
    # All bonus fields in this MVP are province names when provided
    keys = [
        'mas_renida',
        'cambia_ganador',
        'fit_mayor',
        'lla_mas_crece',
        'fuerza_patria_mayor',
    ]
    for k in keys:
        val = bonus.get(k)
        if val is None or val == '':
            continue
        if val not in provincias:
            return f'Provincia "{val}" inválida en bonus ({k})'
    return None
