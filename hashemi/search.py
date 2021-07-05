from nltk import *

import pandas as pd
from p9_tools import config
from p9_tools.relationship import relationship, files
from p9_tools.parse import theory, model
import os

from nltk.sem import Expression
read_expr = Expression.fromstring

FILE_PATH = config.path
EX_PATH = config.examples
CEX_PATH = config.counterexamples
CSV_FILE = config.csv


# find the strongest theory in the chain that is consistent with the example
def find_strong(chain, model_lines):
    i = len(chain)-1    # starting index from the end
    consistent = False
    strongest = -1       # index of strongest consistent theory

    while i >= 0 and not consistent:
        theory_lines = theory.theory_setup(os.path.join(FILE_PATH, chain[i]))
        if theory_lines:
            consistent = relationship.consistency(model_lines, theory_lines,new_dir="")
            # found maximal consistent theory
            if consistent:
                print("consistent with ", chain[i])
                strongest = i
                break
            else:
                print("inconsistent with ", chain[i])
        i -= 1
    return strongest


# find weakest theory that is not consistent with the counterexample
def find_weak(chain, model_lines):
    i = 0
    max_index = len(chain)-1
    consistent = True
    weakest = len(chain)

    while i <= max_index and consistent:
        theory_lines = theory.theory_setup(os.path.join(FILE_PATH, chain[i]))
        if theory_lines:
            consistent = relationship.consistency(model_lines, theory_lines, new_dir="")
            # found minimal inconsistent theory
            if not consistent:
                print("consistent with ", chain[i])
                weakest = i
                break
            else:
                print("inconsistent with ", chain[i])
        i += 1

    return weakest


def find_bracket(chain):
    strong = len(chain)-1       # maximum index for strongest theory for examples
    weak = 0                    # minimum index for weakest theory for counterexamples

    # find strongest theory that is consistent with all examples
    for ex_file in os.listdir(EX_PATH):
        if ex_file.endswith(".in"):
            print("ex", ex_file)
            print(model.model_setup(os.path.join(EX_PATH, ex_file)))
            s = find_strong(chain, model.model_setup(os.path.join(EX_PATH, ex_file)))
            # update the maximum
            if s < strong:
                strong = s
                # the example is inconsistent with all theories in the chain
                if strong == -1:
                    break

    # find weakest theory that is not consistent with all counterexamples
    for cex_file in os.listdir(CEX_PATH):
        if cex_file.endswith(".in"):
            print("cex", cex_file)
            print(model.model_setup(os.path.join(CEX_PATH, cex_file)))
            w = find_weak(chain, model.model_setup(os.path.join(CEX_PATH, cex_file)))
            # update the minimum
            if w > weak:
                weak = w
                # the counterexample is consistent with all theories in the chain
                if weak == len(chain):
                    break

    # no bracket
    if strong == -1 and weak == len(chain):
        bracket = [None, None]

    # one-sided brackets
    elif strong == -1:
        bracket = [weak, None]
    elif weak == len(chain):
        bracket = [None, strong]

    # bracket found
    else:
        bracket = [weak, strong]
    return bracket


def upper_bound_model(t_weak_name, t_strong_name):
    t_weak = theory.theory_setup(t_weak_name)
    t_strong = theory.theory_setup(t_strong_name)

    negated_axioms = []
    for axiom in t_strong:
        if axiom not in t_weak:
            negated_axioms.append("-" + axiom)
    theory_lines = t_weak + negated_axioms
    return theory_lines


def generate_model(theory_lines, new_dir, file_name):
    assumptions = read_expr(theory_lines[0])

    # look for 10 models before timeout
    mb = MaceCommand(None, [assumptions], max_models=10)
    for c, added in enumerate(theory_lines[1:]):
        mb.add_assumptions([read_expr(added)])

    # use mb.build_model([assumptions]) to print the input
    # consistent = "inconclusive"
    try:
        model = mb.build_model()
        # found a model, the theories are consistent with each other
        if model:
            # consistent = True
            consistent_model = mb.model(format='cooked')
            if new_dir:
                files.create_file(new_dir, file_name, consistent_model)
            return True

    except LogicalExpressionException:
        print("model not found")

    return False


def get_input_chains():
    chains_df = pd.read_csv(CSV_FILE)
    chains_list = []
    [chains_list.append(row) for row in chains_df]
    chains_list = chains_df.values.tolist()

    for i, c in enumerate(chains_list):
        chains_list[i] = list(filter(lambda a: pd.notna(a), c))
    input_chains = [[str(s) + ".in" for s in c] for c in chains_list]
    return input_chains


# finding all the brackets
def main():
    # chain decomposition in list form
    input_chains = get_input_chains()

    # get the bracket from each chain
    all_brackets = []
    for i, chain in enumerate(input_chains):
        bracket = [i] + find_bracket(chain)
        all_brackets.append(bracket)

    try:
        new_dir = os.path.join(FILE_PATH, "models_to_classify")
        os.mkdir(new_dir)
    except FileExistsError:
        new_dir = os.path.join(FILE_PATH, "models_to_classify")

    for bracket in all_brackets:
        if bracket[1] is None or bracket[2] is None:
            print("no bracket found for chain", bracket[0])
        else:
            # dialogue phase

            # refine upper bound
            ub_min = False
            lb_theory = input_chains[bracket[0]][bracket[1]]
            while ub_min is False and bracket[2] >= 0:
                ub_theory = input_chains[bracket[0]][bracket[2]]
                ub_model = "ub_model_" + lb_theory.replace(".in", "") + "_" + ub_theory.replace(".in", "")
                # look for a model
                if generate_model(upper_bound_model(lb_theory, ub_theory), new_dir, ub_model):
                    ans = input("is " + os.path.join(new_dir, ub_model) + " an example? (y/n):\n")
                    # omits a model
                    if ans == 'y':
                        bracket[2] -= 1
                    else:
                        ub_min = True
                else:
                    print("model cannot be generated for ", ub_model)
                    ub_min = True

            # refine lower bound
            lb_max = False
            while lb_max is False and bracket[1] < len(input_chains[bracket[0]]):
                lb_theory = input_chains[bracket[0]][bracket[1]]
                lb_model = "lb_model_" + lb_theory.replace(".in", "") + "_" + ub_theory.replace(".in", "")
                # look for a model
                if generate_model(theory.theory_setup(lb_theory), new_dir, lb_model):
                    ans = input("is " + os.path.join(new_dir, lb_model) + " an example? (y/n):\n")
                    # contains an unintended model
                    if ans == 'n':
                        bracket[1] += 1  # move lower bound up
                    else:
                        lb_max = True

            if bracket[1] == bracket[2]:
                best_match = input_chains[bracket[0]][bracket[1]]
                print("best matching theory from chain", bracket[0], "is", best_match)
            elif bracket[1] > bracket[2]:
                best_match = None
                print("overlapped bracket, theory does not exist in chain", bracket[0] + 1)
            else:
                best_match = [bracket[1], bracket[2]]
                print("bracket ", best_match, "cannot be further refined")

    return best_match


if __name__ == "__main__":
    main()

