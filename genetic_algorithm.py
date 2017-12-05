import json
from pyeasyga import pyeasyga
import random
from random import randint
from itertools import accumulate
import requests as re

with open('39.txt') as f:
    knapsack = [(int(l[0]), int(l[1])) for l in [next(f).strip().split(' ')]]
    items = [(int(item[0]), float(item[1]), int(item[2])) for line in f for item in [line.strip().split(' ')]]

# ------------------ Использование библиотеки pyeasyga ------------------
ga = pyeasyga.GeneticAlgorithm(items)
ga.population_size = 200

# Фитнес-функция, которую используют обе реализации
def fitness_function(individual, data):
    weight, volume, price = 0, 0, 0
    for (selected, item) in zip(individual, data):
        if selected:
            weight += item[0]
            volume += item[1]
            price += item[2]
    if weight > knapsack[0][0] or volume > knapsack[0][1]:
        price = 0
    return price

ga.fitness_function = fitness_function
ga.run()

# ------------------ Собственная реализация ------------------

# Генерация начальной популяции (жадный выбор, начиная со случайного груза)
def generate_initial_population(items):
    initial_population = []
    sorted_items = sorted([(ind, val)for ind, val in enumerate(items)], key=lambda tup: tup[1][2], reverse=True)
    for size in range(200):
        individual = [0 for _ in range(len(items))]
        rand = randint(0, len(items) - 1)
        for i in range(0, len(items) - 1):
            modified = individual.copy()
            modified[sorted_items[(rand + i) % 30][0]] = 1
            if fitness_function(modified, items) == 0:
                break
            else:
                individual = modified
        initial_population.append(individual)
    return initial_population

# Отбор особей для скрешивания (рулетка)
def roulette_wheel(population, items):
    parents = []
    sorted_population = sorted([[ind, fitness_function(val, items), val] for ind, val in enumerate(population)], key=lambda x: x[1], reverse=True)
    for pairs in range(int(len(population) / 2)):
        pair = []
        for p in range(2):
            wheel = list(accumulate([sorted_population[ind][1] for ind in range(len(sorted_population))]))
            ball = randint(1, sum(sorted_population[ind][1] for ind in range(len(sorted_population))))
            for i in range(len(wheel)):
                if ball <= wheel[i] and ball > wheel[i] - sorted_population[i][1]:
                    pair.append(sorted_population[i][2])
                    del sorted_population[i]
                    break
        parents.append(pair)
    return parents

# Однородное скрещивание двух особей
def crossover(parents, items):
    children = []
    while len(children) != 2:
        child = [parents[randint(0, 1)][_] for _ in range(len(items))]
        if fitness_function(child, items) != 0:
            children.append([parents[randint(0, 1)][_] for _ in range(len(items))])
    return children

# Скрещивание всех отобранных пар особей
def crossover_population(parents, items):
    children = []
    for p in range(len(parents)):
        children.extend(crossover(parents[p], items))
    return children

# Мутация (добавление 1 случайной вещи 10% особей)
def mutation(population, items):
    count = len(population) / 10
    rand_sequence = random.sample(range(len(population)), len(population))
    for rand in rand_sequence:
        missing_items = [ind for ind, val in enumerate(population[rand]) if val == 0]
        lst = random.sample(range(0, len(missing_items)), len(missing_items))
        for i in lst:
            population[rand][i] = 1
            if (fitness_function(population[rand], items), items) == 0:
                population[rand][i] = 0
            else:
                count = count - 1
                break
        if count == 0: break
    return population

# Формирование новой популяции (замена не более 30% худших особей на потомков)
def new_population(parents, children, items):
    old = sorted([[ind, fitness_function(val, items), val] for ind, val in enumerate(parents)], key=lambda x: x[1], reverse=True)
    new = sorted([[ind, fitness_function(val, items), val] for ind, val in enumerate(children)], key=lambda x: x[1], reverse=True)
    for i in range(int((len(old)*30/100))):
        if (old[len(old) - 1 - i][1]) < new[i][1]:
            old[len(old) - 1 - i] = new.pop(i)
        else:
            break
    return [old[_][2] for _ in range(len(old))]

# Запуск работы алгоритма (до 100 поколений)
def ga_run(items):
    population = generate_initial_population(items)
    for generations in range(100):
        pairs = roulette_wheel(population, items)
        children = mutation(crossover_population(pairs, items), items)
        population = new_population(population, children, items)
    res = sorted([val for val in population], key=lambda x: x[1], reverse=True)
    return res[0]

best_individual = ga_run(items)

# POST-запрос
url = 'https://cit-home1.herokuapp.com/api/ga_homework'
headers = {'Content-Type': 'application/json'}
res = {}
res['1'] = {}
res['2'] = {}
res['1']['value'] = sum(val*items[ind][2] for ind, val in enumerate(ga.best_individual()[1]))
res['1']['weight'] = sum(val*items[ind][0] for ind, val in enumerate(ga.best_individual()[1]))
res['1']['volume'] = int(sum(val*items[ind][1] for ind, val in enumerate(ga.best_individual()[1])))
res['1']['items'] = [ind + 1 for ind, val in enumerate(ga.best_individual()[1]) if val != 0]
res['2']['value'] = sum(val*items[ind][2] for ind, val in enumerate(best_individual))
res['2']['weight'] = sum(val*items[ind][0] for ind, val in enumerate(best_individual))
res['2']['volume'] = int(sum(val*items[ind][1] for ind, val in enumerate(best_individual)))
res['2']['items'] = [ind + 1 for ind, val in enumerate(best_individual) if val != 0]
print(json.dumps(res, indent=4))
#r = re.post(url, data=json.dumps(res), headers=headers)
#print(r)