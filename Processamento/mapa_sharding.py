import os
import json

def generate_sharding_map(output_base_dir, output_map_file="mapa_arquivos.json", web_path_prefix=""):
    """
    Escaneia o diretório gerado e cria um JSON (manifesto) mapeando a estrutura.
    
    Args:
        output_base_dir (str): A pasta onde os arquivos foram gerados (ex: "output_shards").
        output_map_file (str): Nome do arquivo JSON final com o mapa.
        web_path_prefix (str): Prefixo para o caminho no HTML (ex: "./data/" ou "/assets/").
    """
    
    if not os.path.exists(output_base_dir):
        print(f"Erro: O diretório '{output_base_dir}' não existe.")
        return

    print(f"Gerando mapa a partir de: {output_base_dir} ...")
    
    # Dicionário que armazenará o mapa
    file_map = {}
    
    # Percorre todas as pastas e arquivos
    for root, dirs, files in os.walk(output_base_dir):
        for file in files:
            if not file.endswith(".json"):
                continue

            # Caminho completo do arquivo no disco
            full_path = os.path.join(root, file)
            
            # Caminho relativo para usar na estrutura lógica (ex: SP/Santos)
            # Isso remove o "output_base_dir" do início do caminho
            rel_path = os.path.relpath(root, output_base_dir)
            
            # Divide o caminho em partes para saber Estado, Cidade, etc.
            # Se rel_path for '.', significa que o arquivo está na raiz (não esperado no seu caso),
            # mas vamos tratar pastas normais.
            if rel_path == ".":
                path_parts = []
            else:
                path_parts = rel_path.split(os.sep)

            # Prepara o caminho web (troca \ por / para funcionar em URLs)
            # Adiciona o nome do arquivo ao final
            web_rel_path = os.path.join(output_base_dir, rel_path, file).replace("\\", "/")
            final_web_url = f"{web_path_prefix}{web_rel_path}"
            
            # --- Lógica de Construção do Mapa Baseada na Profundidade ---
            
            # Nível 1: Apenas Estado (Modo 1) -> output/AC/arquivo.json
            if len(path_parts) == 1:
                state = path_parts[0]
                # Estrutura: { "AC": "caminho..." }
                file_map[state] = final_web_url

            # Nível 2: Estado -> Cidade (Modo 2) -> output/AC/Rio Branco/arquivo.json
            elif len(path_parts) == 2:
                state, city = path_parts
                if state not in file_map:
                    file_map[state] = {}
                # Estrutura: { "AC": { "Rio Branco": "caminho..." } }
                file_map[state][city] = final_web_url

            # Nível 3: Estado -> Cidade -> Especialidade (Modo 3)
            elif len(path_parts) == 3:
                state, city, spec = path_parts
                if state not in file_map:
                    file_map[state] = {}
                if city not in file_map[state]:
                    file_map[state][city] = {}
                # Estrutura: { "AC": { "Rio Branco": { "Cardio": "caminho..." } } }
                file_map[state][city][spec] = final_web_url

    # Salva o mapa em um arquivo JSON
    with open(output_map_file, 'w', encoding='utf-8') as f:
        json.dump(file_map, f, indent=2, ensure_ascii=False)

    print(f"Sucesso! Mapa salvo em '{output_map_file}'.")
    print("Exemplo de estrutura gerada:")
    # Mostra uma prévia pequena do JSON gerado
    print(json.dumps(dict(list(file_map.items())[:2]), indent=2, ensure_ascii=False))

# ==========================================
# EXEMPLO DE USO
# ==========================================
if __name__ == "__main__":
    # Supondo que sua função anterior salvou em "output_shards"
    # O web_path_prefix é útil se seus arquivos estiverem dentro de uma pasta 'data' no servidor
    
    generate_sharding_map(
        output_base_dir="Rede Credenciada\saude_caixa_sharded\saude_caixa_sharded", 
        output_map_file="mapa_para_site.json",
        web_path_prefix="./" 
    ) 