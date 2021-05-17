

import relationship
import pandas as pd
import os



def find_position(chain, new_t, low, high, insert=False):
    if low == high:
        compare_low = relationship.main(new_t, chain[low], insert)
        if compare_low == "entails_t1_t2":
            return low + 1
        elif compare_low == "entails_t2_t1":
            return low

    if low > high:
        return low

    mid = (low+high)//2
    compare_mid = relationship.main(new_t, chain[mid], insert)

    # middle value
    if "equivalent" in compare_mid:
        # theory already exists in the chain. only the names are checked (not the contents/axioms)
        if new_t == chain[mid]:
            return -1
        # found an equivalent theory
        else:
            if insert:
                return mid
            else:
                return chain[mid]
    # lower half
    elif compare_mid == "entails_t2_t1":
        return find_position(chain, new_t, low, mid-1)
    # upper half
    elif compare_mid == "entails_t1_t2":
        return find_position(chain, new_t, mid+1, high)
    # does not belong
    else:
        return -1



def insertion(chain, in_chain, new_t):
    location = int(find_position(in_chain, new_t, 0, len(in_chain)-1, insert=True))
    if location == -1:
        return []
    else:
        new_t = new_t.replace(".in", "")
        chain.insert(location, new_t)
        # print("inserted at ", location, chain)
        return chain



def start_new_chain(chain, in_chain, new_t):

    new_chain = []
    top = []       #theories that entail theory
    bottom = []    #theories entailed by new theory


    for i, t in enumerate(in_chain):
        rel = relationship.main(new_t, t, True)
        if rel == "entails_t1_t2":
            bottom.append(chain[i])
        elif rel == "entails_t2_t1":
            top.append(chain[i])

    new_t = new_t.replace(".in", "")
    if bottom or top:
        new_chain = bottom + [new_t] + top

    return new_chain



def search(in_chain, new_t):
    location = find_position(in_chain, new_t, 0, len(in_chain)-1)
    if not isinstance(location, int):
        print("an equivalent theory is ", location)
    else:
        print("no equivalent theory found")


def main(csv_file, new_t, function):
    # open existing chain decomposition file, converted to DataFrame then lists
    chains_df = pd.read_csv(csv_file)
    chains_list = []
    [chains_list.append(row) for row in chains_df]
    chains_list = chains_df.values.tolist()

    for i, c in enumerate(chains_list):
        chains_list[i] = list(filter(lambda a: pd.notna(a), c))

    #add ".in" suffix to theories in chains to match input file names to check relationships
    input_chains = [[str(s) + ".in" for s in c] for c in chains_list]

    inserted = False

    # first check if new theory is consistent
    with open(new_t, "r") as f:
        lines = f.readlines()
    lines = relationship.concatenate_axioms(lines)
    relationship.replace_symbol(lines, ".\n", "")
    relationship.replace_symbol(lines, "\t", "")
    check_consistent = relationship.consistency(lines, [])



    if check_consistent is not True:
        print("your theory is inconsistent")
    else:

        num_chains_start = len(chains_list)

        # update each chain
        for i, chain in enumerate(chains_list[:num_chains_start]):
            #condition = relationship.main(new_t, chain[0] + ".in")

            # skip the chain if inconsistent
            #if "inconsistent" in condition:
                #continue
            #else:
            if function == 1:   #insertion
                #regular insertion
                if insertion(chain, input_chains[i], new_t) != -1:
                    inserted = True

                #try starting a new chain with select theories contained in chain
                else:
                    new_chain = start_new_chain(chain, input_chains[i], new_t)
                    if new_chain and (new_chain not in chains_list):
                        print("new chain")
                        chains_list.append(new_chain)
                        print(chains_list)

                        new_chain = [str(c) + ".in" for c in new_chain]
                        input_chains.append(new_chain)
                        inserted = True
                #some_t = new_t.replace(".in", "")
                #if some_t in new_chain:
                 #   inserted = True
                #print(inserted)

            elif function == 2: #search for an equivalent theory
                print(search(input_chains[i], new_t))
                inserted = True

        if inserted is False: # new theory has not been inserted anywhere. create a new chain
            new_t = new_t.replace(".in", "")
            chains_list.append([new_t])
            input_chains.append([new_t + ".in"])

        print("here is the final list \n", chains_list)

        new_df = pd.DataFrame(chains_list)
        new_df.to_csv(csv_file, mode="w", index=False)
        print("chain decomposition is now updated")


def complete_insertion(csv_file):
    for file_name in os.listdir():
        if file_name.endswith(".in"):
            print(file_name)
            main(csv_file, file_name, 1)


# 1 for insert, 2 for search
main("semilinear-orderings.csv", "weak_upper_separative.in", 1)
#complete_insertion("between.csv")
