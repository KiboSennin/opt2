import random
from read import read_instance
from scipy.sparse import dok_matrix
ENE = 5

# Done?
def complete_solution(solution, data):
    """
    Verifica si todas las demandas han sido satisfechas.
    """
    total_assigned = {client: 0 for client in range(data["params"][1])}
    for (facility, client), proportion in solution.items():
        total_assigned[client] += proportion

    demandas_pendientes = {
        client: data["initial_demand"][client] - total_assigned[client]
        for client in range(data["params"][1])
    }

    print(f"Demandas pendientes: {list(demandas_pendientes.items())[:10]} (mostrando las primeras 10)")
    return all(
        total_assigned[client] >= data["initial_demand"][client]
        for client in range(data["params"][1])
    )



# Done?
def all_candidates(data, solution):
    candidates = []

    for facility in range(data["params"][0]):
        if facility >= len(data["capacity"]):
            print(f"Índice de facilidad fuera de rango: {facility}")
            continue

        if data["capacity"][facility] > 0:  # Considerar facilidades con capacidad restante
            for client in range(data["params"][1]):
                if data["demandas"][client] > 0:  # Considerar clientes con demanda pendiente
                    current_demand_satisfied = solution[:, client].sum()
                    remaining_capacity = data["capacity"][facility] - current_demand_satisfied
                    if remaining_capacity > 0:
                        candidates.append((facility, client))

    print(f"Candidatos disponibles: {candidates}")
    return candidates

# Falta expandir
def construct_candidates(data, solution):
    """
    Construye una lista de candidatos factibles para agregar a la solución.
    """
    all_can = all_candidates(data, solution)
    if not all_can:
        print("Advertencia: No se generaron candidatos válidos en esta iteración.")
    else:
        print(f"Candidatos generados: {all_can[:10]} (mostrando los primeros 10)")
    return all_can


# DONE?
def select_candidate(candidate_list, seed):
    """
    Selecciona un candidato aleatorio de la lista.
    """
    random.seed(seed)
    if not candidate_list:
        print("Error: Lista de candidatos vacía. No se puede seleccionar.")
        return None
    candidate = random.choice(candidate_list)
    print(f"Candidato seleccionado: {candidate}")
    return candidate



def add_candidate(solution, candidate, data):
    """
    Asigna una parte de la demanda de un cliente a una facilidad.
    """
    facility, client = candidate
    demand = data["demandas"][client]
    capacity = data["capacity"][facility]

    # Asignar lo máximo posible
    total_assigned_demand = min(demand, capacity)

    if total_assigned_demand > 0:
        solution[facility, client] += total_assigned_demand
        data["demandas"][client] -= total_assigned_demand
        data["capacity"][facility] -= total_assigned_demand
        print(f"Asignación realizada: {candidate}, demanda satisfecha: {total_assigned_demand}")
    else:
        print(f"Advertencia: No se pudo asignar {candidate}. Capacidad restante: {capacity}, demanda: {demand}")
    return solution


def evaluate_cost(solution, data):
    """
    Calcula el costo total de la solución.

    Args:
        solution (dok_matrix): Solución actual.
        data (dict): Datos de la instancia.

    Returns:
        float: Costo total o None si la solución es inválida.
    """
    if solution.nnz == 0:  # Verifica si la solución está vacía
        print("La solución está vacía, no se puede calcular el costo.")
        return None

    total_cost = 0
    facilities_used = set(i for i, _ in solution.keys() if solution[i, _] > 0)

    # Costo fijo por abrir instalaciones
    total_cost += sum(data["costos_fijos"][facility] for facility in facilities_used)

    # Costo de transporte
    for (facility, client), proportion in solution.items():
        if proportion > 0:  # Solo considera asignaciones no nulas
            total_cost += proportion * data["costo"][client][facility]

    return total_cost


def greedy_randomized_construction(seed, data):
    """
    Construye una solución inicial utilizando un enfoque aleatorio greedy.

    Args:
        seed (int): Semilla para generar números aleatorios.
        data (dict): Datos de la instancia.

    Returns:
        tuple: Solución generada y su costo.
    """
    random.seed(seed)
    instance_dim = data["params"]
    solution = dok_matrix((instance_dim[0], instance_dim[1]), dtype=float)

    print("Estado inicial:")
    print(f"Capacidades: {data['capacity']}")
    print(f"Demandas: {data['demandas']}")

    while not complete_solution(solution, data):
        candidates = construct_candidates(data, solution)
        if not candidates:
            print("No hay más candidatos disponibles.")
            break

        print(f"Candidatos disponibles: {candidates}")

        selection = select_candidate(candidates, seed)
        if not selection:
            print("No se pudo seleccionar un candidato.")
            break

        solution = add_candidate(solution, selection, data)
        print(f"Asignación actual: {solution.items()}")

    cost = evaluate_cost(solution, data)
    print(f"Solución construida con costo: {cost}")
    return solution, cost



def SAS(solution, data):
    """
    Reassigns a portion of a client's demand from one facility to another to reduce cost
    or improve resource utilization while respecting capacity and demand constraints.

    Args:
        solution (dok_matrix): Current solution matrix (centers x clients), where values represent 
                               the amount of demand satisfied by each facility.
        data (dict): Instance data, including capacities, demands, costs, etc.

    Returns:
        dok_matrix: Updated solution matrix after performing a single assignment swap.
    """
    best_solution = solution.copy()  # Copy current solution as the baseline
    best_cost = evaluate_cost(best_solution, data)  # Initial cost of the current solution
    improved = False 
    # Iterate over all assignments in the solution
    for (current_facility, client), assigned_demand in solution.items():
        if assigned_demand <= 0:  # Skip if no demand is currently assigned
            continue

        # Iterate over all alternative facilities (to swap with)
        for alternative_facility in range(data["params"][0]):
            if alternative_facility == current_facility:
                continue  # Skip the current facility

            # Calculate the potential new demand for both facilities
            # Tentatively swap the entire demand between the current and alternative facility
            tentative_solution = best_solution.copy()
            tentative_solution[current_facility, client] -= assigned_demand
            tentative_solution[alternative_facility, client] += assigned_demand

            # Check if this reassignment respects the capacity constraints
            # Ensure that no facility exceeds its original capacity after reassignment
            facility_demand_current = tentative_solution[current_facility, :].sum()  # Total demand in the current facility
            facility_demand_alternative = tentative_solution[alternative_facility, :].sum()  # Total demand in the alternative facility

            if facility_demand_current <= data["initial_capacity"][current_facility] and facility_demand_alternative <= data["initial_capacity"][alternative_facility]:
                # If the solution is feasible, evaluate the cost
                tentative_cost = evaluate_cost(tentative_solution, data)

                # If this reassignment reduces the cost, update the best solution
                if tentative_cost < best_cost:
                    best_solution = tentative_solution
                    best_cost = tentative_cost
                    improved = True

    return best_solution, improved
def facility_opening_closing(solution, data):
    """
    Intenta abrir o cerrar instalaciones para mejorar la solución actual.
    
    Args:
        solution (dok_matrix): Solución actual.
        data (dict): Datos de la instancia.

    Returns:
        tuple: (Nueva solución, bool indicando si hubo mejora).
    """
    improved = False
    best_solution = solution.copy()
    best_cost = evaluate_cost(best_solution, data)

    # Intentar cerrar instalaciones
    for facility in range(data["params"][0]):
        if solution[facility, :].sum() == 0:  # Si no tiene asignaciones, ya está cerrada
            continue
        
        tentative_solution = best_solution.copy()
        tentative_solution[facility, :] = 0  # Eliminar todas las asignaciones de esta instalación

        # Reasignar demanda de los clientes
        feasible = True
        for client in range(data["params"][1]):
            remaining_demand = data["initial_demand"][client] - tentative_solution[:, client].sum()
            if remaining_demand > 0:
                # Buscar la instalación más barata para satisfacer esta demanda
                best_facility = None
                min_cost = float('inf')
                for alt_facility in range(data["params"][0]):
                    if alt_facility != facility and data["capacity"][alt_facility] > 0:
                        cost = data["costo"][client][alt_facility]
                        if cost < min_cost:
                            min_cost = cost
                            best_facility = alt_facility
                
                if best_facility is not None:
                    assignable = min(remaining_demand, data["capacity"][best_facility])
                    tentative_solution[best_facility, client] += assignable
                    data["capacity"][best_facility] -= assignable
                else:
                    feasible = False
                    break

        # Evaluar costo
        if feasible:
            tentative_cost = evaluate_cost(tentative_solution, data)
            if tentative_cost < best_cost:
                best_solution = tentative_solution
                best_cost = tentative_cost
                improved = True

    # Intentar abrir instalaciones
    for facility in range(data["params"][0]):
        if solution[facility, :].sum() > 0:  # Si ya está abierta
            continue
        
        tentative_solution = best_solution.copy()

        for client in range(data["params"][1]):
            remaining_demand = data["initial_demand"][client] - tentative_solution[:, client].sum()
            if remaining_demand > 0:
                cost = data["costo"][client][facility]
                assignable = min(remaining_demand, data["capacity"][facility])
                tentative_solution[facility, client] += assignable
                data["capacity"][facility] -= assignable

        # Evaluar costo
        tentative_cost = evaluate_cost(tentative_solution, data)
        if tentative_cost < best_cost:
            best_solution = tentative_solution
            best_cost = tentative_cost
            improved = True

    return best_solution, improved


def find_improvement(solution, data, iter, N):
    improved = False
    
    
    # Dado un número de SAS, hacer FOC
    if iter % N == 0:               
        new, improved =  facility_opening_closing(solution, data)
    new, improved = SAS(solution, data)
    
    if improved:    return new, improved
    else:           return solution, improved

#Done?
def Local_Search(solution, data):
    """
    Mejora la solución iterativamente

    Args:
        solution (dok_matrix): Solución inicial
        data (dict): Datos de la instancia

    Returns:
        dok_matrix: Solución mejorada, en caso de que se hayan logrado mejoras
    """
    improved = True
    i = 1
    while improved:
        new_solution, improved = find_improvement(solution, data, i, N = ENE)
        print("i : ", i)
        if improved:
            solution = new_solution
        else:
            improved = False
            
        i += 1
    return solution, evaluate_cost(solution, data)

#Done?
def Update_Solution(current, best):
    """
    Actualiza la mejor solución encontrada hasta el momento-

    Args:
        current (tuple): Solución actual (solution, cost)
        best (tuple): Mejor solución hasta el momento (solution, cost)

    Returns:
        tuple: Mejor solución entre ambas
    """
    
    print(current)
    print(best)
    if best is None or current[1] < best[1]:
        return current
    return best

from copy import deepcopy

def GRASP(iterations, seed, instance_name):
    """
    Algoritmo GRASP para resolver el problema.
    """
    data = read_instance(instance_name)  # Leer datos de entrada
    best_solution = None

    for i in range(iterations):  # Control del número de iteraciones
        print(f"Iteración {i+1} de {iterations}")
        dat = deepcopy(data)  # Copia de los datos para la iteración
        solution, cost = greedy_randomized_construction(seed, dat)

        if cost is None or solution.nnz == 0:  # Validar solución inicial
            print("Solución inicial inválida. Continuando con la siguiente iteración...")
            continue

        print(f"Solución generada con costo: {cost}")

        solution, cost = Local_Search(solution.copy(), dat)  # Búsqueda local
        best_solution = Update_Solution((solution, cost), best_solution)  # Actualizar mejor solución

        print("-" * 100)

    # Retornar la mejor solución encontrada
    if best_solution is None:
        print("No se encontró una solución válida en ninguna iteración.")
        return dok_matrix((data["params"][0], data["params"][1]), dtype=float), float('inf')

    return best_solution

    