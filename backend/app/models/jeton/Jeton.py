from enum import Enum


class TypeJeton(str, Enum):
    # Les valeurs doivent correspondre exactement au type SQL type_jeton
    ACTIVATION = "activation"
    REINITIALISATION_MDP = "reinitialisation_mdp"