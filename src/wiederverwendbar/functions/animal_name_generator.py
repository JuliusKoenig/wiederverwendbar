import random


def animal_name_generator() -> list[str]:
    animals = [
        ["Dog", "Hund"], ["Puppy", "Welpe"], ["Turtle", "Schildkröte"], ["Parrot", "Papagei"], ["Cat", "Katze"], ["Kitten", "Kätzchen"],
        ["Goldfish", "Goldfisch"], ["Mouse", "Maus"], ["Hamster", "Hamster"], ["Cow", "Kuh"], ["Rabbit", "Kaninchen"], ["Ducks", "Enten"],
        ["Shrimp", "Garnele"], ["Pig", "Schwein"], ["Goat", "Ziege"], ["Crab", "Krabbe"], ["Deer", "Hirsche"], ["Bee", "Biene"], ["Sheep", "Schaf"],
        ["Fish", "Fisch"], ["Turkey", "Truthahn"], ["Dove", "Taube"], ["Chicken", "Huhn"], ["Horse", "Pferd"], ["Crow", "Krähe"], ["Peacock", "Pfau"],
        ["Dove", "Taube"], ["Sparrow", "Sperling"], ["Goose", "Gans"], ["Stork", "Storch"], ["Pigeon", "Taube"], ["Turkey", "Truthahn"], ["Hawk", "Falke"],
        ["BaldEagle", "Weißkopfseeadler"], ["Raven", "Rabe"], ["Parrot", "Papagei"], ["Flamingo", "Flamingo"], ["Seagull", "Möwe"], ["Ostrich", "Strauß"],
        ["Swallow", "Schwalbe"], ["BlackBird", "Schwarzvogel"], ["Penguin", "Pinguin"], ["Robin", "Rotkehlchen"], ["Swan", "Schwan"], ["Owl", "Eule"],
        ["Woodpecker", "Specht"], ["Squirrel", "Eichhörnchen"], ["Dog", "Hund"], ["Chimpanzee", "Schimpanse"], ["Ox", "Ochse"], ["Lion", "Löwe"],
        ["Panda", "Panda"], ["Walrus", "Walross"], ["Otter", "Otter"], ["Mouse", "Maus"], ["Kangaroo", "Känguru"], ["Goat", "Ziege"], ["Horse", "Pferd"],
        ["Monkey", "Affe"], ["Cow", "Kuh"], ["Koala", "Koala"], ["Mole", "Maulwurf"], ["Elephant", "Elefant"], ["Leopard", "Leopard"],
        ["Hippopotamus", "Nilpferd"], ["Giraffe", "Giraffe"], ["Fox", "Fuchs"], ["Coyote", "Kojote"], ["Hedgehong", "Igelhund"], ["Sheep", "Schaf"],
        ["Deer", "Hirsche"], ["Giraffe", "Giraffe"], ["Woodpecker", "Specht"], ["Camel", "Kamel"], ["Starfish", "Seestern"], ["Koala", "Koala"],
        ["Alligator", "Alligator"], ["Owl", "Eule"], ["Tiger", "Tiger"], ["Bear", "Bär"], ["BlueWhale", "Blauwal"], ["Coyote", "Kojote"],
        ["Chimpanzee", "Schimpanse"], ["Raccoon", "Waschbär"], ["Lion", "Löwe"], ["ArcticWolf", "Polarwolf"], ["Crocodile", "Krokodil"], ["Dolphin", "Delfin"],
        ["Elephant", "Elefant"], ["Squirrel", "Eichhörnchen"], ["Snake", "Schlange"], ["Kangaroo", "Känguru"], ["Hippopotamus", "Nilpferd"], ["Elk", "Elch"],
        ["Fox", "Fuchs"], ["Gorilla", "Gorilla"], ["Bat", "Fledermaus"], ["Hare", "Hase"], ["Toad", "Kröte"], ["Frog", "Frosch"], ["Deer", "Rotwild"],
        ["Rat", "Ratte"], ["Badger", "Dachs"], ["Lizard", "Eidechse"], ["Mole", "Maulwurf"], ["Hedgehog", "Igel"], ["Otter", "Fischotter"],
        ["Reindeer", "Rentier"], ["Crab", "Krabbe"], ["Fish", "Fisch"], ["Seal", "Robbe"], ["Octopus", "Oktopus"], ["Shark", "Hai"],
        ["Seahorse", "Seepferdchen"], ["Walrus", "Walross"], ["Starfish", "Seestern"], ["Whale", "Walfisch"], ["Penguin", "Pinguin"], ["Jellyfish", "Qualle"],
        ["Squid", "Tintenfisch"], ["Lobster", "Hummer"], ["Pelican", "Pelikan"], ["Clam", "Muschel"], ["Seagull", "Möwe"], ["Dolphin", "Delphin"],
        ["Shell", "Muschel"], ["SeaUrchin", "Seebarsch"], ["Cormorant", "Kormoran"], ["Otter", "Fischotter"], ["Pelican", "Pelikan"],
        ["SeaAnemone", "Seeanemone"], ["SeaTurtle", "Meeresschildkröte"], ["SeaLion", "Seelöwe"], ["Coral", "Koralle"], ["Moth", "Motte"], ["Bee", "Biene"],
        ["Butterfly", "Schmetterling"], ["Spider", "Spinne"], ["Ant", "Ameise"], ["Dragonfly", "Libelle"], ["Fly", "Fliege"], ["Mosquito", "Stechmücke"],
        ["Grasshopper", "Grashüpfer"], ["Beetle", "Käfer"], ["Cockroach", "Kakerlake"], ["Centipede", "Tausendfüßler"], ["Worm", "Wurm"], ["Louse", "Laus"]
    ]
    name = random.choice(animals)
    return name
