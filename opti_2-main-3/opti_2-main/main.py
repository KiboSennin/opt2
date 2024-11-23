
from read import read_options, read_instance
from utility import display, get_iter
from GRASP import GRASP
from os.path import join 

# Directorio donde se almacenan las instancias 
instances_path = r'opti_2-main\intances_abc(2)\intances_abc_dat'

# Semilla para generación de soluciones aleatorias (reproducibilidad)
seed = None

def main():
    
    # Leer instancias disponibles desde el directorio especificado
    instances = read_options(instances_path)
    
    # Mostrar opciones y extraer selección (nombre de la instancia)
    name, _ = display(instances)
    
    # Extraer máximo de iteraciones (input)
    max_iterations =  get_iter()
    
    # Generar string del path de la instancia
    file_path = join(instances_path, name + '.txt')
    
    # Resolver instancia seleccionada
    solution, cost = GRASP(max_iterations, seed, file_path)
    
    unique_columns = {j for _, j in solution.keys()}
    
    print(unique_columns)

    if cost == float('inf'):
        print("El GRASP no generó una solución válida.")
        return

    print(f"Solución encontrada por GRASP con costo: {cost}")
    
if __name__ == "__main__":
    main()