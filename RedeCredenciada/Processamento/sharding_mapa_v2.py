import json
import os
import random
import string
import shutil
from collections import defaultdict

# ==========================================
# FUNÇÃO PRINCIPAL (Tudo incluído)
# ==========================================

def shard_json_data(input_data, mode, output_base_dir="output_shards", web_path_prefix="./"):
    """
    input_data: O dicionário gigante.
    mode: 
      1 = Por Estado (Ordenado por cidade)
      2 = Por Cidade (Ordenado por nome)
      3 = Por Especialidade
    output_base_dir: Pasta raiz da saída
    web_path_prefix: Prefixo para o caminho no JSON de mapa (ex: './data/')
    """

    # ------------------------------------------
    # 1. FUNÇÕES AUXILIARES (NESTED)
    # ------------------------------------------
    
    def generate_random_code(length=10):
        """Gera um código alfanumérico aleatório para evitar enumeration."""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def clean_filename(text):
        """Remove caracteres inválidos para nomes de arquivos/pastas."""
        return "".join(c for c in text if c.isalnum() or c in (' ', '-', '_')).strip()

    def parse_location(location_str):
        """
        Separa 'Cidade - UF' em ('Cidade', 'UF').
        Ex: 'Rio Branco - AC' -> ('Rio Branco', 'AC')
        """
        if not location_str or '-' not in location_str:
            return ("Desconhecido", "ND")
        
        parts = location_str.split('-')
        state = parts[-1].strip()
        # Junta o resto caso a cidade tenha hífen (Ex: Xique-Xique - BA)
        city = '-'.join(parts[:-1]).strip()
        return city, state

    def extract_specialties(provider_data):
        """
        Extrai lista de especialidades baseada na lógica:
        - Se tem ODONTOLOGIA, usa ela.
        - Se não, usa Especialidade(s).
        """
        specialties = []
        
        # 1. Checa se é Odonto
        if "ODONTOLOGIA" in provider_data and provider_data["ODONTOLOGIA"]:
            raw_specs = provider_data["ODONTOLOGIA"]
        # 2. Se não, pega médica
        elif "Especialidade(s)" in provider_data:
            raw_specs = provider_data["Especialidade(s)"]
        else:
            raw_specs = "Geral"

        # Limpa e separa por vírgula
        if raw_specs:
            specialties = [s.strip() for s in raw_specs.split(',') if s.strip()]
        
        if not specialties:
            specialties = ["Geral"]
            
        return specialties

    # ------------------------------------------
    # 2. LÓGICA DE SHARDING
    # ------------------------------------------
    
    # Limpa diretório anterior para teste limpo
    if os.path.exists(output_base_dir):
        shutil.rmtree(output_base_dir)
    os.makedirs(output_base_dir)

    print(f"Iniciando Sharding - Modo {mode}...")

    # Estruturas temporárias para agrupamento
    # Modo 1: buffer[UF] = [lista de providers]
    # Modo 2: buffer[UF][Cidade] = [lista de providers]
    # Modo 3: buffer[UF][Cidade][Especialidade] = [lista de providers]
    
    buffer = defaultdict(lambda: defaultdict(lambda: defaultdict(list))) # Estrutura genérica profunda

    # --- FASE 1: PROCESSAMENTO E AGRUPAMENTO ---
    for provider_id, details in input_data.items():
        city, state = parse_location(details.get("Cidade/Estado", ""))
        
        # Injeta o ID original dentro do objeto para não perder a referência
        details_with_id = details.copy()
        details_with_id["_id_original"] = provider_id 

        if mode == 1:
            # Agrupa apenas por Estado
            # Usamos uma chave dummy para cidade/especialidade para manter compatibilidade
            buffer[state]["all"]["all"].append(details_with_id)
            
        elif mode == 2:
            # Agrupa por Estado e Cidade
            buffer[state][city]["all"].append(details_with_id)
            
        elif mode == 3:
            # Agrupa por Estado, Cidade e Especialidade
            specs = extract_specialties(details)
            for spec in specs:
                # Normaliza nome da especialidade para nome de pasta/arquivo
                spec_clean = clean_filename(spec)
                buffer[state][city][spec_clean].append(details_with_id)

    # --- FASE 2: ORDENAÇÃO E ESCRITA ---
    
    for state, cities_data in buffer.items():
        state_clean = clean_filename(state)
        
        # Modo 1: Pasta é o Estado
        if mode == 1:
            # Pega a lista "all" que criamos
            providers = cities_data["all"]["all"]
            
            # ORDENAÇÃO MODO 1: Por nome da cidade
            providers.sort(key=lambda x: parse_location(x.get("Cidade/Estado", ""))[0])
            
            # Cria Caminho: Output/Estado
            dir_path = os.path.join(output_base_dir, state_clean)
            os.makedirs(dir_path, exist_ok=True)
            
            # Nome do arquivo: Estado_{Random}.json
            file_name = f"{state_clean}_{generate_random_code()}.json"
            full_path = os.path.join(dir_path, file_name)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(providers, f, indent=2, ensure_ascii=False)
                
        else:
            # Modos 2 e 3 iteram sobre cidades
            for city, specs_data in cities_data.items():
                city_clean = clean_filename(city)
                
                if mode == 2:
                    providers = specs_data["all"]
                    # ORDENAÇÃO MODO 2: Alfabética (Nome do Prestador)
                    providers.sort(key=lambda x: x.get("Nome", ""))
                    
                    # Cria Caminho: Output/Estado/Cidade
                    dir_path = os.path.join(output_base_dir, state_clean, city_clean)
                    os.makedirs(dir_path, exist_ok=True)
                    
                    # Nome: Estado-Cidade_{Random}.json
                    file_name = f"{state_clean}-{city_clean}_{generate_random_code()}.json"
                    full_path = os.path.join(dir_path, file_name)
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        json.dump(providers, f, indent=2, ensure_ascii=False)
                        
                elif mode == 3:
                    # Modo 3 itera sobre especialidades
                    for spec, providers in specs_data.items():
                        # ORDENAÇÃO MODO 3: Alfabética (Nome do Prestador)
                        providers.sort(key=lambda x: x.get("Nome", ""))
                        
                        # Cria Caminho: Output/Estado/Cidade/Especialidade
                        # Nota: A especificação dizia "estado/cidade/especialidade" como hierarquia
                        dir_path = os.path.join(output_base_dir, state_clean, city_clean, spec)
                        os.makedirs(dir_path, exist_ok=True)
                        
                        # Nome: Estado-Cidade-Especialidade_{Random}.json
                        file_name = f"{state_clean}-{city_clean}-{spec}_{generate_random_code()}.json"
                        full_path = os.path.join(dir_path, file_name)
                        
                        with open(full_path, 'w', encoding='utf-8') as f:
                            json.dump(providers, f, indent=2, ensure_ascii=False)

    print(f"Sucesso! Arquivos gerados em '{output_base_dir}'")

    # ------------------------------------------
    # 3. FASE DE MAPEAMENTO (NESTED)
    # ------------------------------------------
    
    def _create_map_internal():
        """
        Função aninhada que varre o diretório recém-criado e gera o mapa.json.
        Usa os arquivos reais do disco para garantir precisão com os códigos random.
        """
        print("Iniciando geração do mapa de arquivos (Nested)...")
        file_map = {}
        
        for root, dirs, files in os.walk(output_base_dir):
            for file in files:
                if not file.endswith(".json") or file == "mapa_arquivos.json":
                    continue

                # Caminho relativo para lógica da estrutura
                rel_path = os.path.relpath(root, output_base_dir)
                if rel_path == ".": path_parts = []
                else: path_parts = rel_path.split(os.sep)

                # Caminho Web Final
                web_rel_path = os.path.join(output_base_dir, rel_path, file).replace("\\", "/")
                final_web_url = f"{web_path_prefix}{web_rel_path}"
                
                # Preenche o mapa baseado na profundidade da pasta
                if len(path_parts) == 1: # Modo 1: Estado
                    state = path_parts[0]
                    file_map[state] = final_web_url
                elif len(path_parts) == 2: # Modo 2: Estado/Cidade
                    state, city = path_parts
                    if state not in file_map: file_map[state] = {}
                    file_map[state][city] = final_web_url
                elif len(path_parts) == 3: # Modo 3: Estado/Cidade/Espec
                    state, city, spec = path_parts
                    if state not in file_map: file_map[state] = {}
                    if city not in file_map[state]: file_map[state][city] = {}
                    file_map[state][city][spec] = final_web_url

        # Salva o mapa na raiz do output
        map_path = os.path.join(output_base_dir, "mapa_arquivos.json")
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump(file_map, f, indent=2, ensure_ascii=False)
        
        print(f"Mapa gerado com sucesso: {map_path}")

    # Chama a função nested imediatamente após gerar os arquivos
    _create_map_internal()