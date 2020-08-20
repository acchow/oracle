'''
 August 2020
 By Amanda Chow
'''

from nltk import *
import os

from nltk.sem import Expression
read_expr = Expression.fromstring


def concatenate_axioms(lines):
    # remove specific lines
    [lines.remove(x) for x in lines if "formulas(assumptions)" in x]
    # [lines.remove("formulas(assumptions).\n") if "formulas(assumptions).\n" in lines else lines=lines]
    [lines.remove(y) for y in lines if "end_of_list" in y]

    # put axioms together into one list
    index_last_line = []
    for c, val in enumerate(lines):
        if "." in val:
            index_last_line.append(c)

    one_axiom = []
    all_axioms = []
    c2 = 0
    for c1, i in enumerate(index_last_line):
        while c2 <= i:
            one_axiom.append(lines[c2])
            c2 += 1
        all_axioms.append("".join(one_axiom))
        one_axiom.clear()

    return all_axioms


def replace_symbol(lines, symbol, new_symbol):
    for x, line in enumerate(lines):
        while symbol in lines[x]:
            lines[x] = line.replace(symbol, new_symbol)
    return lines


def theory_setup(theory_name):
    with open(theory_name, "r") as f:
        lines = f.readlines()
        lines = concatenate_axioms(lines)
        # remove comments
        for x, line in enumerate(lines):
            while "%" in lines[x]:
                lines.remove(lines[x])

        try:
            while True:
                lines.remove("\n")
        except ValueError:
            pass
        replace_symbol(lines, ".\n", "")
        replace_symbol(lines, "\t", "")
    f.close()
    return lines


def create_file(name, contents, path):
    new_path = os.path.join(path, name)
    with open(new_path, "w+") as new_file:
        new_file.write(contents)


def consistency(lines_t1, lines_t2, path=None):
    lines = lines_t1 + lines_t2
    assumptions = read_expr(lines[0])

    # set max number of models 50 (otherwise times out)
    mb = MaceCommand(None, [assumptions], 5)
    for c, added in enumerate(lines):
        if c == 0:
            continue
        mb.add_assumptions([read_expr(added)])

    # use mb.build_model([assumptions]) to print the input
    model = mb.build_model()
    if model:
        consistent = True
        consistent_model = mb.model(format='cooked')
        if path:
            create_file("consistent_model", consistent_model, path)

    elif model is False:
        # up to 3 minutes
        prover = Prover9Command(None, [assumptions], 30)
        for c, added in enumerate(lines):
            if c == 0:
                continue
            prover.add_assumptions([read_expr(added)])

        proven = prover.prove()
        if proven:
            consistent = False
            inconsistent_proof = prover.proof()
            if path:
                create_file("inconsistent_proof", inconsistent_proof, path)
    else:
        print("hey")
        consistent = "inconclusive"
    return consistent


def entailment(lines_t1, lines_t2, path=None):
    saved_proofs = []
    # new_axioms = []
    entail = 0
    counter_file_created = False

    for c1, goal in enumerate(lines_t2):
        # set first lines to use prover
        assumptions = read_expr(lines_t1[0])
        goals = read_expr(goal)

        prover = Prover9Command(goals, [assumptions])

        # add axioms into assumptions
        for c, added in enumerate(lines_t1):
            if c == 0:
                continue
            prover.add_assumptions([read_expr(added)])

        # print("from prover9, assumptions: \n", prover.assumptions())
        # print("from p9, the goal: \n", prover.goal())

        proven = prover.prove()
        if proven & (entail == 0):
            get_proof = prover.proof()
            saved_proofs.append(get_proof)

        elif proven is False:
            entail += 1
            # saved_proofs.clear()

            mb = MaceCommand(goals, [assumptions])
            for c, added in enumerate(lines_t1):
                if c == 0:
                    continue
                mb.add_assumptions([read_expr(added)])

            # print("from mace, assumptions: \n", mb.assumptions())
            # print("from mace, the goal: \n", mb.goal())

            # use mb.build_model([assumptions]) to print the input
            # is there a model?
            counterexample = mb.build_model()
            # new_axioms.append(mb.goal())

            if counterexample & (counter_file_created is False):
                counterexample_model = mb.model(format='cooked')
                if path:
                    create_file("counterexample_found", counterexample_model, path)
                counter_file_created = True
            # elif counterexample is False:
            #     print("no counterexample found for the axiom: \n", mb.goal())

    if entail > 0:
        # create_file("remaining_axioms", new_axioms, path)
        return False
    else:
        if path:
            for c, proof in enumerate(saved_proofs):
                create_file("proof" + str(c + 1), proof, path)
        return True


# update owl files
def owl_update(t1, rel, t2, alt_file, meta_file):
    l1 = "ObjectPropertyAssertion(:" + rel
    l2 = " :" + t1 + " :" + t2 + ")\n\n"
    syntax1 = l1 + l2

    f = open(alt_file, "r")
    alt_lines = f.readlines()
    f.close()

    for c1 in range(len(alt_lines)-1, 0, -1):
        if alt_lines[c1] != "":
            alt_lines.insert(c1, syntax1)
            break

    f = open(alt_file, "w")
    alt_string = "".join(alt_lines)
    f.write(alt_string)
    f.close()

    l3 = "Declaration(NamedIndividual(:" + t1 + "))\n"

    l4 = "# Individual: :" + t1 + " (:" + t1 + ")\n\n"
    l5 = "ClassAssertion(:Theory :" + t1 + ")\n\n"

    l6 = "# Individual: :" + t2 + " (:" + t2 + ")\n\n"
    l7 = "ClassAssertion(:Theory :" + t2 + ")\n"

    l8 = "ObjectPropertyAssertion(:" + rel + " :" + t1 + " :" + t2 + ")\n\n"
    syntax2 = l4 + l5 + l6 + l7 + l8

    f = open(meta_file, "r")
    meta_lines = f.readlines()
    f.close()

    for c, l in enumerate(meta_lines):
        if l3 in l:
            break
        elif "###" in l:
            meta_lines.insert(c, l3)
            break
    for c1 in range(len(meta_lines)-1, 0, -1):
        if meta_lines[c1] != "":
            meta_lines.insert(c1, syntax2)
            break

    f = open(meta_file, "w")
    meta_string = "".join(meta_lines)
    f.write(meta_string)
    f.close()


def oracle(t1, lines_t1, t2, lines_t2, alt_file, meta_file, path=None):
    # consistent
    if consistency(lines_t1, lines_t2, path):
        o1_entails_o2 = entailment(lines_t1, lines_t2, path)
        o2_entails_o1 = entailment(lines_t2, lines_t1, path)

        # equivalent
        if o1_entails_o2 & o2_entails_o1:
            if t1 != t2:
                owl_update(t1, "equivalent", t2, alt_file, meta_file)
                if path:
                    os.rename(path, "equivalent_" + t1 + "_" + t2)
            return "equivalent_t1_t2"

        # independent
        elif (o1_entails_o2 is False) & (o2_entails_o1 is False):
            owl_update(t1, "independent", t2, alt_file, meta_file)
            if path:
                os.rename(path, "independent_" + t1 + "_" + t2)
            return "independent_t1_t2"

        # t1 entails t2
        elif o1_entails_o2:
            owl_update(t1, "entails", t2, alt_file, meta_file)
            if path:
                os.rename(path, "entails_" + t1 + "_" + t2)
            return "entails_t1_t2"

        # t2 entails t1
        elif o2_entails_o1:
            owl_update(t2, "entails", t1, alt_file, meta_file)
            if path:
                os.rename(path, "entails_" + t2 + "_" + t1)
            return "entails_t2_t1"

    # inconsistent
    elif consistency(lines_t1, lines_t2, path) is False:
        owl_update(t1, "inconsistent", t2, alt_file, meta_file)
        if path:
            os.rename(path, "inconsistent_" + t1 + "_" + t2)
        return "inconsistent_t1_t2"


def check(meta_file, t1, t2):
    # check if relationship has been found already
    possible = ["inconsistent",
                "entails",
                "independent",
                "equivalent"]

    with open(meta_file, "r") as file3:
        all_relations = file3.readlines()
        for r in all_relations:
            for p in possible:
                if "ObjectPropertyAssertion(:" + p + " :" + t1 + " :" + t2 + ")" in r:
                    # print("ObjectPropertyAssertion(:" + p + " :" + t1 + " :" + t2 + ")")
                    relationship = p + "_t1_t2"
                    file3.close()
                    return relationship
                elif "ObjectPropertyAssertion(:" + p + " :" + t2 + " :" + t1 + ")" in r:
                    # print("ObjectPropertyAssertion(:" + p + " :" + t2 + " :" + t1 + ")")
                    relationship = p + "_t2_t1"
                    file3.close()
                    return relationship
    file3.close()
    return "nf"


# main program
def main(t1, t2, file=False):

    t1 = t1.replace(".in", "")
    t2 = t2.replace(".in", "")

    alt_file = "alt-metatheory.owl"
    meta_file = "metatheory.owl"

    check_rel = check(meta_file, t1, t2)

    if check_rel == "nf":
        if file:
            new_dir = t1 + "_" + t2
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
        else:
            new_dir = None

        lines_t1 = theory_setup(t1 + ".in")
        lines_t2 = theory_setup(t2 + ".in")

        relationship = oracle(t1, lines_t1, t2, lines_t2, alt_file, meta_file, new_dir)
    else:
        relationship = check_rel

    return relationship


# t1 = input("enter theory 1:")
# t2 = input("enter theory 2:")
# print(main(t1, t2))
# print(main("betweenness.in", "betweenness.in"))
