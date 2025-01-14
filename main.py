from vrp import *
from itertools import combinations
import io_solomon
import pickle
from functional_bcd import *


def create_toy_instance():
    # V = [0, 1, 2, 3, 4, 5]
    # E = [(s, t) for s in V for t in V if s != t]
    # J = [0, 1, 2]
    # c = [1] * len(V)
    # C = 10
    # d = {(s, t): abs(s - t) for s, t in E}
    # a = np.random.randint(0, 50, len(V))
    # b = a + 4
    # T = {k: v / 2 for k, v in d.items()}
    # vrp = VRP(V, E, J, c, C, d, a, b, T)
    import json

    capitals_json = json.load(open('capitals.json'))
    capitals = []
    coordinates = {}
    for state in capitals_json:
        if state not in ['AK', 'HI']:
            capital = capitals_json[state]['capital']
            capitals.append(capital)
            coordinates[capital] = (float(capitals_json[state]['lat']), float(capitals_json[state]['long']))
    capital_map = {c: i for i, c in enumerate(capitals)}
    coordinates = {capital_map[c]: coordinates[c] for c in capitals}
    capitals = range(len(capitals))

    def distance(city1, city2):
        c1 = coordinates[city1]
        c2 = coordinates[city2]
        diff = (c1[0] - c2[0], c1[1] - c2[1])
        return math.sqrt(diff[0] * diff[0] + diff[1] * diff[1])

    dist = {(c1, c2): distance(c1, c2) for c1 in capitals for c2 in capitals if c1 != c2}

    V = capitals
    E = [(c1, c2) for c1 in capitals for c2 in capitals if c1 != c2]
    J = [0, 1, 2]
    c = [1] * len(V)
    C = 18
    d = dist
    l = np.random.randint(0, 50, len(V))
    u = l + 4
    T = {k: v / 2 for k, v in d.items()}
    vrp = VRP(V, E, J, c, C, d, l, u, T)
    return vrp


def read_solomon(fp="dataset/data/SolomonDataset_v2/r101-25", n_vehicles=10):
    # pkl_fp = fp + "/data.pkl"
    pkl_fp = fp + "/data_{}.pkl".format(n_vehicles)
    try:
        with open(pkl_fp, "rb") as f:
            V, E, J, c, C, d, l, u, T, coordinates = pickle.load(f)
    except FileNotFoundError:
        V, E, J, c, C, d, l, u, T, coordinates = io_solomon.data_loader(fp, n_vehicles=n_vehicles)
        with open(fp + "/data_{}.pkl".format(n_vehicles), "wb") as f:
            pickle.dump((V, E, J, c, C, d, l, u, T, coordinates), f)

    vrp = VRP(V, E, J, c, C, d, l, u, T, coordinates)
    return vrp


if __name__ == "__main__":
    params_bcd = BCDParams()
    # create vrp instance
    # vrp = create_toy_instance()
    vrp = read_solomon(fp=params_bcd.fp, n_vehicles=params_bcd.n_vehicles)
    vrp.create_model()
    vrp.init(get_block_data=True)

    # clone model for heur
    vrp_clone = read_solomon(fp=params_bcd.fp, n_vehicles=params_bcd.n_vehicles)
    vrp_clone.create_model()
    vrp_clone.init(get_block_data=True)

    print(len(vrp.block_data))
    print(len(vrp.block_data["A"]))
    vrp.m.write("vrp.lp")
    vrp.m.Params.SolutionLimit = 1000000
    vrp.m.Params.MIPGap = 1e-5
    vrp.m.Params.TimeLimit = params_bcd.time_limit
    # vrp.m.Params.Heuristics = 0
    vrp.solve()
    vrp.visualize(x=None)
    # vrp.m.write("vrp.sol")
    # print(vrp.m.objVal)

    # create routing solver
    route = Route(vrp)

    xk = optimize(bcdpar=params_bcd, vrps=(vrp, vrp_clone), route=route)
    # vrp.visualize(x=xk)

    print("*"*50)
    vrp.visualize(x=None)
    vrp.visualize(x=xk)
    print("*"*50)
