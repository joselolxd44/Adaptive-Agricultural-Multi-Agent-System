import random
import csv
from dataclasses import dataclass, field
from typing import List


@dataclass
class Attribute:
    attributeID: int
    description: str
    minValue: float = 0
    maxValue: float = 0
    value: float = 0


@dataclass
class Variety:
    varietyID: int
    name: str
    minHeightZone: float
    maxHeightZone: float
    attributes: List[Attribute] = field(default_factory=list)
    aggressiveness: float = 0
    baseRange: float = 0
    maxChildren: int = 1
    kcal_base: float = 0
    food_base_amount: int = 0


@dataclass
class HeightVarietyMetrics:
    varieties: List[Variety] = field(default_factory=list)


@dataclass
class Seed:
    originalHeight: float = 0
    attributesShot: List[Attribute] = field(default_factory=list)

    newHeight: float = 0

    mutability: float = 0
    heightTolerance: float = 0

    influenceShot: float = 1
    chaos: float = 0

    totalInfluenceWeight: float = 0
    range: float = 10

    parentVariety: Variety = None

@dataclass
class Food:
    name: str
    calories: float
    parentSeed: Seed
    amount: int = 0
    
    
@dataclass
class VarietyInfluence:
    variety: Variety
    distance: float
    influenceWeight: float
    


def checkVarietiesPositions(heightMetrics: HeightVarietyMetrics) -> bool:
    prevMinHeight = 0
    prevMaxHeight = 0

    for variety in heightMetrics.varieties:
        if (
            variety.maxHeightZone < prevMaxHeight
            or variety.maxHeightZone < prevMinHeight
            or variety.minHeightZone < prevMinHeight
        ):
            return False

        prevMinHeight = variety.minHeightZone
        prevMaxHeight = variety.maxHeightZone

    return True


def setHeightMetrics(varieties: List[Variety]) -> HeightVarietyMetrics:
    heightMetrics = HeightVarietyMetrics()

    for variety in varieties:
        heightMetrics.varieties.append(variety)

    return heightMetrics
    

def setAttribute(id: int, description: str, minValue: float, maxValue: float) -> Attribute:
    return Attribute(
        attributeID=id,
        description=description,
        minValue=minValue,
        maxValue=maxValue
    )


def setVariety(
    id: int,
    description: str,
    minHeight: float,
    maxHeight: float,
    attributes: List[Attribute],
    aggressiveness: float,
    maxChildren: int,
    kcal_base: float,
    food_base_amount: float
) -> Variety:
    return Variety(
        varietyID=id,
        name=description,
        minHeightZone=minHeight,
        maxHeightZone=maxHeight,
        attributes=attributes,
        aggressiveness=aggressiveness,
        maxChildren=maxChildren,
        food_base_amount=food_base_amount,
        kcal_base=kcal_base
    )


def setSeed(
    originalHeight: float,
    aggressivenessShot: float,
    mutability: float,
    influenceShot: float,
    rangeValue: float,
    parentVariety: Variety
) -> Seed:
    seed = Seed()
    seed.originalHeight = originalHeight
    seed.influenceShot = influenceShot
    seed.chaos = 1 - seed.influenceShot
    seed.range = rangeValue
    seed.parentVariety = parentVariety
    seed.mutability = mutability

    return seed


def setPrimalSeed(originalHeight: float, parentVariety: Variety) -> Seed:
    seed = Seed()
    seed.originalHeight = originalHeight
    seed.influenceShot = 1
    seed.chaos = 1 - seed.influenceShot
    seed.range = 10
    seed.parentVariety = parentVariety
    seed.mutability = 0

    return seed


def distanceOutsideZone(height: float, variety: Variety) -> float:
    if height < variety.minHeightZone:
        return variety.minHeightZone - height

    if height > variety.maxHeightZone:
        return height - variety.maxHeightZone

    return 0.0


def findInfluences(heightMetric: HeightVarietyMetrics, seed: Seed) -> List[VarietyInfluence]:
    influentialVarieties = []
    totalInfluence = 0

    for variety in heightMetric.varieties:
        distance = distanceOutsideZone(seed.newHeight, variety)

        if variety.varietyID != seed.parentVariety.varietyID:
            if distance <= seed.range:
                influenceWeight = variety.aggressiveness / (1 + distance)

                infVar = VarietyInfluence(
                    variety=variety,
                    distance=distance,
                    influenceWeight=influenceWeight
                )

                influentialVarieties.append(infVar)
                totalInfluence += influenceWeight

    seed.totalInfluenceWeight = totalInfluence

    return influentialVarieties


def probabilitySelectionByInfluence(seed: Seed, influentialVarieties: List[VarietyInfluence]) -> int:
    roulette = [-1 for _ in range(100)]

    slotindex = 0

    slots = round(seed.influenceShot * 100)

    for slotindex in range(slotindex, min(slots, 100)):
        roulette[slotindex] = seed.parentVariety.varietyID

    slotindex = slots

    for infVariety in influentialVarieties:
        slotsFilled = slotindex

        if seed.totalInfluenceWeight == 0:
            slots = 0
        else:
            slots = round(
                (infVariety.influenceWeight / seed.totalInfluenceWeight)
                * 100
                * (1 - seed.influenceShot)
            )

        for slotindex in range(slotsFilled, min(slotsFilled + slots, 100)):
            if slots > 10:
                roulette[slotindex] = infVariety.variety.varietyID
            else:
                roulette[slotindex] = -1

    ind = random.randint(0, 99)
    value = roulette[ind]

    return value


def generateAmountAttributesByLuck(playerLuck: float) -> int:
    probabilities = [0.30, 0.50, 0.20]

    probabilities[1] *= 1 + playerLuck
    probabilities[2] *= 1 + playerLuck * 2
    probabilities[0] = 1.0 - (probabilities[1] + probabilities[2])

    randomValue = random.random()

    if randomValue < probabilities[0]:
        return 1
    elif randomValue < probabilities[0] + probabilities[1]:
        return 2
    else:
        return 3


def getVarietyById(varietyID: int, heightVarieties: HeightVarietyMetrics) -> Variety:
    for variety in heightVarieties.varieties:
        if varietyID == variety.varietyID:
            return variety

    raise ValueError(f"Variety with ID {varietyID} not found")


def getAttributeFromVariety(variety: Variety, seed: Seed) -> Attribute:
    index = random.randint(0, len(variety.attributes) - 1)

    baseAttribute = variety.attributes[index]

    attribute = Attribute(
        attributeID=baseAttribute.attributeID,
        description=baseAttribute.description,
        minValue=baseAttribute.minValue,
        maxValue=baseAttribute.maxValue,
        value=baseAttribute.value
    )

    noise = -1.0 + random.random() * 2.0

    middleValue = (attribute.maxValue - attribute.minValue) / 2

    attribute.value = (
        middleValue
        + seed.influenceShot * (attribute.maxValue - middleValue)
        + noise * seed.chaos * (2 * middleValue)
    )

    return attribute


def setConceivedSeed(newSeed: Seed, seed: Seed, variety: Variety) -> None:
    randomValue = random.random() * 0.5
    hasMutated = False

    newSeed.originalHeight = seed.newHeight

    if seed.parentVariety.varietyID != variety.varietyID:
        hasMutated = True

    newSeed.parentVariety = variety
    newSeed.range = seed.range

    distance = distanceOutsideZone(seed.newHeight, variety)

    newSeed.heightTolerance = (
        (variety.maxHeightZone - variety.minHeightZone) / 2
    ) * (0.5 + variety.aggressiveness)

    baseInfluence = newSeed.heightTolerance / (
        newSeed.heightTolerance + distance**4 + 1.0
    )

    noise = random.random() * 0.10
    noiseLoss = baseInfluence * noise

    newSeed.influenceShot = ((seed.influenceShot)+ (baseInfluence - noiseLoss))/2

    newSeed.mutability = seed.mutability

    if hasMutated:
        newSeed.mutability = seed.mutability + 0.5 * randomValue

    newSeed.chaos = 1 - newSeed.influenceShot


def printSeedDataLine(seed: Seed) -> None:
    print(
        seed.originalHeight,
        seed.newHeight,
        seed.influenceShot,
        seed.chaos,
        seed.heightTolerance,
        seed.mutability,
        seed.parentVariety.name,
        seed.range,
        seed.totalInfluenceWeight
    )

    print("Attributes:")

    for attribute in seed.attributesShot:
        print(attribute.description, attribute.value)



def printColumnsName() -> None:
    print(
        "Original Height newHeight influenceShot chaos "
        "heightTolerance mutability parentVariety range totalInfluenceWeight"
    )


def plantSeed(seed: Seed, newHeight: float) -> None:
    seed.newHeight = newHeight

    centerHeight = (
        seed.parentVariety.maxHeightZone
        + seed.parentVariety.minHeightZone
    ) / 2.0

    distance = abs(seed.newHeight - centerHeight)

    expansion = distance * ((1.5 * (seed.chaos + 0.1)) + seed.mutability)

    stabilization = 1.0 - (seed.influenceShot * 0.25)

    seed.range = seed.range * stabilization + expansion * seed.chaos * 0.25


def attributeAlreadyGiven(seed: Seed, attribute: Attribute) -> bool:
    for givenAttribute in seed.attributesShot:
        if attribute.attributeID == givenAttribute.attributeID:
            return True

    return False


def getAttributesByInfluence(
    newSeed: Seed,
    seed: Seed,
    influentialVarieties: List[VarietyInfluence],
    heightMetric: HeightVarietyMetrics
) -> None:
    cantAttributes = generateAmountAttributesByLuck(0)

    i = 0

    while i < cantAttributes:
        varietyId = probabilitySelectionByInfluence(seed, influentialVarieties)

        if varietyId != -1:
            variety = getVarietyById(varietyId, heightMetric)

            if len(variety.attributes) == 0:
                continue

            attribute = getAttributeFromVariety(variety, seed)

            if attributeAlreadyGiven(newSeed, attribute):
                i += 1
                continue
            else:
                newSeed.attributesShot.append(attribute)

        i += 1


def mutateVarietyByInfluence(
    newSeed: Seed,
    seed: Seed,
    influentialVarieties: List[VarietyInfluence],
    heightMetric: HeightVarietyMetrics
) -> bool:
    varietyId = probabilitySelectionByInfluence(seed, influentialVarieties)

    if varietyId != -1:
        if varietyId != seed.parentVariety.varietyID:
            variety = getVarietyById(varietyId, heightMetric)
            newSeed.parentVariety = variety
            setConceivedSeed(newSeed, seed, variety)
        else:
            setConceivedSeed(newSeed, seed, seed.parentVariety)

        return True

    else:
        return False

def calculate_kcal_from_seed(seed):
    variety = seed.parentVariety

    kcal_base = variety.kcal_base

    ideal_height = (
        variety.minHeightZone + variety.maxHeightZone
    ) / 2

    distance = abs(seed.originalHeight - ideal_height)

    height_tolerance = (
        (variety.maxHeightZone - variety.minHeightZone) / 2
    ) * (0.5 + variety.aggressiveness)

    height_factor = height_tolerance / (
        height_tolerance + distance + 1
    )

    influence_factor = 0.7 + 0.3 * seed.influenceShot

    noise = random.uniform(-1, 1) * seed.chaos * 0.25

    noise_factor = 1 + noise

    kcal_final = (
        kcal_base
        * height_factor
        * influence_factor
        * noise_factor
    )

    return max(0, kcal_final)

def calculate_food_amount_from_seed(seed):
    variety = seed.parentVariety

    food_amount = variety.food_base_amount

    ideal_height = (
        variety.minHeightZone + variety.maxHeightZone
    ) / 2

    distance = abs(seed.originalHeight - ideal_height)

    height_tolerance = (
        (variety.maxHeightZone - variety.minHeightZone) / 2
    ) * (0.5 + variety.aggressiveness)

    height_factor = height_tolerance / (
        height_tolerance + distance + 1
    )

    influence_factor = 0.5 + 0.2 * seed.influenceShot

    noise = random.uniform(-1, 0) * seed.chaos * 0.75

    noise_factor = 1 + noise

    food_amount = round(
        food_amount
        * height_factor
        * influence_factor
        * noise_factor
    )

    return max(0, food_amount)


def getFoodFromSeed(seed: Seed) :
    foodName = seed.parentVariety.name
    calories = calculate_kcal_from_seed(seed)
    food_amount= calculate_food_amount_from_seed(seed)
    for attribute in seed.attributesShot:
        calories += attribute.value * 5

    return Food(
        name=foodName,
        calories=calories*food_amount,
        amount=food_amount,
        parentSeed=seed
    )
    
def getCantChildren(seed: Seed) -> int:
    variety = seed.parentVariety

    distance = distanceOutsideZone(seed.newHeight, variety)

    height_tolerance = (
        (variety.maxHeightZone - variety.minHeightZone) / 2
    ) * (0.5 + variety.aggressiveness)

    height_tolerance = max(height_tolerance, 1)

    altitude_factor = height_tolerance / (height_tolerance + distance + 1)

    influence_factor = 0.4 + 0.6 * seed.influenceShot

    chaos_penalty = 1 - (seed.chaos * 0.65)

    mutability_bonus = 1 + min(seed.mutability, 1.5) * 0.25

    
    expected_children = (
        variety.maxChildren
        * altitude_factor
        * influence_factor
        * chaos_penalty
        * mutability_bonus
        + round(random.randint(0,2)*0.5)
        
    )

    noise = random.uniform(-0.75, 0.75)

    cant_children = round(expected_children + noise)

    cant_children = max(0, cant_children)
    cant_children = min(cant_children, variety.maxChildren)

    return cant_children

def generateChildren(
    seed: Seed,
    influentialVarieties: List[VarietyInfluence],
    heightMetric: HeightVarietyMetrics
):
    cantChildren = getCantChildren(seed)

    children = []
    food=[]
    for child in range(cantChildren):
        newSeed = Seed()

        getAttributesByInfluence(
            newSeed,
            seed,
            influentialVarieties,
            heightMetric
        )

        if mutateVarietyByInfluence(
            newSeed,
            seed,
            influentialVarieties,
            heightMetric
        ):
            children.append(newSeed)
            food.append(getFoodFromSeed(newSeed))

    return children, food


def seedReproduction(
    heightMetric: HeightVarietyMetrics,
    seed: Seed,
    newHeight: float
):
    plantSeed(seed, newHeight)

    influentialVarieties = findInfluences(heightMetric, seed)

    children, food = generateChildren(
        seed,
        influentialVarieties,
        heightMetric
    )

    return children, food


def writeSeedCSVHeader(writer) -> None:
    writer.writerow([
        "generation",
        "height",
        "parentVariety",
        "influence",
        "chaos",
        "mutability",
        "range",
        "totalInfluenceWeight",
        "cantAttributes",
        "totalSeeds",
        "totalCalories",
        "foodAmount",
        "leftSeeds"
    ])


def writeSeedCSVLine(writer, generation: int, seed: Seed, food: List[Food], seeds: List[Seed], total_seeds: List[Seed]) -> None:
    writer.writerow([
        generation,
        seed.originalHeight,
        seed.parentVariety.name,
        seed.influenceShot,
        seed.chaos,
        seed.mutability,
        seed.range,
        seed.totalInfluenceWeight,
        len(seed.attributesShot),
        len(seeds),
        sum(f.calories for f in food),
        sum(f.amount for f in food),
        len(total_seeds)
    ])

def generateRandomFood(amount):
    var1Potato = setVariety(
        1,
        "Sani imilla",
        3830,
        3900,
        [],
        0.3,
        20,
        77,
        3
    )
    food=[]
    seed1 = setPrimalSeed(20, var1Potato)
    for i in range(amount):
        food.append(
            Food(
                parentSeed=seed1,
                name=seed1.parentVariety.name,
                calories=calculate_kcal_from_seed(seed1),
                amount=calculate_food_amount_from_seed(seed1)
            )
        )
    return food

def generateRandomSeeds(amount,original_height):
    var1Potato = setVariety(
        1,
        "Sani imilla",
        3830,
        3900,
        [],
        0.3,
        20,
        77,
        5
    )
    seeds=[]
    for i in range(amount):
        seeds.append(setPrimalSeed(20, var1Potato))
    return seeds

def generateHeightMetrics():
    varieties = []

    atri1 = setAttribute(1, "speed", 3, 20)
    atri2 = setAttribute(2, "energy", 5, 30)
    atri3 = setAttribute(3, "night vision", 5, 20)
    atri4 = setAttribute(4, "force", 3, 20)

    var1Potato = setVariety(
        1,
        "Sani imilla",
        3830,
        3900,
        [atri1],
        0.3,
        20,
        77,
        5
    )

    var2Potato = setVariety(
        2,
        "Imilla Negra",
        3850,
        3900,
        [atri2],
        0.2,
        20,
        77,
        10
    
    )

    var3Potato = setVariety(
        3,
        "Imilla Rosada",
        3830,
        3880,
        [atri3],
        0.2,
        20,
        77,
        10
    )

    var4Potato = setVariety(
        4,
        "Ocucuri morado",
        3230,
        4000,
        [atri4],
        0.4,
        20,
        77,
        15
    )
    
    var5Potato = setVariety(
        5,
        "Locka",
        3830,
        4200,
        [atri4],
        0.5,
        20,
        77,
        15
    )

    varieties.append(var1Potato)
    varieties.append(var2Potato)
    varieties.append(var3Potato)
    varieties.append(var4Potato)
    varieties.append(var5Potato)
    

    heightMetrics = setHeightMetrics(varieties)

    return heightMetrics

def behaviorSimulation():
    varieties = []

    atri1 = setAttribute(1, "speed", 3, 20)
    atri2 = setAttribute(2, "energy", 5, 30)
    atri3 = setAttribute(3, "night vision", 5, 20)
    atri4 = setAttribute(4, "force", 3, 20)

    varDarkPotato = setVariety(
        1,
        "Dark Potato",
        10,
        50,
        [atri1],
        0.5,
        8,
        77,
        5
    )

    varYellowPotato = setVariety(
        2,
        "Yellow Potato",
        45,
        60,
        [atri2],
        0.2,
        10,
        250,
        10
    
    )

    varRedPotato = setVariety(
        3,
        "Red Potato",
        55,
        80,
        [atri3],
        0.4,
        4,
        120,
        5
    )

    varWhitePotato = setVariety(
        4,
        "White Potato",
        70,
        100,
        [atri4],
        0.2,
        7,
        200,
        4
    )

    varieties.append(varDarkPotato)
    varieties.append(varYellowPotato)
    varieties.append(varRedPotato)
    varieties.append(varWhitePotato)

    heightMetrics = setHeightMetrics(varieties)

    seed1 = setPrimalSeed(20, varDarkPotato)
    seeds_amount= 10
    total_food=list()
    total_seeds=list()
    with open("seed_simulation.csv", "w", newline="") as csvFile:
        writer = csv.writer(csvFile)

        writeSeedCSVHeader(writer)

        for i in range(30):
            for j in range(seeds_amount):
                seeds, food = seedReproduction(heightMetrics, seed1, 90)
                total_food.extend(food)
                total_seeds.extend(seeds)

            writeSeedCSVLine(writer, i, seed1, total_food,seeds,total_seeds)

            
            
            
            if len(seeds) == 0:
                writer.writerow(["The actual seed has no offspring. Selecting a previous seed."])
                seed1 = total_seeds[random.randint(0, len(total_seeds) - 1)]
                seeds_amount=1
                continue
            
                
            seeds_amount=len(seeds)
            ind = random.randint(0, len(seeds) - 1)
            seed1 = seeds[ind]

        writer.writerow(["ALTITUDE CHANGED TO 30M"])
        writeSeedCSVHeader(writer)
        seeds_amount=1
        for i in range(30):
            for j in range(seeds_amount):
                seeds, food = seedReproduction(heightMetrics, seed1, 30)
                total_food.extend(food)
                total_seeds.extend(seeds)

            writeSeedCSVLine(writer, i, seed1, total_food,seeds,total_seeds)

            
            
            
            if len(seeds) == 0:
                writer.writerow(["The actual seed has no offspring. Selecting a previous seed."])
                seed1 = total_seeds[random.randint(0, len(total_seeds) - 1)]
                seeds_amount=1
                continue
            
                
            seeds_amount=len(seeds)
            ind = random.randint(0, len(seeds) - 1)
            seed1 = seeds[ind]

        writer.writerow(["RANDOM ALTITUDES"])
        writeSeedCSVHeader(writer)
        seeds_amount=1
        for i in range(30):
            for j in range(seeds_amount):
                seeds, food = seedReproduction(heightMetrics, seed1, random.randint(10,95))
                total_food.extend(food)
                total_seeds.extend(seeds)

            writeSeedCSVLine(writer, i, seed1, total_food,seeds,total_seeds)

            
            
            
            if len(seeds) == 0:
                writer.writerow(["The actual seed has no offspring. Selecting a previous seed."])
                seed1 = total_seeds[random.randint(0, len(total_seeds) - 1)]
                seeds_amount=1
                continue
            
                
            seeds_amount=len(seeds)
            ind = random.randint(0, len(seeds) - 1)
            seed1 = seeds[ind]


if __name__ == "__main__":
    behaviorSimulation()