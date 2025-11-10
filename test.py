numbers = []
numbers_set = set()

with open("tests/trace.in", "r") as fd:
    lista = fd.readlines()
    lista = [int(i) for i in lista]
    for x in lista:
        numbers.append(x)
        numbers_set.add(x)

print(len(numbers), len(numbers_set))
